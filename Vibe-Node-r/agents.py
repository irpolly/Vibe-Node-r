# --------------------------------------------------------------
# agents.py  (replace the whole file)
# --------------------------------------------------------------
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any
from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session


# ------------------------------------------------------------------
# Base Agent
# ------------------------------------------------------------------
class Agent:
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
        try:
            model_name = self.config.get("llm", "gemini-1.5-flash")
            system = f"You are an AI agent acting as a {self.role}. Be concise."
            model = GenerativeModel(model_name, system_instruction=system)
            resp = await model.generate_content_async(prompt)
            return resp.text.strip()
        except Exception as e:
            return f"API error: {e}"


    # --------------------------------------------------------------
    #  CoderAgent – the ONLY part you need to change
    # --------------------------------------------------------------
    async def _generate(self, prompt: str, max_retries: int = 3) -> Dict[str, str]:
        """
        Generates *valid* JSON → {"index.html": "<single-line html>"}
        Retries with the exact parse error until it works or falls back.
        """
        model = GenerativeModel(
            self.config.get("llm", "gemini-1.5-pro"),
            system_instruction=(
                "You are a JSON-only code generator. "
                "Output **exactly** one key: \"index.html\". "
                "Escape quotes with \\\", line-breaks with \\n. "
                "Never use real new-lines inside the string. "
                "No markdown, no ```, no extra text."
            )
        )
        cfg = {
            "response_mime_type": "application/json",
            "max_output_tokens": 16384,
            "temperature": 0.0,
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = await model.generate_content_async(prompt, generation_config=cfg)
                raw = resp.text.strip()

                # Strip any code-block wrappers Gemini loves to add
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

                data = json.loads(raw)                     # <-- this is where it used to die
                html = data.get("index.html", "")

                # Basic sanity – must contain the two CDNs and Phaser init
                if not html:
                    raise ValueError("Empty index.html")
                if "phaser" not in html.lower() or "pixi" not in html.lower():
                    raise ValueError("Missing Phaser/Pixi CDN")
                if "new Phaser.Game" not in html:
                    raise ValueError("Missing Phaser.Game init")

                self.speak(f"JSON parsed on attempt {attempt}.")
                return data

            except (json.JSONDecodeError, ValueError) as e:
                last_error = str(e)
                print(f"[Coder] attempt {attempt} failed → {last_error}")
                if attempt < max_retries:
                    # Feed the *exact* error back to Gemini so it can self-correct
                    prompt = (
                        f"{prompt}\n\n--- PREVIOUS ERROR ---\n{last_error}\n"
                        "Regenerate **valid** JSON with proper escaping."
                    )
                # else: fall through to fallback

        # --------------------------------------------------------------
        #  Fallback – never let the workflow crash
        # --------------------------------------------------------------
        fallback_html = (
            "<!DOCTYPE html><html><head><title>Code-gen fallback</title>"
            "</head><body style='margin:0;background:#111;color:#fff;font-family:sans-serif;"
            "display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div><h1>Code-gen failed</h1><p>{last_error or 'unknown'}</p>"
            "<p>Retry the workflow – the agents will fix it.</p></div></body></html>"
        )
        self.speak("Fallback HTML generated.")
        return {"index.html": fallback_html}

# ------------------------------------------------------------------
# TesterAgent – runtime sanity only
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

        # ----- quick string checks -----------------------------------------
        checks = {
            "Phaser CDN": "phaser" in html.lower(),
            "Pixi CDN": "pixi" in html.lower(),
            "Phaser.Game init": "new phaser.game" in html.lower(),
            "Scene class": "phaser.scene" in html.lower(),
            "update()": "update() {" in html,
        }

        history = "\n".join(
            f"- {m.agent_name}: {m.text[:50]}..."
            for m in self.session.messages[-5:]
        )

        tester_prompt = f"""
QA: SCAN index.html for RUNTIME ERRORS ONLY.
Checks: {json.dumps(checks, indent=2)}
History (last 5): {history}

[BUG] **only** if:
- Missing CDNs
- No `new Phaser.Game`
- No `update()` / empty create()
- Obvious syntax (unclosed {{}} or ; missing)

VIBE/SEMANTICS → IGNORE. [PASS] even if colours wrong.
Response format: [PASS|BUG] + one-sentence reason.
"""

        resp = await self.generate_response(tester_prompt)
        self.speak(resp)
        return resp


# ------------------------------------------------------------------
# Designer / Writer – unchanged (just keep the old ones)
# ------------------------------------------------------------------
class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        ack = await self.generate_response(f"Acknowledged design task: {prompt}")
        self.speak(ack)
        await self.think(2)
        ideas = await self.generate_response(
            f"Describe visual assets for '{prompt}'. Suggest Phaser/Pixi particles, GSAP UI, Howler.js sounds."
        )
        self.speak(ideas)


class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        full = f"{prompt}. {instructions or ''}"
        story = await self.generate_response(full)
        self.speak(story)


# ------------------------------------------------------------------
# Manager – unchanged
# ------------------------------------------------------------------
class ManagerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        self.speak(f"Manager: Kick off the project for the vibe: '{prompt}'")
        await self.think(1)

        writer = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        if not coder:
            raise RuntimeError("CoderAgent missing")

        # ---- ideation ----------------------------------------------------
        self.speak("Manager: Tasking Writer and Designer with initial concepts.")
        if writer:
            await writer.run(f"Backstory + cutscenes for vibe: '{prompt}'", instructions)
        if designer:
            await designer.run(f"Visual concepts for vibe: '{prompt}'", instructions)

        # ---- code --------------------------------------------------------
        self.speak("Manager: Tasking Coder with initial development.")
        await coder.run_finalization(prompt, instructions)

        # ---- test-fix loop (max 2 retries) -------------------------------
        max_retries = 2
        for i in range(max_retries):
            if not tester:
                self.speak("Manager: No Tester – assuming good.")
                break

            self.speak(f"Manager: Handing off to Tester (Attempt {i+1}/{max_retries}).")
            test = await tester.run("Review artifacts", instructions)

            if test.startswith("[PASS]"):
                self.speak("Manager: Tester approved. Done.")
                break

            bug = test.replace("[BUG]", "").strip()
            self.speak(f"Manager: Bug found – sending back to Coder. Report: {bug}")
            await coder.run_iteration(f"Fix: {bug}", prompt)

            if i == max_retries - 1:
                self.speak("Manager: Max retries reached – finalising anyway.")

        self.speak("Manager: Workflow complete.")