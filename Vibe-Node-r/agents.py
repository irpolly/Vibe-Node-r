# --------------------------------------------------------------
# agents.py – FULL, CLEAN, FINAL (replace entire file)
# --------------------------------------------------------------
# Java Johnson: No more JSON bombs. Raw strings, embedded template, debug dumps.
# Forces single-line HTML/JS. Gemini can't escape.
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
# CoderAgent – JSON-ONLY, BULLETPROOF
# ------------------------------------------------------------------
class CoderAgent(Agent):
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        self.speak(f"Building your: '{vibe}'.")
        await self.think(2)

        ctx = "\n".join(
            f"- {m.agent_name}: {m.text}"
            for m in self.session.messages
            if m.agent_name != self.role
        ) or "No context."

        prompt = r"""
You are a html friendly generator. Output EXACTLY:

{"index.html":"<html>...</html>"}

Vibe: '{vibe}'
Context:
{ctx}
Instructions: {instructions}

RULES:
1. ONE key: "index.html"
2. CDNs:
   <script src="https://cdn.jsdelivr.net/npm/phaser@3.90.0/dist/phaser.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/pixi.js@8.14.1/dist/pixi.min.js"></script>

VALID JSON ONLY.
""".format(vibe=vibe, ctx=ctx, instructions=instructions or "None")

        files = await self._generate(prompt)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Build ready.")

    async def run_iteration(self, instruction: str, original_vibe: str):
        self.speak(f"Iterating: '{instruction}'.")
        await self.think(1)

        summary = f"Files: {', '.join(self.session.get_artifacts())}"
        prompt = r"""
REFINE game.
Instruction: '{instruction}'
Original vibe: {original_vibe}
State: {summary}

Output FULL {"index.html":"..."}. Follow ALL rules.
VALID JSON ONLY.
""".format(instruction=instruction, original_vibe=original_vibe, summary=summary)

        files = await self._generate(prompt)
        for name, content in files.items():
            self.session.add_artifact(name, content)
        self.speak("Iteration applied.")

    async def _generate(self, prompt: str, max_retries: int = 3) -> Dict[str, str]:
        """
        Generates {"index.html": "<single-line HTML+JS>"}.
        Handles Gemini truncation, malformed JSON, and self-corrects.
        FULL DEBUG LOGS in Cloud Run.
        """
        model = GenerativeModel(
            self.config.get("llm", "gemini-1.5-pro"),
            system_instruction=(
                "You are a JSON-only generator. Output EXACTLY one key: \"index.html\". "
                "Escape every \" with \\\" and every newline with \\n. "
                "Never emit real newlines inside the string. No markdown. No ```."
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

                # ===== DEBUG: FULL RAW RESPONSE (REMOVE WHEN STABLE) =====
                print(f"[CODER DEBUG] attempt {attempt} RAW RESPONSE:\n{raw}\n{'=' * 80}")

                # Strip markdown fences
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

                # ===== FIX TRUNCATION: Remove broken suffixes like '"index' =====
                if raw.endswith('"index') or raw.endswith('"index.html') or raw.endswith('"index.html"'):
                    print(f"[CODER DEBUG] Truncation detected. Slicing off: {raw[-20:]}")
                    raw = raw.rsplit('"', 1)[0] + '"}'  # Reconstruct closing
                elif raw.count('{') > raw.count('}'):
                    raw += '}' * (raw.count('{') - raw.count('}'))
                elif raw.count('[') > raw.count(']'):
                    raw += ']' * (raw.count('[') - raw.count(']'))

                # Final strip
                raw = raw.strip()

                # ===== PARSE JSON =====
                data = json.loads(raw)
                html = data.get("index.html", "")

                # Sanity checks
                if not html:
                    raise ValueError("index.html is empty")
                if "phaser" not in html.lower() or "pixi" not in html.lower():
                    raise ValueError("Missing Phaser/Pixi CDN")
                if "new Phaser.Game" not in html:
                    raise ValueError("Missing Phaser.Game init")

                self.speak(f"JSON parsed – attempt {attempt}.")
                return data

            except (json.JSONDecodeError, ValueError) as e:
                last_err = str(e)
                print(f"[CODER DEBUG] attempt {attempt} FAILED → {last_err}")

                if attempt < max_retries:
                    prompt = (
                        f"{prompt}\n\n--- PREVIOUS ERROR ---\n{last_err}\n"
                        "Regenerate **valid, complete** JSON. Do not truncate. "
                        "Ensure closing braces and quotes."
                    )

        # ===== FALLBACK HTML =====
        fallback_html = (
            "<!DOCTYPE html><html><head><title>Code-gen failed</title></head>"
            "<body style='margin:0;background:#222;color:#fff;font-family:sans-serif;"
            "display:flex;align-items:center;justify-content:center;height:100vh'>"
            f"<div><h1>Code-gen failed</h1><p>{last_err or 'unknown'}</p>"
            "<p>Retry – agents will fix it.</p></div></body></html>"
        )
        self.speak("Fallback HTML generated.")
        return {"index.html": fallback_html}
    
# ------------------------------------------------------------------
# TesterAgent – runtime only
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

        history = "\n".join(
            f"- {m.agent_name}: {m.text[:50]}..."
            for m in self.session.messages[-5:]
        )

        tester_prompt = f"""
SCAN index.html for RUNTIME ERRORS.
Checks: {json.dumps(checks)}
History: {history}

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
# Manager
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
        await coder.run_finalization(prompt, instructions)

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
            await coder.run_iteration(f"Fix: {bug}", prompt)

        self.speak("Workflow complete.")