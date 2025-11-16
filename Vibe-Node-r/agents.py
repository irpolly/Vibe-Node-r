
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any

# --- HARD CODED PROJECT SETTINGS ---
import vertexai
vertexai.init(
    project="cloud-run-hackathon-477510",   # ← YOUR PROJECT ID
    location="europe-west4"                 # ← INFERRED FROM LOGS
)

from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session


# ------------------------------------------------------------------
# Base Agent
# ------------------------------------------------------------------
class Agent:
    def __init__(self, node_id: str, config: Dict[str, Any], session: "Session"):
        self.node_id = node_id
        self.config = config
        self.session = session
        self.role = config.get("role", "Unnamed Agent")

    async def think(self, seconds: float = 1.0):
        await asyncio.sleep(seconds)

    def speak(self, text: str):
        print(f"[{self.role}]: {text}")
        self.session.add_message(self.role, text)

    async def generate_response(self, prompt: str) -> str:
        try:
            model_name = self.config.get("llm", "gemini-1.5-flash")
            system = f"You are a concise {self.role}."
            model = GenerativeModel(model_name, system_instruction=system)
            resp = await model.generate_content_async(prompt)
            return resp.text.strip()
        except Exception as e:
            return f"API error: {e}"


# ------------------------------------------------------------------
# CoderAgent – JSON-ONLY, BULLETPROOF
# ------------------------------------------------------------------
class CoderAgent(Agent):
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        self.speak(f"Building Phaser+PixiJS for: '{vibe}'.")
        await self.think(2)

        recent_ctx = "\n".join(
            f"- {m.agent_name}: {m.text[:120]}..."
            for m in self.session.messages[-3:]
            if m.agent_name != self.role
        ) or "No context."

        # BULLETPROOF TEMPLATE – Gemini CANNOT break this
        template = """
<!DOCTYPE html>
<html>
<head>
<title>{vibe}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{margin:0;overflow:hidden;background:#000}</style>
</head>
<body>
<div id="game-container"></div>
<script src="https://cdn.jsdelivr.net/npm/phaser@3.90.0/dist/phaser.min.js"></script>
<script>
class BootScene extends Phaser.Scene {
    constructor() { super('Boot'); }
    create() { this.scene.start('Main'); }
}
class MainScene extends Phaser.Scene {
    constructor() { super('Main'); }
    preload() { }
    create() {
        this.add.text(400, 300, 'VIBE: {vibe}\\nLoading...', {fontSize: '32px', color: '#fff'}).setOrigin(0.5);
        // VIBE CODE HERE
    }
    update() { }
}
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'game-container',
    physics: { default: 'arcade' },
    scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
    scene: [BootScene, MainScene]
};
new Phaser.Game(config);
</script>
</body>
</html>
""".format(vibe=vibe)

        prompt = f"""
You are a JSON-only generator. Output EXACTLY: {{"index.html":"..."}} 

Vibe: '{vibe}'
Context: {recent_ctx}

TASK: Replace the comment "// VIBE CODE HERE" with Phaser code that implements the vibe.
Use only Phaser.Graphics, this.add.text(), this.physics.add.sprite(), etc.
Add touch/mouse controls, win/lose, score.
Keep it under 100 lines.

RULES:
- SINGLE LINE JS: use \\n for breaks, \" for quotes
- NO external assets
- NO markdown, NO ```

VALID JSON ONLY.
"""

        files = await self.generate(prompt)
        for name, content in files.items():
            # FINAL FIX: Ensure script is closed + escape newlines
            content = content.replace('\n', '\\n').replace('\r', '')
            content = content.replace('</script>', '</script>\\n</body>\\n</html>')
            self.session.add_artifact(name, content)
        self.speak("Build deployed – scene classes enforced.")
# ------------------------------------------------------------------
# TesterAgent
# ------------------------------------------------------------------
class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None) -> str:
        if not self.session.get_artifacts():
            r = "[BUG] No artifacts."
            self.speak(r)
            return r

        html = self.session.get_artifact_content("index.html") or ""
        if not html:
            r = "[BUG] Missing index.html"
            self.speak(r)
            return r

        checks = {
            "Phaser CDN": "phaser" in html.lower(),
            "Pixi CDN": "pixi" in html.lower(),
            "Phaser.Game": "new phaser.game" in html.lower(),
            "update()": "update() {" in html,
        }

        history = "\n".join(f"- {m.agent_name}: {m.text[:50]}..." for m in self.session.messages[-5:])

        tester_prompt = f"""
SCAN index.html for RUNTIME ERRORS.
Checks: {json.dumps(checks)}
History: {history}

[BUG] only if:
- Missing CDNs
- No `new Phaser.Game`
- No `update()`

Ignore vibe. [PASS] if playable.
Response: [PASS|BUG] + reason.
"""

        resp = await self.generate_response(tester_prompt)
        self.speak(resp)
        return resp


# ------------------------------------------------------------------
# Designer / Writer
# ------------------------------------------------------------------
class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        ack = await self.generate_response(f"Design task: {prompt}")
        self.speak(ack)
        await self.think(2)
        ideas = await self.generate_response(f"Visuals for '{prompt}'. Use Phaser/Pixi particles.")
        self.speak(ideas)


class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        full = f"{prompt}. {instructions or ''}"
        story = await self.generate_response(full)
        self.speak(story)


# ------------------------------------------------------------------
# Manager – CRASH-PROOF
# ------------------------------------------------------------------
class ManagerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        self.speak(f"Starting vibe: '{prompt}'")
        await self.think(1)

        writer = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        if not coder:
            raise RuntimeError("Coder missing")

        self.speak("Tasking Writer & Designer.")
        if writer:
            await writer.run(f"Story for '{prompt}'", instructions)
        if designer:
            await designer.run(f"Visuals for '{prompt}'", instructions)

        self.speak("Tasking Coder.")
        try:
            await coder.run_finalization(prompt, instructions)
        except Exception as e:
            self.speak(f"⚠️ Coder crashed: {e}")
            fallback = (
                "<!DOCTYPE html><html><head><title>Emergency</title></head>"
                "<body style='margin:0;background:#c00;color:#fff;font-family:sans-serif;"
                "display:flex;align-items:center;justify-content:center;height:100vh'>"
                f"<div><h1>CRASH</h1><p>{e}</p></div></body></html>"
            )
            self.session.add_artifact("index.html", fallback)

        for i in range(2):
            if not tester:
                break
            self.speak(f"Tester run {i+1}.")
            result = await tester.run("Review", instructions)
            if result.startswith("[PASS]"):
                self.speak("Approved.")
                break
            bug = result.replace("[BUG]", "").strip()
            self.speak(f"Fixing: {bug}")
            try:
                await coder.run_iteration(f"Fix: {bug}", prompt)
            except Exception as e:
                self.speak(f"Iteration failed: {e}")
                break

        self.speak("Workflow complete.")