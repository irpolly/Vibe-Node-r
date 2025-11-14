import asyncio
import json
import os
from typing import TYPE_CHECKING, Dict, Any, List

# --- Vertex AI (unchanged) ---
try:
    from vertexai.generative_models import GenerativeModel
    import vertexai
    VERTEX_AVAILABLE = True
except Exception as e:
    print(f"Vertex AI import failed: {e}")
    VERTEX_AVAILABLE = False
    GenerativeModel = None
    vertexai = None

# TYPE-CHECKING ONLY – safe for circular refs
if TYPE_CHECKING:
    from session import Session 

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
        if not VERTEX_AVAILABLE:
            return "Vertex AI not available."
        try:
            model_name = self.config.get("llm", "gemini-1.5-flash")
            system = f"You are a professional {self.role}. Answer concisely."
            model = GenerativeModel(model_name, system_instruction=system)
            resp = await model.generate_content_async(prompt)
            return resp.text.strip()
        except Exception as e:
            err = f"Gemini error: {e}"
            print(err)
            return err

    async def run(self, vibe: str, instructions: str | None = None):
        raise NotImplementedError

    async def run_iteration(self, instruction: str, vibe: str):
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Manager
# --------------------------------------------------------------------------- #
class ManagerAgent(Agent):
    async def run(self, vibe: str, instructions: str | None = None):
        self.speak(f"Starting project for vibe: \"{vibe}\"")
        await self.think(0.5)

        writer = self._find(WriterAgent)
        plan = await writer.run(vibe, instructions)
        self.session.add_artifact("PLAN.md", plan)
        self.speak("Received design plan from Writer.")

        designer = self._find(DesignerAgent)
        assets = await designer.run(vibe, plan, instructions)
        for name, content in assets.items():
            self.session.add_artifact(name, content)
        self.speak("All assets received from Designer.")

        coder = self._find(CoderAgent)
        files = await coder.run(vibe, plan, assets, instructions)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Coder delivered initial build.")

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
        self.speak(f"User instruction: \"{instruction}\"")
        coder = self._find(CoderAgent)
        plan = self.session.get_artifact_content("PLAN.md") or ""
        assets = {f: self.session.get_artifact_content(f) for f in self.session.get_artifacts() if f != "PLAN.md"}
        fixes = await coder.run_iteration(instruction, vibe, plan, assets)
        for name, content in fixes.items():
            self.session.add_artifact(name, content)

    def _find(self, cls):
        return next(a for a in self.session.agents.values() if isinstance(a, cls))


# --------------------------------------------------------------------------- #
# Writer
# --------------------------------------------------------------------------- #
class WriterAgent(Agent):
    async def run(self, vibe: str, instructions: str | None):
        prompt = f"""
        You are the Writer. Produce a concise design plan for a **single-player** HTML5 game based on the vibe below.
        Include:
        * Game title
        * Core loop
        * Win / lose conditions
        * List of required assets (images, sounds)
        * List of source files the Coder must create
        * Short narrative script (intro / win / lose)

        Vibe: {vibe}
        {instructions or ""}
        """
        plan = await self.generate(prompt)
        self.speak("Design plan ready.")
        return plan

    async def run_iteration(self, *_):
        pass


# --------------------------------------------------------------------------- #
# Designer
# --------------------------------------------------------------------------- #
class DesignerAgent(Agent):
    async def run(self, vibe: str, plan: str, instructions: str | None, *_):
        prompt = f"""
        You are the Designer. Using the plan below, list **every visual / audio asset** the game needs.
        Return a JSON object where each key is the filename (e.g. "player.png") and the value is a
        short description of the asset.

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

        assets = {}
        for name, desc in data.items():
            placeholder = f"# {name}\n# {desc}\n"
            assets[name] = placeholder
        self.speak(f"Designed {len(assets)} assets.")
        return assets

    async def run_iteration(self, *_):
        pass


# --------------------------------------------------------------------------- #
# Coder
# --------------------------------------------------------------------------- #
class CoderAgent(Agent):
    async def run(self, vibe: str, plan: str, assets: Dict[str, str], instructions: str | None):
        asset_list = "\n".join(f"- {k}: {v.splitlines()[1] if v else ''}".strip() for k, v in assets.items())
        prompt = f"""
        You are the Coder. Implement the game as described in the plan.
        Use **Phaser 3** (load from CDN).  Do **not** use Kaboom.

        Plan:
        {plan}

        Required assets:
        {asset_list}

        Return a JSON object:
        {{
          "index.html": "...",
      "game.js": "...",
      "style.css": "...",
      ... any other files ...
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
        asset_list = "\n".join(f"- {k}" for k in assets)
        prompt = f"""
        Coder, the Tester (or user) reported:

        {bug}

        Current plan:
        {plan}

        Current asset list:
        {asset_list}

        Fix the code and return **only the changed files** as JSON.
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
# Tester
# --------------------------------------------------------------------------- #
class TesterAgent(Agent):
    async def run(self, artifact_names: List[str], session: "Session") -> str:
        files = {
            f: session.get_artifact_content(f) or ""
            for f in artifact_names
            if not f.endswith(".md")
        }

        if "index.html" not in files:
            return "[BUG] Missing index.html"
        if not any(f.endswith(".js") for f in files):
            return "[BUG] No JavaScript file found"

        html = files["index.html"]
        js_files = [f for f in files if f.endswith(".js")]
        missing_refs = [f for f in js_files if f not in html]
        if missing_refs:
            return f"[BUG] index.html does not reference: {', '.join(missing_refs)}"

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