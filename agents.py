# agents.py
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any, List
from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session

# --------------------------------------------------------------------------- #
#  Base Agent
# --------------------------------------------------------------------------- #
class Agent:
    """Base class for all agents in the system."""

    def __init__(self, node_id: str, config: Dict[str, Any], session: 'Session'):
        self.node_id = node_id
        self.config = config
        self.session = session
        self.role = config.get('role', 'Unnamed Agent')

    async def think(self, duration_s: float = 1.0):
        await asyncio.sleep(duration_s)

    def speak(self, text: str):
        print(f"[{self.role}]: {text}")
        self.session.add_message(self.role, text)

    async def generate_response(self, prompt: str) -> str:
        """Call Gemini (system instruction forces concise, professional tone)."""
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            system_instruction = (
                f"You are an AI agent acting as a {self.role} in a team. "
                "Be professional but concise. Answer in 1-2 sentences."
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

# --------------------------------------------------------------------------- #
#  ManagerAgent – orchestrates the exact phases described in the README
# --------------------------------------------------------------------------- #
class ManagerAgent(Agent):
    """
    1. Kick-off → Writer + Designer (ideation)
    2. Coder → initial code generation
    3. Tester → test-fix loop (max 2 retries)
    4. Finalise
    """
    async def run(self, vibe: str, instructions: str | None = None):
        self.speak(f"Starting project for vibe: “{vibe}”")
        await self.think(1)

        # locate peers
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
        """Iterative user command → always routed to Coder."""
        self.speak(f"New user instruction: “{instruction}”")
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        if coder:
            await coder.run_iteration(instruction, "user-directed change")
        else:
            self.speak("No Coder Agent found to apply the instruction.")

# --------------------------------------------------------------------------- #
#  CoderAgent – JSON-structured file generation (README step 5)
# --------------------------------------------------------------------------- #
class CoderAgent(Agent):
    async def _gemini_json(self, prompt: str) -> Dict[str, str]:
        """Force Gemini to return a JSON map {filename: content}."""
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            system = (
                "You are a Coder Agent. Return a JSON object where each key is a filename "
                "and each value is the complete file content. No markdown fences, no explanations."
            )
            model = GenerativeModel(model_name, system_instruction=system)

            generation_config = {
                "response_mime_type": "application/json",
                "max_output_tokens": 30208,
                "thinking_config": {"thinking_budget": 12800}
            }

            response = await model.generate_content_async(prompt, generation_config=generation_config)
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.endswith("```"): raw = raw[:-3]
            return json.loads(raw)
        except Exception as e:
            # Fallback error page – still returns a dict so the caller never breaks
            html = f"""
            <html><head><title>Coder Error</title></head>
            <body style="font-family:monospace;background:#111;color:#f00;">
            <h1>Coder Agent Failure</h1><pre>{e}</pre>
            </body></html>
            """
            return {"error.html": html}

    async def run_finalization(self, vibe: str, instructions: str | None = None):
        instr = f" Also apply: {instructions}" if instructions else ""
        prompt = (
            f"Generate a **single level, playable web game** for the vibe “{vibe}”{instr}. "
            "Return a JSON object with filenames (e.g., index.html, style.css, game.js) "
            "and their full source code. Use Kaboom.js / Phaser for game logic, "
            "GSAP for UI animations, Howler.js for audio."
        )
        files = await self._gemini_json(prompt)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Initial code generation finished – files saved as artifacts.")

    async def run_iteration(self, instruction: str, original_vibe: str):
        # Provide current files so the model can edit in-place
        current = {
            f: self.session.get_artifact_content(f)
            for f in self.session.get_artifacts()
            if self.session.get_artifact_content(f)
        }
        context = "\n".join([f"--- {fn} ---\n{c}\n" for fn, c in current.items()])

        prompt = (
            f"Current project files:\n{context}\n\n"
            f"Original vibe: “{original_vibe}”\n"
            f"Apply the following change: {instruction}\n"
            "Return a **new JSON object** containing **only the files that changed** "
            "(or the full set if easier). Keep existing files untouched unless modified."
        )
        updated = await self._gemini_json(prompt)
        for name, content in updated.items():
            self.session.add_artifact(name, content)
        self.speak(f"Applied instruction – updated {len(updated)} file(s).")

# --------------------------------------------------------------------------- #
#  DesignerAgent – produces descriptive asset list (README step 4)
# --------------------------------------------------------------------------- #
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

# --------------------------------------------------------------------------- #
#  TesterAgent – returns [PASS] or [BUG] (README step 6)
# --------------------------------------------------------------------------- #
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

        Respond with:
        - `[PASS]` + short confirmation **or**
        - `[BUG]` + concise, actionable bug report for the Coder.
        """
        verdict = await self.generate_response(tester_prompt)
        self.speak(verdict)
        return verdict

# --------------------------------------------------------------------------- #
#  WriterAgent – generates story & cut-scenes (README step 4)
# --------------------------------------------------------------------------- #
class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        extra = f" Also consider: {instructions}" if instructions else ""
        full = f"{prompt}{extra} Write a short backstory and opening/closing cut-scenes. "
        full += "Use [sound cue] notation so the Coder can implement audio."
        story = await self.generate_response(full)
        self.speak(story)