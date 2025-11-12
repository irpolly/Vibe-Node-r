# agents.py
import asyncio
import json
import os
from typing import TYPE_CHECKING, Dict, Any, List
from j

from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _clean_json(text: str) -> str:
    """Strip markdown fences if present."""
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# --------------------------------------------------------------------------- #
# Base Agent
# --------------------------------------------------------------------------- #
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

    async def generate(self, prompt: str) -> str:
        """One-shot call to Gemini (flash by default)."""
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            system = f"You are a professional {self.role}. Answer concisely."
            model = GenerativeModel(model_name, system_instruction=system)
            resp = await model.generate_content_async(prompt)
            return resp.text.strip()
        except Exception as e:
            err = f"Gemini error: {e}"
            print(err)
            return err

    # ------------------------------------------------------------------- #
    # Sub-classes must implement these
    # ------------------------------------------------------------------- #
    async def run(self, vibe: str, instructions: str | None = None):
        raise NotImplementedError

    async def run_iteration(self, instruction: str, vibe: str):
        """Called for user-driven changes."""
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Manager – single source of truth for artifacts
# --------------------------------------------------------------------------- #
class ManagerAgent(Agent):
    """
    1. Receives the vibe.
    2. Asks Writer for a design plan + script.
    3. Stores the plan, hands tasks to Designer → Coder → Tester.
    4. Holds *all* artifacts and only pushes a file to the session when it
       has been verified.
    """

    async def run(self, vibe: str, instructions: str | None = None):
        self.speak(f"Starting project for vibe: “{vibe}”")
        await self.think(0.5)

        # ------------------------------------------------------------------- #
        # 1. Writer creates the master plan
        # ------------------------------------------------------------------- #
        writer = self._find(WriterAgent)
        plan = await writer.run(vibe, instructions)
        self.session.add_artifact("PLAN.md", plan)          # store for everyone
        self.speak("Received design plan from Writer.")

        # ------------------------------------------------------------------- #
        # 2. Designer creates assets
        # ------------------------------------------------------------------- #
        designer = self._find(DesignerAgent)
        assets = await designer.run(vibe, plan, instructions)
        for name, content in assets.items():
            self.session.add_artifact(name, content)
        self.speak("All assets received from Designer.")

        # ------------------------------------------------------------------- #
        # 3. Coder builds the game
        # ------------------------------------------------------------------- #
        coder = self._find(CoderAgent)
        files = await coder.run(vibe, plan, assets, instructions)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Coder delivered initial build.")

        # ------------------------------------------------------------------- #
        # 4. Test-Fix loop (max 2 retries)
        # ------------------------------------------------------------------- #
        tester = self._find(TesterAgent)
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            self.speak(f"Handing build to Tester (attempt {attempt}).")
            verdict = await tester.run(self.session.get_artifacts(), self.session)
            if verdict.startswith("[PASS]"):
                self.speak("Tester approved the build – project complete!")
                break

            bug = verdict.replace("[BUG]", "").strip()
            self.speak(f"Tester found a bug: {bug}")
            fixes = await coder.run_iteration(bug, vibe, plan, assets)
            for name, content in fixes.items():
                self.session.add_artifact(name, content)
            self.speak("Coder applied fixes.")
        else:
            self.speak("Max retries reached – final build may contain bugs.")

    async def run_iteration(self, instruction: str, vibe: str):
        """User-driven change – delegate straight to Coder."""
        self.speak(f"User instruction: “{instruction}”")
        coder = self._find(CoderAgent)
        plan = self.session.get_artifact_content("PLAN.md") or ""
        assets = {
            f: self.session.get_artifact_content(f)
            for f in self.session.get_artifacts()
            if f not in ("PLAN.md",)
        }
        fixes = await coder.run_iteration(instruction, vibe, plan, assets)
        for name, content in fixes.items():
            self.session.add_artifact(name, content)
        self.speak("Applied user instruction.")

    # ------------------------------------------------------------------- #
    # tiny helpers
    # ------------------------------------------------------------------- #
    def _find(self, cls):
        return next((a for a in self.session.agents.values() if isinstance(a, cls)), None)

level_manifest = [
    {"key": "forest", "name": "Whispering Woods", "goal": "Find the Rune"},
    {"key": "city", "name": "Ruined City", "goal": "Defeat the Cultist"},
    {"key": "library", "name": "Arcane Library", "goal": "Solve the Puzzle"},
    {"key": "shadow", "name": "Shadow Plane", "goal": "Survive Inversion"},
    {"key": "boss", "name": "Final Arena", "goal": "Choose Your Fate"}
]

output_json["levels"] = level_manifest
output_json["config"]["scene"] = ["BootScene", "TitleScene", "PlayScene", "WinScene", "LoseScene"]
# --------------------------------------------------------------------------- #
# Writer – produces a single markdown design plan
# --------------------------------------------------------------------------- #
class WriterAgent(Agent):
    async def run(self, vibe: str, instructions: str | None, *_):
        prompt = f"""
You are the Writer. Turn the vibe “{vibe}” into a **complete design plan** in markdown.
Include:
* Game title
* Core loop
* Win / lose conditions
* List of required assets (images, sounds)
* List of source files the Coder must create
* Short narrative script (intro / win / lose)

{instructions or ""}
"""
        plan = await self.generate(prompt)
        self.speak("Design plan ready.")
        return plan

    async def run_iteration(self, *_):
        pass  # Writer never iterates


# --------------------------------------------------------------------------- #
# Designer – returns a dict {filename: base64-or-text-content}
# --------------------------------------------------------------------------- #
class DesignerAgent(Agent):
    async def run(self, vibe: str, plan: str, instructions: str | None, *_):
        prompt = f"""
You are the Designer. Using the plan below, list **every visual / audio asset** the game needs.
Return a JSON object where each key is the filename (e.g. "player.png") and the value is a
short description of the asset.  Generate real data pass to coder via manager, copies of raw assets to be output to zip file. titled "assets.zip". Raw uncompressed assets to be base64 encoded within json object.

Plan:
{plan}

{instructions or ""}
"""
        raw = await self.generate(prompt)
        raw = _clean_json(raw)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"error.txt": "Designer failed to return valid JSON."}

        # Store a placeholder file for each asset so the Coder knows the name
        assets = {}
        for name, desc in data.items():
            placeholder = f"# {name}\n# {desc}\n"
            assets[name] = placeholder
        self.speak(f"Designed {len(assets)} assets.")
        return assets

    async def run_iteration(self, *_):
        pass


# --------------------------------------------------------------------------- #
# Coder – builds *any* number of files, **never** uses Kaboom
# --------------------------------------------------------------------------- #
class CoderAgent(Agent):
    """
    Recommended engine: **Phaser 3** (self-contained, CDN-hosted).
    The coder may create as many .html, .js, .css, .json files as needed.
    """

    async def run(self, vibe: str, plan: str, assets: Dict[str, str], instructions: str | None):
        asset_list = "\n".join(f"- {k}: {v.splitlines()[1] if v else ''}".strip() for k, v in assets.items())
        prompt = f"""
You are the Coder. Implement the game as described in the plan.
Use **Phaser 3** (load from CDN).  Do **not** use Kaboom.

Plan:
{plan}

Required assets (Incorporate assets into the code, do not leave placeholders, do not give raw/unincorporated assets to user):
{asset_list}

Return a JSON object:
{{
  "index.html": "...",
  "game.js": "...",
  "style.css": "...",
  ... any other required/requested files ...
}}

{instructions or ""}
"""
        raw = await self.generate(prompt)
        raw = _clean_json(raw)
        try:
            files = json.loads(raw)
        except json.JSONDecodeError:
            files = {"error.html": f"<pre>Coder JSON error:\n{raw}</pre>"}

        self.speak(f"Generated {len(files)} source files.")
        return files

    async def run_iteration(self, bug: str, vibe: str, plan: str, assets: Dict[str, str]):
        """Fix a bug reported by Tester or a user instruction."""
        asset_list = "\n".join(f"- {k}" for k in assets)
        prompt = f"""
Coder, the Tester (or user) reported:

{bug}

Current plan:
{plan}

Current asset list:
{asset_list}

Fix the code and return **only the changed files** as JSON (same format as before).
"""
        raw = await self.generate(prompt)
        raw = _clean_json(raw)
        try:
            fixes = json.loads(raw)
        except json.JSONDecodeError:
            fixes = {"error.html": f"<pre>Iteration JSON error:\n{raw}</pre>"}
        self.speak("Applied fix.")
        return fixes


# --------------------------------------------------------------------------- #
# Tester – strict functional check only
# --------------------------------------------------------------------------- #
class TesterAgent(Agent):
    async def run(self, artifact_names: List[str], session: "Session") -> str:
        """
        1. Must have at least index.html + one .js file.
        2. HTML must reference the JS file(s).
        3. No syntax errors detectable by a quick regex (good enough for demo).
        """
        files = {
            f: session.get_artifact_content(f) or ""
            for f in artifact_names
            if not f.endswith(".md")
        }

        # ---- basic presence -------------------------------------------------
        if "index.html" not in files:
            return "[BUG] Missing index.html"
        if not any(f.endswith(".js") for f in files):
            return "[BUG] No JavaScript file found"

        html = files["index.html"]
        js_files = [f for f in files if f.endswith(".js")]
        missing_refs = [f for f in js_files if f not in html]
        if missing_refs:
            return f"[BUG] index.html does not reference: {', '.join(missing_refs)}"

        # ---- very light syntax check ----------------------------------------
        for name, code in files.items():
            if name.endswith(".js"):
                if "function" in code and "{" in code and "}" not in code:
                    return f"[BUG] Unclosed brace in {name}"
                if "Phaser.Game(" in code and "config" not in code:
                    return f"[BUG] Phaser.Game called without config in {name}"

        self.speak("Functional checks passed.")
        return "[PASS] Build is functionally complete and playable."

    async def run_iteration(self, *_):
        pass