# agents.py (improved)
import asyncio
import json
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

if TYPE_CHECKING:
    from session import Session

# ---------------------------------------------------------------------------
# Helper – CSS-styled “speak” (restored from old for UI chat bubbles)
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

def _clean_json(raw: str) -> str:
    if raw.startswith("```json"): raw = raw[7:]
    if raw.endswith("```"): raw = raw[:-3]
    return raw.strip()

class Agent:
    def __init__(self, node_id: str, config: Dict[str, Any], session: 'Session'):
        self.node_id = node_id
        self.config = config
        self.session = session
        self.role = config.get('role', 'Unnamed Agent')

    async def think(self, duration_s: float = 1.0):
        await asyncio.sleep(duration_s)

    # ------------------------------------------------------------------- #
    # speak → CSS-styled HTML (restored from old)
    # ------------------------------------------------------------------- #
    def speak(self, text: str):
        html = _css_speak(self.role, text)
        print(f"[{self.role}]: {text}")               # keep console log
        self.session.add_message(self.role, html)     # UI receives HTML

    async def generate(self, prompt: str) -> str:
        if not VERTEX_AVAILABLE:
            return "Vertex AI not available."
        try:
            model_name = self.config.get("llm", "gemini-1.5-flash")
            system = f"You are a professional {self.role}. Be concise but detailed. Focus on creating a playable HTML5 game."
            model = GenerativeModel(model_name, system_instruction=system)
            resp = await model.generate_content_async(prompt)
            return resp.text.strip()
        except Exception as e:
            err = f"Gemini error: {e}"
            print(err)
            return err

    async def run(self, vibe: str, instructions: str | None = None):
        raise NotImplementedError

# ---------------------------------------------------------------------------
# Export create_agents for main.py (from new)
# ---------------------------------------------------------------------------
def create_agents(canvas_cfg: Dict[str, Any]) -> Dict[str, "Agent"]:
    import importlib
    agents_mod = importlib.import_module('agents')
    agents: Dict[str, "Agent"] = {}

    for node in canvas_cfg.get('nodes', []):
        if node.get('type') != 'agentNode':
            continue
        label = node['data']['label']
        class_name = Session.AGENT_MAP.get(label)
        if not class_name:
            continue
        cls = getattr(agents_mod, class_name, Agent)
        agents[node['id']] = cls(
            node_id=node['id'],
            config=node['data'].get('config', {}),
            session=None  # Injected later
        )
    return agents

# ---------------------------------------------------------------------------
# ManagerAgent (merge: restore phases/loop from old, keep simplified run from new)
# ---------------------------------------------------------------------------
class ManagerAgent(Agent):
    async def run(self, vibe: str, instructions: str | None = None):
        self.speak(f"Starting project for vibe: “{vibe}”")
        await self.think(1)

        writer   = self._find(WriterAgent)
        designer = self._find(DesignerAgent)
        coder    = self._find(CoderAgent)
        tester   = self._find(TesterAgent)

        if not coder:
            raise Exception("Coder Agent is required – aborting workflow.")

        # ---- Phase 1: Ideation (Writer & Designer) ----
        self.speak("Phase 1 – Ideation: Writer & Designer")
        plan = ""
        assets = {}
        if writer:
            plan = await writer.run(vibe, instructions)
            self.session.add_artifact("PLAN.md", plan)
        if designer:
            assets = await designer.run(vibe, plan, instructions)
            for name, content in assets.items():
                self.session.add_artifact(name, content)

        # ---- Phase 2: Initial Code ----
        self.speak("Phase 2 – Initial code generation")
        files = await coder.run(vibe, plan, assets, instructions)
        for name, content in files.items():
            self.session.add_artifact(name, content)

        # ---- Phase 3: Test-Fix Loop (restored from old, max 2 retries) ----
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            if not tester:
                self.speak("No Tester in workflow – skipping QA.")
                break

            self.speak(f"Phase 3 – QA round {attempt}/{max_retries}")
            verdict = await tester.run(self.session.get_artifacts(), self.session)

            if verdict.strip().startswith("[PASS]"):
                self.speak("Tester passed – build is good.")
                break

            bug = verdict.replace("[BUG]", "", 1).strip()
            self.speak(f"Tester reported bug: {bug}")
            fixes = await coder.run_iteration(bug, vibe, plan, assets)
            for name, content in fixes.items():
                self.session.add_artifact(name, content)

            if attempt == max_retries:
                self.speak("Max QA retries reached – finalising anyway.")

        self.speak("Workflow complete – artifacts ready for preview/download.")

    async def run_instruction(self, instruction: str):  # Restored from old for iterations
        self.speak(f"New user instruction: “{instruction}”")
        coder = self._find(CoderAgent)
        if coder:
            plan = self.session.get_artifact_content("PLAN.md") or ""
            assets = {f: self.session.get_artifact_content(f) for f in self.session.get_artifacts() if f != "PLAN.md"}
            fixes = await coder.run_iteration(instruction, "", plan, assets)  # Vibe not needed for instruct
            for name, content in fixes.items():
                self.session.add_artifact(name, content)
        else:
            self.speak("No Coder Agent found to apply the instruction.")

    def _find(self, cls):
        return next((a for a in self.session.agents.values() if isinstance(a, cls)), None)

# ---------------------------------------------------------------------------
# WriterAgent (improved prompt for better narratives)
# ---------------------------------------------------------------------------
class WriterAgent(Agent):
    async def run(self, vibe: str, instructions: str | None = None):
        extra = f" Also consider: {instructions}" if instructions else ""
        prompt = f"""
        You are the Writer. Write a short backstory, core mechanics, and cut-scenes for vibe: “{vibe}”{extra}.
        Use [sound cue] for audio. Be concise: 1-2 paragraphs for backstory, bullet points for mechanics.
        """
        story = await self.generate(prompt)
        self.speak(story)
        return story

# ---------------------------------------------------------------------------
# DesignerAgent (from new, but restore text output + JSON)
# ---------------------------------------------------------------------------
class DesignerAgent(Agent):
    async def run(self, vibe: str, plan: str, instructions: str | None = None):
        extra = f" Also: {instructions}" if instructions else ""
        prompt = f"""
        Design visual concepts for vibe: “{vibe}”{extra}. Based on plan: {plan}.
        List assets (sprites, backgrounds, UI). Mention Phaser for integration, Howler for sound.
        Return JSON: {{"asset_name.png": "description", ...}}
        """
        assets_text = await self.generate(prompt)
        self.speak(assets_text)

        raw = _clean_json(assets_text)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"error.txt": "Designer failed to return valid JSON."}
        assets = {name: f"# Placeholder for {desc}" for name, desc in data.items()}
        return assets

# ---------------------------------------------------------------------------
# CoderAgent (from new, keep Phaser; restore JSON gen from old)
# ---------------------------------------------------------------------------
class CoderAgent(Agent):
    async def _gemini_json(self, prompt: str) -> Dict[str, str]:  # Restored from old for JSON output
        try:
            model_name = self.config.get("llm", "gemini-1.5-flash")
            system = (
                "You are a Coder Agent. Return **only** a JSON object where each key is a filename "
                "and each value is the complete file content. No markdown fences, no explanations."
            )
            model = GenerativeModel(model_name, system_instruction=system)

            generation_config = {
                "response_mime_type": "application/json",
                "max_output_tokens": 16384,
            }

            response = await model.generate_content_async(prompt, generation_config=generation_config)
            raw = _clean_json(response.text.strip())
            return json.loads(raw)
        except Exception as e:
            html = f"<html><body><h1>Coder Error</h1><pre>{e}</pre></body></html>"
            return {"error.html": html}

    async def run(self, vibe: str, plan: str, assets: Dict[str, str], instructions: str | None = None):
        asset_list = "\n".join(f"- {k}: {v.splitlines()[0] if v else ''}" for k, v in assets.items())
        instr = f" Also apply: {instructions}" if instructions else ""
        prompt = (
            f"Generate a **complete, playable Phaser 3 web game** for vibe “{vibe}”{instr}. "
            f"Plan: {plan}. Assets: {asset_list}. "
            "Return JSON with filenames (index.html, game.js, etc.) and full code. Load Phaser from CDN."
        )
        files = await self._gemini_json(prompt)
        return files

    async def run_iteration(self, instruction: str, vibe: str, plan: str, assets: Dict[str, str]):
        current_files = {f: self.session.get_artifact_content(f) for f in self.session.get_artifacts()}
        context = "\n".join([f"--- {fn} ---\n{c}\n" for fn, c in current_files.items()])
        prompt = (
            f"Current files:\n{context}\n\n"
            f"Original vibe: “{vibe}” Plan: {plan}\n"
            f"Apply change/fix: {instruction}\n"
            "Return JSON with **only changed files**."
        )
        updated = await self._gemini_json(prompt)
        return updated

# ---------------------------------------------------------------------------
# TesterAgent (restore LLM from old, keep file checks from new as pre-LLM)
# ---------------------------------------------------------------------------
class TesterAgent(Agent):
    async def run(self, artifact_names: List[str], session: "Session") -> str:
        files = {
            f: session.get_artifact_content(f)
            for f in artifact_names
            if session.get_artifact_content(f)
        }
        if not files:
            verdict = "[BUG] No artifacts found – Coder must generate files first."
            self.speak(verdict)
            return verdict

        # Pre-LLM basic checks (from new)
        if "index.html" not in files:
            return "[BUG] Missing index.html"
        js_files = [f for f in files if f.endswith(".js")]
        html = files["index.html"]
        missing_refs = [f for f in js_files if f not in html]
        if missing_refs:
            return f"[BUG] index.html does not reference: {', '.join(missing_refs)}"

        # LLM review (restored from old)
        code_block = "\n".join([f"--- {fn} ---\n{c}\n" for fn, c in files.items()])
        history = "\n".join([f"{m.agent_name}: {m.text}" for m in session.messages])
        tester_prompt = f"""
        You are a QA Tester. Review history and code for playability, bugs, vibe alignment.
        History: {history}
        Code: {code_block}
        Respond with [PASS] + confirmation OR [BUG] + actionable report.
        """
        verdict = await self.generate(tester_prompt)
        self.speak(verdict)
        return verdict