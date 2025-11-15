# --------------------------------------------------------------
# agents.py  –  full, clean file (replace everything)
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
# CoderAgent – JSON-only, bullet-proof
# ------------------------------------------------------------------
class CoderAgent(Agent):
    # ------------------------------------------------------------------
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        self.speak(
            await self.generate_response(
                f"Building Phaser+PixiJS game for vibe: '{vibe}'."
            )
        )
        await self.think(2)

        # ---- team context ------------------------------------------------
        ctx = "\n".join(
            f"- {m.agent_name}: {m.text}"
            for m in self.session.messages
            if m.agent_name != self.role
        ) or "No prior context."

        # ---- raw-string prompt (no Python escape problems) ---------------
        prompt = r"""
You are a **JSON-only** code generator. Output **exactly**:

{{"index.html":"<html>...</html>"}}

Vibe: '{vibe}'
Team context:
{ctx}
Instructions: {instructions}

MANDATORY RULES (break any → output is invalid):
1. ONE key → "index.html".
2. CDNs (exact URLs):
   <script src="https://cdn.jsdelivr.net/npm/phaser@3.90.0/dist/phaser.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/pixi.js@8.14.1/dist/pixi.min.js"></script>
3. NO external assets → use Phaser.Graphics / Pixi filters only.
4. HTML+JS **must be a SINGLE line** – use \\n for line-breaks, \" for quotes.
5. Phaser config:
   type: Phaser.AUTO, width:800, height:600, parent:'game-container',
   physics:{default:'arcade'},
   scale:{mode:Phaser.Scale.FIT, autoCenter:Phaser.Scale.CENTER_BOTH}
6. Boot scene: preload(){}, create(){this.scene.start('MainScene');}, update(){}
7. MainScene extends Phaser.Scene with preload/create/update.
8. Mobile-ready, touch/mouse, win/lose, restart.
9. NO markdown, NO ```, NO extra text.

VALID JSON ONLY.
""".format(vibe=vibe, ctx=ctx, instructions=instructions or "None")

        files = await self._generate(prompt)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Phaser build ready.")

    # ------------------------------------------------------------------
    async def run_iteration(self, instruction: str, original_vibe: str):
        self.speak(await self.generate_response(f"Iterating: '{instruction}'."))
        await self.think(1)

        summary = f"Files: {', '.join(self.session.get_artifacts())}"
        prompt = r"""
REFINE the existing game.
Instruction: '{instruction}'
Original vibe: {original_vibe}
Current state: {summary}

Output **full** {{"index.html":"..."}} obeying ALL rules above.
VALID JSON ONLY.
""".format(instruction=instruction, original_vibe=original_vibe, summary=summary)

        files = await self._generate(prompt)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Iteration applied.")

    # ------------------------------------------------------------------
    async def _generate(self, prompt: str, max_retries: int = 3) -> Dict[str, str]:
        model = GenerativeModel(
            self.config.get("llm", "gemini-1.5-pro"),
            system_instruction=(
                "JSON-only. Single key \"index.html\". "
                "Escape \" with \\\", line-breaks with \\n. "
                "Never use real new-lines inside the string. "
                "No markdown, no ```."
            ),
        )
        cfg = {
            "response_mime_type": "application/json",
            "max_output_tokens": 16384,
            "temperature": 0.0,
        }

        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = await model.generate_content_async(prompt, generation_config=cfg)
                raw = resp.text.strip()

                # Strip possible code fences
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

                data = json.loads(raw)
                html = data.get("index.html", "")

                if not html:
                    raise ValueError("Empty index.html")
                if "phaser" not in html.lower() or "pixi" not in html.lower():
                    raise ValueError("Missing CDNs")
                if "new Phaser.Game" not in html:
                    raise ValueError("Missing Phaser.Game init")

                self.speak(f"JSON parsed (attempt {attempt}).")
                return data

            except (json.JSONDecodeError, ValueError) as e:
                last_err = str(e)
                # TEMP DEBUG: Dump raw response + error to logs
                print(f"[DEBUG] Raw Gemini response: {resp.text}")
                print(f"[DEBUG] Parse error: {last_err}")
                # END TEMP DEBUG

                if attempt < max_retries:
                    prompt = (
                        f"{prompt}\n\n--- PREVIOUS ERROR ---\n{last_err}\n"
                        "Regenerate **valid** JSON with proper escaping."
                    )

        # ---- fallback ----------------------------------------------------
        fallback = (
            "<!DOCTYPE html><html><head><title>Fallback</title></head>"
            "<body style='margin:0;background:#111;color:#fff;font-family:sans-serif;"
            "display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div><h1>Code-gen failed</h1><p>{last_err or 'unknown'}</p>"
            "<p>Retry the workflow – the agents will fix it.</p></div></body></html>"
        )
        self.speak("Fallback HTML generated.")
        return {"index.html": fallback}


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
# Designer / Writer – unchanged
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
        self.speak(f"Manager: Kick off vibe: '{prompt}'")
        await self.think(1)

        writer = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        if not coder:
            raise RuntimeError("CoderAgent missing")

        self.speak("Manager: Tasking Writer & Designer.")
        if writer:
            await writer.run(f"Backstory + cutscenes for '{prompt}'", instructions)
        if designer:
            await designer.run(f"Visual concepts for '{prompt}'", instructions)

        self.speak("Manager: Tasking Coder.")
        await coder.run_finalization(prompt, instructions)

        max_retries = 2
        for i in range(max_retries):
            if not tester:
                self.speak("Manager: No Tester – assuming good.")
                break

            self.speak(f"Manager: Tester run {i+1}/{max_retries}.")
            result = await tester.run("Review artifacts", instructions)

            if result.startswith("[PASS]"):
                self.speak("Manager: Tester approved.")
                break

            bug = result.replace("[BUG]", "").strip()
            self.speak(f"Manager: Bug – sending to Coder: {bug}")
            await coder.run_iteration(f"Fix: {bug}", prompt)

            if i == max_retries - 1:
                self.speak("Manager: Max retries – finalising anyway.")

        self.speak("Manager: Workflow complete.")