
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any

# --- HARD CODED PROJECT SETTINGS ---
import vertexai
vertexai.init(
    project="cloud-run-hackathon-477510",
    location="europe-west4"
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
# CoderAgent – Guided Generation + Self-Debug Loop
# ------------------------------------------------------------------
class CoderAgent(Agent):
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        self.speak(f"Generating for '{vibe}' – using shared state.")
        await self.think(2)

        # Pull from shared
        sprites = self.session.get_shared("sprites") or "{}"
        script = self.session.get_shared("script") or "[]"
        
        # Slim prompt – chunked to avoid truncation
        head_prompt = f"HTML head for '{vibe}' – title, viewport, style. JSON: {{\"head\": \"<head>...</head>\"}}"
        head = await self.generate_response(head_prompt)
        
        create_prompt = f"Phaser create() for '{vibe}'. Use sprites: {sprites}. Add controls, score. JSON: {{\"create\": \"this.add...\"}}"
        create = await self.generate_response(create_prompt)
        
        update_prompt = f"Phaser update() for '{vibe}'. Game loop, collisions. JSON: {{\"update\": \"if (cursors...\"}}"
        update = await self.generate_response(update_prompt)
        
        # Assemble
        full_js = (
            f"class Play extends Phaser.Scene {{\n"
            f"  constructor() {{ super('Play'); }}\n"
            f"  preload() {{}}\n"
            f"  create() {{ {create} }}\n"
            f"  update() {{ {update} }}\n"
            f"}}\n"
            f"new Phaser.Game({{\n"
            f"  type: Phaser.AUTO,\n"
            f"  width: 800,\n"
            f"  height: 600,\n"
            f"  parent: 'game',\n"
            f"  physics: {{ default: 'arcade' }},\n"
            f"  scale: {{ mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH }},\n"
            f"  scene: [Boot, Play]\n"
            f"}});"
        )        
        html = f"<!DOCTYPE html><html><head>{head}</head><body><div id='game'></div><script src='https://cdn.jsdelivr.net/npm/phaser@3.90.0/dist/phaser.min.js'></script><script>{full_js}</script></body></html>"
        
        self.session.set_shared("full_html", html)
        self.session.add_artifact("index.html", html)
        
        # SELF-DEBUG LOOP
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)
        for i in range(3):
            if tester:
                result = await tester.run("Debug full_html")
                if "[PASS]" in result:
                    self.speak("Self-debug: PASS.")
                    break
                fix_prompt = f"Fix bug: {result} in code: {html[:500]}... Output fixed HTML JSON: {{\"fixed\": \"<html>...\"}}"
                fixed = await self.generate_response(fix_prompt)
                html = fixed.get("fixed", html)
                self.session.set_shared("full_html", html)
                self.session.add_artifact("index.html", html)
                self.speak(f"Self-debug iteration {i+1}: Fixed {result}.")
        
        self.speak("Code deployed – self-debug complete.")

    async def run_iteration(self, instruction: str, original_vibe: str):
        html = self.session.get_shared("full_html") or ""
        prompt = f"Refine '{instruction}' in: {html}. Output fixed HTML JSON: {{\"fixed\": \"<html>...\"}}"
        fixed = await self.generate_response(prompt)
        new_html = fixed.get("fixed", html)
        self.session.set_shared("full_html", new_html)
        self.session.add_artifact("index.html", new_html)
        self.speak("Iteration applied.")

# ------------------------------------------------------------------
# TesterAgent – Simulated Debug + Gemini Review
# ------------------------------------------------------------------
class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None) -> str:
        html = self.session.get_shared("full_html") or ""
        if not html:
            return "[BUG] No full_html in shared state"

        # String checks
        checks = {
            "Phaser CDN": "phaser" in html,
            "Scene Class": "class Play extends Phaser.Scene" in html,
            "new Phaser.Game": "new Phaser.Game" in html,
            "create()": "create() {" in html,
            "update()": "update() {" in html,
        }

        # Gemini simulate
        debug_prompt = f"Simulate errors in this HTML: {html[:1000]}... Checks: {checks}. Output [PASS|BUG] + reason."
        result = await self.generate_response(debug_prompt)
        
        self.speak(result)
        return result
# ------------------------------------------------------------------
# DesignerAgent – Output JSON Sprites to Shared
# ------------------------------------------------------------------
class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        ack = await self.generate_response(f"Design task: {prompt}")
        self.speak(ack)
        await self.think(2)
        
        # Generate SVG sprites as JSON
        sprite_prompt = f"Generate SVG for '{prompt}'. Output JSON: {{\"sprites\": {{\"fish\": \"<svg>...</svg>\"}}}} – procedural, Phaser-ready."
        sprites = await self.generate_response(sprite_prompt)
        self.session.set_shared("sprites", sprites)
        self.speak(f"Sprites stored: {sprites[:100]}...")
        
        ideas = await self.generate_response(f"Visuals for '{prompt}'. Use Phaser/Pixi particles.")
        self.speak(ideas)


# ------------------------------------------------------------------
# WriterAgent – Output JSON Script to Shared
# ------------------------------------------------------------------
class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        full = f"{prompt}. {instructions or ''}"
        story_prompt = f"Story for '{full}'. Output JSON: {{\"script\": [{{\"speaker\": \"Narrator\", \"text\": \"...\"}}]}} – structured dialogue."
        script = await self.generate_response(story_prompt)
        self.session.set_shared("script", script)
        self.speak(f"Script stored: {script[:100]}...")
        
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
