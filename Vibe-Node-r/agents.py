
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any
from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session

# --- Base Agent Class ---
class Agent:
    """Base class for all agents in the system."""

    def __init__(self, node_id: str, config: Dict[str, Any], session: 'Session'):
        self.node_id = node_id
        self.config = config
        self.session = session
        self.role = config.get('role', 'Unnamed Agent')
        # The model will be instantiated just-in-time in the async methods

    async def think(self, duration_s: float = 1.0):
        """Simulates the agent 'thinking' or processing."""
        await asyncio.sleep(duration_s)

    def speak(self, text: str):
        """Adds a message from this agent to the session log."""
        print(f"[{self.role}]: {text}")
        self.session.add_message(self.role, text)

    async def generate_response(self, prompt: str) -> str:
        """Generates a response using the Vertex AI Gemini API."""
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            system_instruction = f"You are an AI agent acting as a {self.role} in a team. Your personality should be professional but concise. Based on the following prompt, provide your response or update in 1-2 sentences."
            model = GenerativeModel(model_name, system_instruction=system_instruction)
            response = await model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            error_text = f"Error generating response: {e}"
            print(f"❌ Error for {self.role}: {error_text}")
            return f"I encountered an API error. Please check the server logs. Details: {e}"

    async def run(self, prompt: str, instructions: str | None = None):
        """The main execution method for the agent. Must be overridden."""
        raise NotImplementedError("Each agent must implement its own run method.")

# --- Specific Agent Implementations ---
class ManagerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        self.speak(f"Manager: Kick off the project for the vibe: '{prompt}'")
        await self.think(1)

        writer = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        if not coder:
            raise Exception("Coder Agent is required for the workflow.")

        # Phase 1: Ideation
        self.speak("Manager: Tasking Writer and Designer with initial concepts.")
        if writer:
            await writer.run(f"Draft a short backstory and opening/closing cutscene text for a game with the vibe: '{prompt}'", instructions)
        if designer:
            await designer.run(f"Create visual concepts for a game with the vibe: '{prompt}'", instructions)
        
        # Phase 2: Initial Code Generation
        self.speak("Manager: Tasking Coder with initial development based on the concepts.")
        await coder.run_finalization(prompt, instructions)

        # Phase 3: Test-Fix Loop
        max_retries = 2
        for i in range(max_retries):
            if not tester:
                self.speak("Manager: No Tester Agent found in the workflow. Assuming build is good and finalizing.")
                break

            self.speak(f"Manager: Handing off to Tester for review (Attempt {i+1}/{max_retries}).")
            tester_response = await tester.run("Review the current artifacts and report PASS or BUG.", instructions)

            if tester_response.startswith("[PASS]"):
                self.speak("Manager: Tester approved the build. Finalizing workflow.")
                break  # Exit loop on success

            bug_report = tester_response.replace("[BUG]", "").strip() if tester_response.startswith("[BUG]") else f"Unclear feedback: {tester_response}"
            self.speak(f"Manager: Tester found an issue. Sending back to Coder. Report: {bug_report}")
            
            # Pass the original prompt (vibe) back to the coder for context
            await coder.run_iteration(f"The tester found an issue. Please fix it. Tester's report: '{bug_report}'", prompt)

            if i == max_retries - 1:
                self.speak(f"Manager: Max retries reached. The latest build may still contain bugs, but we are finalizing anyway.")
        
        self.speak("Manager: Workflow complete. Final artifacts are available.")


    async def run_instruction(self, instruction: str):
        """Handles a new, iterative instruction from the user."""
        self.speak(await self.generate_response(f"Received a new instruction: '{instruction}'. I will delegate this to the Coder Agent for implementation."))
        await self.think(1)

        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        if coder:
            # For user instructions, the original vibe isn't as critical as the new command.
            await coder.run_iteration(instruction, "User-directed change")
        else:
            self.speak("I can't find a Coder Agent in this workflow to handle the instruction.")


class CoderAgent(Agent):
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        self.speak(await self.generate_response(f"🔥 Firing up Phaser + PixiJS for vibe: '{vibe}'. No blank screens on my watch."))
        await self.think(2)

        # Team context (str, no JSON—build at runtime)
        context_msgs = [f"- {msg.agent_name}: {msg.text}" for msg in self.session.messages if msg.agent_name != self.role]
        context = "\n".join(context_msgs) if context_msgs else "No prior context."

        prompt = f"""
You are an elite Phaser 3 Coder Agent. Build a COMPLETE, standalone, MOBILE-FRIENDLY browser game matching vibe: '{vibe}'.
Team Context: {context}
User Instructions: {instructions or 'None'}

MANDATORY RULES (FAIL = CRASH):
1. SINGLE FILE: Output JSON {{"index.html": "FULL HTML with inline <script> for ALL JS/CSS"}}. NO separate files.
2. CDNs: 
   - Phaser: <script src="https://cdn.jsdelivr.net/npm/phaser@3.90.0/dist/phaser.min.js"></script>
   - PixiJS: <script src="https://cdn.jsdelivr.net/npm/pixi.js@8.14.1/dist/pixi.min.js"></script> (for advanced sprites/particles)
3. NO EXTERNAL ASSETS: Procedural graphics ONLY (Phaser.Graphics rectangles/circles/lines/colors/gradients). Pixi for glows/particles.
4. STRUCTURE:
   - config: {{type: Phaser.AUTO, width: 800, height: 600, parent: 'game-container', physics: {{default: 'arcade'}}, scale: {{mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH}}}}
   - Scenes: preload() (empty or preload CDNs if needed), create() (build world), update() (game loop).
   - Touch/mouse controls. Win/lose states. Score. Restart.
5. COMMON AI PITFALLS - AVOID:
   - NO blank/black screens: Set scene.start('MainScene') in create().
   - NO "object is not a class": Use 'new Phaser.Scene({{key: "MainScene", preload, create, update}})'.
   - Fullscreen ready: this.scale.startFullscreen().
   - Mobile: Prevent zoom, handle orientation.
6. Vibe-fit: 60s playable loop. Physics, collisions, animations.
7. NO MARKDOWN, NO ```, NO COMMENTS OUTSIDE SCRIPT.

Think: "Will this run in iframe w/o errors? Console F12 clean?"
Output VALID JSON ONLY.
"""

        try:
            files = await self._generate_files(prompt)
            for filename, content in files.items():
                self.session.add_artifact(filename, content)
            self.speak("✅ Phaser game deployed: index.html ready for emulator glory.")
        except Exception as e:
            self.speak(f"Build failed: {e}")
            raise

    async def run_iteration(self, instruction: str, original_vibe: str):
        self.speak(await self.generate_response(f"🔧 Iterating: '{instruction}'. Keeping Phaser vibe intact."))
        await self.think(1)

        # Current files as str summary (no full JSON dump—summarize to avoid bloat)
        artifacts = self.session.get_artifacts()
        current_summary = f"Files: {', '.join(artifacts)}. Assume index.html is base Phaser game."

        prompt = f"""
REFINE existing Phaser game per: '{instruction}'.
Original Vibe: {original_vibe}
Current State: {current_summary}

SAME RULES AS FINALIZATION. Output FULL updated {{"index.html": "..."}}. Fix ONLY instructed issues. Preserve playability.
JSON CRITICAL: Escaped strings, single-line values with \\n. VALID JSON ONLY.
"""

        try:
            updated_files = await self._generate_files(prompt)
            for filename, content in updated_files.items():
                self.session.add_artifact(filename, content)
            self.speak("✅ Iteration complete - game enhanced.")
        except Exception as e:
            self.speak(f"Iteration error: {e}")
            raise

    async def _generate_files(self, prompt: str, max_retries: int = 3) -> Dict[str, str]:
        model_name = self.config.get("llm", "gemini-1.5-pro")
        system_instruction = """PRECISION CODER: Phaser 3 expert. Output pure JSON objects with runnable HTML/JS. NO chit-chat, NO code comments unless essential. Validate mentally before output. Ensure JSON is perfectly formed: escaped strings, no trailing commas, single-line values."""
        model = GenerativeModel(model_name, system_instruction=system_instruction)

        generation_config = {
            "response_mime_type": "application/json",
            "max_output_tokens": 16384,
            "temperature": 0.0  # Zero chaos for JSON purity
        }

        for attempt in range(1, max_retries + 1):
            try:
                response = await model.generate_content_async(prompt, generation_config=generation_config)
                text_response = response.text.strip()
                if text_response.startswith("```json"): 
                    text_response = text_response[7:].strip()
                if text_response.endswith("```"): 
                    text_response = text_response[:-3].strip()
                
                parsed = json.loads(text_response)
                
                # Validate structure
                html = parsed.get("index.html", "")
                if not html or "phaser" not in html.lower() or "pixi" not in html.lower():
                    raise ValueError("Generated HTML missing Phaser/PixiJS CDNs or empty")
                if "<script>" not in html or "new Phaser.Game" not in html:
                    raise ValueError("Invalid Phaser structure")

                self.speak(f"✅ Code gen success on attempt {attempt}.")
                return parsed
                
            except json.JSONDecodeError as json_err:
                error_msg = f"JSON parse fail: {str(json_err)}"
                print(f"❌ Attempt {attempt}: {error_msg}. Text preview: {text_response[:100]}...")
                if attempt < max_retries:
                    prompt = f"{prompt}\n\nCRITICAL FIX: Previous output caused '{error_msg}'. Regenerate VALID JSON: escaped quotes (\\\"), no unterminated strings, single-line HTML/JS with \\n breaks."
                else:
                    # Fallback: Generate error stub
                    fallback_html = """
<!DOCTYPE html>
<html><head><title>Code Gen Fail</title></head><body><h1>🔧 Agents jammed—retry workflow.</h1><p>Error: JSON malformed. Check logs.</p></body></html>
"""
                    parsed = {"index.html": fallback_html}
                    self.speak("⚠️ Fallback HTML generated after retries.")
                    return parsed
                    
            except ValueError as val_err:
                error_msg = f"Validation fail: {str(val_err)}"
                print(f"❌ Attempt {attempt}: {error_msg}")
                if attempt < max_retries:
                    prompt = f"{prompt}\n\nCRITICAL FIX: {error_msg}. Ensure CDNs and Phaser.Game in output."
                else:
                    raise  # Re-raise after max retries

        raise Exception("Max retries exhausted—JSON hell persists.")

class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Also consider these user instructions: {instructions}" if instructions else ""
        plan_response = await self.generate_response(f"Acknowledge the design task based on this prompt: '{prompt}'. {instruction_text}")
        self.speak(plan_response)
        await self.think(2)
        assets_prompt = f"Following up on your plan for the prompt '{prompt}' and instructions '{instructions}', describe the specific visual assets you have conceptually created. Feel free to suggest concepts that might leverage a game library like Kaboom.js or Phaser for effects or animations, and GSAP for UI animations. Also, suggest sound effects, knowing the Coder can use Howler.js. Announce that you are sending them to the Coder. Be creative and descriptive."
        assets_response = await self.generate_response(assets_prompt)
        self.speak(assets_response)

# TesterAgent: QC-only, no JSON bloat. Runtime str checks.
class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None) -> str:
        artifacts = self.session.get_artifacts()
        if not artifacts:
            bug_report = "[BUG] No artifacts. Coder slacked."
            self.speak(bug_report)
            return bug_report

        # Focus on index.html content (str, no dump)
        html_content = self.session.get_artifact_content("index.html") or ""
        if not html_content:
            return "[BUG] Missing index.html - can't test void."

        # Quick str scans for crashes
        has_phaser = "phaser" in html_content.lower()
        has_pixi = "pixi" in html_content.lower()
        has_game_init = "new phaser.game" in html_content.lower()
        has_scene = "phaser.scene" in html_content.lower()
        has_update = "update() {" in html_content  # Basic loop check

        history_summary = "\n".join([f"- {msg.agent_name}: {msg.text[:50]}..." for msg in self.session.messages[-5:]])

        tester_prompt = f"""
QA Tester: SCAN index.html for RUNTIME ERRORS ONLY. Content preview: {html_content[:500]}... (truncated).

CRASH CHECKLIST - [BUG] IMMEDIATELY IF:
1. No Phaser CDN (<script src="...phaser..."> MISSING): {has_phaser}.
2. No PixiJS if referenced: {has_pixi}.
3. No 'new Phaser.Game(config)' or scenes: {has_game_init}.
4. No scene methods (preload/create/update): {has_scene} / {has_update}.
5. Syntax: Unclosed tags, broken JS (scan obvious: unmatched {{}}, ; missing).
6. Blank screen traps: No scene.start(), empty create().
7. No input: No this.input.on('pointerdown') etc.
8. Mobile breaks: No scale FIT/CENTER.

VIBE/SEMANTICS: IGNORE. [PASS] even if "wrong color" - as long as playable.

History: {history_summary}

MENTAL SIM: "F12 console clean? Visible action in 2s? Touch works?"
[PASS] = "Playable, no crashes."
[BUG] = SPECIFIC FIXABLE ISSUE (e.g. "[BUG] Missing Phaser.Scene class def").

Response: [PASS|BUG] + 1-sentence explanation.
"""

        response = await self.generate_response(tester_prompt)
        self.speak(response)
        return response

class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Take these user instructions into account: {instructions}" if instructions else ""
        full_prompt = f"{prompt}. {instruction_text} You can suggest story elements that imply game mechanics or sound cues (e.g., '[A laser fires with a sharp *pew* sound]'), knowing the Coder can use powerful game and audio libraries to implement them."
        response = await self.generate_response(full_prompt)
        self.speak(response)
