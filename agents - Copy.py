# agents.py
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any

from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session

# --------------------------------------------------------------------- #
#  Plain-text speak – UI will colour it via agentColors
# --------------------------------------------------------------------- #
def _plain_speak(self, text: str):
    print(f"[{self.role}]: {text}")
    self.session.add_message(self.role, text)

# ---------------------------------------------------------------------------
# Helper – CSS-styled “speak”
# ---------------------------------------------------------------------------
def _css_speak(role: str, text: str) -> str:
    """
    Returns an HTML snippet that the UI will inject into the chat bubble.
    Colors match the agent palette defined in constants.tsx.
    """
    color_map = {
        "Manager Agent": "bg-orange-600 text-white",
        "Coder Agent":   "bg-blue-600 text-white",
        "Designer Agent":"bg-purple-600 text-white",
        "Tester Agent":  "bg-green-600 text-white",
        "Writer Agent":  "bg-rose-600 text-white",
    }
    bg = color_map.get(role, "bg-gray-600 text-white")
    return f'<div class="inline-block px-3 py-1.5 rounded-lg {bg} text-sm font-medium">{text}</div>'

# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------
class Agent:
    def __init__(self, node_id: str, config: Dict[str, Any], session: 'Session'):
        self.node_id = node_id
        self.config = config
        self.session = session
        self.role = config.get('role', 'Unnamed Agent')

    async def think(self, duration_s: float = 1.0):
        await asyncio.sleep(duration_s)

    # ------------------------------------------------------------------- #
    # NEW: speak → CSS-styled HTML
    # ------------------------------------------------------------------- #
    def speak(self, text: str):
        html = _css_speak(self.role, text)
        print(f"[{self.role}]: {text}")               # keep console log
        self.session.add_message(self.role, html)     # UI receives HTML

    async def generate_response(self, prompt: str) -> str:
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            system_instruction = (
                f"You are an AI agent acting as a {self.role} in a team. "
                "Be professional but concise."
            )
            model = GenerativeModel(model_name, system_instruction=system_instruction)
            response = await model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            err = f"Gemini error: {e}"
            print(f"Error for {self.role}: {err}")
            return f"I hit an API problem – see server logs. ({e})"

    async def run(self, prompt: str, instructions: str | None = None):
        raise NotImplementedError

# ---------------------------------------------------------------------------
# ManagerAgent – orchestrates phases (same logic, CSS speak)
# ---------------------------------------------------------------------------
class ManagerAgent(Agent):
    async def run(self, vibe: str, instructions: str | None = None):
        self.speak(f"Starting project for vibe: “{vibe}”")
        await self.think(1)

        writer   = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder    = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester   = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        if not coder:
            raise Exception("Coder Agent is required – aborting workflow.")

        # ---- Phase 1: Ideation ------------------------------------------------
        self.speak("Phase 1 – Ideation: Writer & Designer")
        if writer:
            await writer.run(f"Write a short backstory & cut-scenes for vibe: “{vibe}”", instructions)
        if designer:
            await designer.run(f"Design visual concepts for vibe: “{vibe}”", instructions)

        # ---- Phase 2: Initial Code --------------------------------------------
        self.speak("Phase 2 – Initial code generation")
        await coder.run_finalization(vibe, instructions)

        # ---- Phase 3: Test-Fix Loop (max 2 retries) ---------------------------
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            if not tester:
                self.speak("No Tester in workflow – skipping QA.")
                break

            self.speak(f"Phase 3 – QA round {attempt}/{max_retries}")
            verdict = await tester.run("Review current artifacts and return [PASS] or [BUG]…", instructions)

            if verdict.strip().startswith("[PASS]"):
                self.speak("Tester passed – build is good.")
                break

            bug = verdict.replace("[BUG]", "", 1).strip()
            self.speak(f"Tester reported bug: {bug}")
            await coder.run_iteration(f"Fix the following bug: {bug}", vibe)

            if attempt == max_retries:
                self.speak("Max QA retries reached – finalising anyway.")

        self.speak("Workflow complete – artifacts ready for preview/download.")

    async def run_instruction(self, instruction: str):
        self.speak(f"New user instruction: “{instruction}”")
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        if coder:
            await coder.run_iteration(instruction, "user-directed change")
        else:
            self.speak("No Coder Agent found to apply the instruction.")

# ---------------------------------------------------------------------------
# CoderAgent – JSON file generation (CSS speak)
# ---------------------------------------------------------------------------
# === GROUNDED CODER AGENT – PHASER 3 EDITION (drop-in replacement for agents.py) ===
class CoderAgent(Agent):
    # ⚡ PHASER 3 BOILERPLATE – battle-tested, always works
    BOILERPLATE = {
        "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Vibe Game</title>
  <link rel="stylesheet" href="style.css" />
  <!-- PHASER 3 CDN -->
  <script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>
  <!-- GSAP for UI -->
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.2/dist/gsap.min.js"></script>
  <!-- Howler for audio -->
  <script src="https://cdn.jsdelivr.net/npm/howler@2.2.4/dist/howler.min.js"></script>
</head>
<body>
  <div id="game"></div>
  <script src="game.js"></script>
</body>
</html>""",
        "style.css": """* { margin:0; padding:0; box-sizing:border-box; }
body, html { 
  width:100%; height:100%; overflow:hidden; 
  background:#111; font-family:monospace;
}
#game { width:100vw; height:100vh; }""",
        "game.js": """// PHASER 3 GAME BOILERPLATE
const config = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  parent: 'game',
  scene: { preload: preload, create: create, update: update },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  backgroundColor: '#111827'
};

let game = new Phaser.Game(config);

function preload() {
  // Assets loaded here
  this.load.image('background', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==');
}

function create() {
  // Game starts here
  this.add.text(400, 300, 'Vibe Game Ready!', { 
    fontSize: '32px', fill: '#38bdf8', 
    stroke: '#000', strokeThickness: 4 
  }).setOrigin(0.5);
}

function update() {
  // Game loop
}
"""
    }

    async def _gemini_json(self, prompt: str) -> Dict[str, str]:
        """Force JSON output (unchanged from before)"""
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            system = (
                "You are a Coder Agent. Return **only** a JSON object where each key is a filename "
                "and each value is the complete file content. No markdown fences, no explanations."
            )
            model = GenerativeModel(model_name, system_instruction=system)

            generation_config = {
                "response_mime_type": "application/json",
                "max_output_tokens": 16384,
                "thinking_config": {"thinking_budget": 8192}
            }

            response = await model.generate_content_async(prompt, generation_config=generation_config)
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.endswith("```"): raw = raw[:-3]
            return json.loads(raw)
        except Exception as e:
            html = f"""
            <html><head><title>Coder Error</title></head>
            <body style="font-family:monospace;background:#111;color:#f00;">
            <h1>Phaser 3 Coder Failure</h1><pre>{e}</pre>
            </body></html>
            """
            return {"error.html": html}

    async def run_finalization(self, vibe: str, instructions: str | None = None):
        """🚀 Generate complete Phaser 3 game from vibe"""
        instr = f" Also apply: {instructions}" if instructions else ""
        prompt = f"""
You are a professional Phaser 3 game developer.

**TASK**: Build a **complete, playable Phaser 3 web game** for vibe: "{vibe}"{instr}

**MANDATORY STRUCTURE** (return JSON with EXACTLY these 3 files):
1. `index.html` → Use the HTML boilerplate with Phaser 3.80.1 CDN, GSAP, Howler
2. `style.css` → Responsive, mobile-first, dark theme (#111827 bg)
3. `game.js` → **Full Phaser 3 game** with preload/create/update"""

**PHASER 3 RULES**:

# ---------------------------------------------------------------------------
# DesignerAgent – CSS speak
# ---------------------------------------------------------------------------
class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        extra = f" Also: {instructions}" if instructions else ""
        plan = await self.generate_response(f"Design visual assets for vibe: “{prompt}”{extra}")
        self.speak(plan)

        assets_prompt = (
            f"List every visual asset you would create for the game described above. "
            "Include sprites, backgrounds, UI elements, particle effects, etc. "
            "Mention libraries (Kaboom, Phaser, GSAP) and sound cues (Howler). "
            "End with: “Sending asset list to Coder.”"
        )
        assets = await self.generate_response(assets_prompt)
        self.speak(assets)

# ---------------------------------------------------------------------------
# TesterAgent – CSS speak, returns [PASS]/[BUG]
# ---------------------------------------------------------------------------
class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None) -> str:
        files = {
            f: self.session.get_artifact_content(f)
            for f in self.session.get_artifacts()
            if self.session.get_artifact_content(f)
        }
        if not files:
            verdict = "[BUG] No artifacts found – Coder must generate files first."
            self.speak(verdict)
            return verdict

        code_block = "\n".join([f"--- {fn} ---\n{c}\n" for fn, c in files.items()])
        history = "\n".join([f"{m.agent_name}: {m.text}" for m in self.session.messages])

        tester_prompt = f"""
        You are a QA Tester. Review the project history and current code.

        History:
        {history}

        Current files:
        {code_block}

        Respond **exactly** with:
        - `[PASS]` + short confirmation **or**
        - `[BUG]` + concise, actionable bug report for the Coder.
        """

        verdict = await self.generate_response(tester_prompt)
        self.speak(verdict)
        return verdict

# ---------------------------------------------------------------------------
# WriterAgent – CSS speak
# ---------------------------------------------------------------------------
class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        extra = f" Also consider: {instructions}" if instructions else ""
        full = f"{prompt}{extra} Write a short backstory and opening/closing cut-scenes. "
        full += "Use [sound cue] notation so the Coder can implement audio."
        story = await self.generate_response(full)
        self.speak(story)