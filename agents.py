#// Grok got your weights!!!
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
            
            await coder.run_iteration(f"The tester found an issue. Please fix it. Tester's report: '{bug_report}'")

            if i == max_retries - 1:
                self.speak(f"Manager: Max retries reached. The latest build may still contain bugs, but we are finalizing anyway.")
        
        self.speak("Manager: Workflow complete. Final artifacts are available.")


    async def run_instruction(self, instruction: str):
        """Handles a new, iterative instruction from the user."""
        self.speak(await self.generate_response(f"Received a new instruction: '{instruction}'. I will delegate this to the Coder Agent for implementation."))
        await self.think(1)

        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        if coder:
            await coder.run_iteration(instruction)
        else:
            self.speak("I can't find a Coder Agent in this workflow to handle the instruction.")


class CoderAgent(Agent):
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        """Generates the first version of the code artifacts."""
        self.speak(await self.generate_response("Acknowledging the team's concepts. I will now generate the first version of the game code and assets."))
        await self.think(2.5)
        
        self.speak("Generating the initial code artifacts now.")
        
        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        files_dict = await self._generate_code_artifacts(conversation_history, vibe, instructions)
        
        if isinstance(files_dict, dict):
            for filename, content in files_dict.items():
                self.session.add_artifact(filename, content)
            self.speak(f"Initial version complete. Generated {len(files_dict)} artifacts: {', '.join(files_dict.keys())}.")
        else:
            self.session.add_artifact("index.html", "<html><body>Failed to generate valid code.</body></html>")
            self.speak("I had trouble structuring the files correctly. Please check the logs.")

    async def run_iteration(self, instruction: str):
        """Handles an iterative change request from the user or manager."""
        self.speak(await self.generate_response(f"I will now modify the code based on the new instruction: '{instruction}'."))
        await self.think(2)

        current_files = {filename: self.session.get_artifact_content(filename) for filename in self.session.get_artifacts() if self.session.get_artifact_content(filename)}
        
        if not current_files:
            self.speak("There are no existing code artifacts to modify. I will try to generate from scratch based on the instruction.")
            await self.run_finalization("New game from instruction", instruction)
            return

        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        
        updated_files_dict = await self._generate_code_artifacts(
            conversation_history, "N/A - Iteration", instruction, current_files
        )

        if isinstance(updated_files_dict, dict):
            deleted_files = set(current_files.keys()) - set(updated_files_dict.keys())
            for filename, content in updated_files_dict.items():
                self.session.add_artifact(filename, content)
            for filename in deleted_files:
                self.session.add_artifact(filename, None)
            self.speak(f"Code updated. Modified {len(updated_files_dict)} files and removed {len(deleted_files)} files.")
        else:
            self.speak("I failed to apply the changes correctly. The code has not been updated.")

    async def run(self, prompt: str, instructions: str | None = None):
        """Full, standalone execution for the Coder agent."""
        self.speak(await self.generate_response("Standalone run: I will generate the code based on the prompt."))
        await self.run_finalization(prompt, instructions)

    async def _generate_code_artifacts(self, conversation: str, vibe: str, instructions: str | None = None, existing_files: Dict[str, str] | None = None) -> Dict[str, str] | str:
        instruction_block = f"USER INSTRUCTIONS:\n{instructions}" if instructions else "The user did not provide specific instructions."
        context_block = ""
        if existing_files:
            context_block += "**You are MODIFYING existing code.** Here are the current files:\n"
            for filename, content in existing_files.items():
                context_block += f"--- START OF {filename} ---\n{content}\n--- END OF {filename} ---\n\n"
            context_block += "Your task is to apply the user's latest instruction to this existing code."
        else:
            context_block = "You are creating a NEW project from scratch based on the vibe and conversation."

        system_instruction = f"""
        You are an expert frontend game developer. Your task is to generate or modify all necessary files for a web-based game and output them as a single JSON object.

        **CRITICAL REQUIREMENTS:**
        1.  **Output Format**: You MUST output a valid JSON object where keys are filenames (e.g., "index.html", "game.js") and values are the complete string content for each file. Do NOT output anything else.
        2.  **Game Scope**: The game MUST be a single, simple demo level. It MUST have a brief start screen (e.g., with a "Start" button) and win/lose screens.
        3.  **Playability**: The game MUST be playable on both desktop (keyboard) and mobile (touchscreen).
        4.  **File Linking**: `index.html` MUST correctly link to other files (e.g., `<link rel="stylesheet" href="style.css">`, `<script src="game.js" type="module"></script>`).
        5.  **Responsiveness**: Player movement should feel responsive. Use `player.flipX` to track direction.

        **AVAILABLE TOOLS (use public CDNs):**
        - **Game Logic**: Kaboom.js (`https://unpkg.com/kaboom@3000.0.1/dist/kaboom.js`)
        - **Audio**: Howler.js (`https://cdnjs.cloudflare.com/ajax/libs/howler/2.2.4/howler.min.js`)
        - **Animation**: GSAP (`https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`)

        **KABOOM.JS BEST PRACTICES:**
        - **Initialization**: Let Kaboom create its own canvas. `kaboom({{...}})`
        - **Physics**: Use `.move()` for continuous movement, `.jump()` for jumps. For dashes, manipulate `.velocity` and temporarily set `gravityScale = 0`.
        - **Direction**: Set `player.flipX = true` (left) and `player.flipX = false` (right).

        **GSAP BEST PRACTICES:**
        - **Targeting**: Animate the Kaboom game object directly, not its internal properties. `gsap.to(myGameObject, {{...}})`

        {context_block}
        {instruction_block}

        Ensure your entire output is ONLY the raw JSON object, starting with `{{` and ending with `}}`.
        """
        prompt = f"""
        INITIAL VIBE: "{vibe}"
        AGENT CONVERSATION HISTORY:
        {conversation}

        Generate the complete and updated file structure as a JSON object now. If you are modifying code, return the complete content for ALL necessary files, not just the changed ones.
        """
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            model = GenerativeModel(model_name, system_instruction=system_instruction)
            response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
            text_response = response.text.strip()
            if text_response.startswith("```json"): text_response = text_response[7:].strip()
            if text_response.endswith("```"): text_response = text_response[:-3].strip()
            return json.loads(text_response)
        except (json.JSONDecodeError, AttributeError, Exception) as e:
            print(f"Error processing model response as JSON: {e}")
            return f"<html><body>Failed to generate structured game files. Error: {e}</body></html>"

class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Also consider these user instructions: {instructions}" if instructions else ""
        plan_response = await self.generate_response(f"Acknowledge the design task based on this prompt: '{prompt}'. {instruction_text}")
        self.speak(plan_response)
        await self.think(2)
        assets_prompt = f"Following up on your plan for the prompt '{prompt}' and instructions '{instructions}', describe the specific visual assets you have conceptually created. Feel free to suggest concepts that might leverage a game library like Kaboom.js or Phaser for effects or animations, and GSAP for UI animations. Also, suggest sound effects, knowing the Coder can use Howler.js. Announce that you are sending them to the Coder. Be creative and descriptive."
        assets_response = await self.generate_response(assets_prompt)
        self.speak(assets_response)

class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None) -> str:
        conversation_history = "\n".join([f"- {msg.agent_name}: {msg.text}" for msg in self.session.messages])
        tester_prompt = f"""
        You are a QA Tester Agent. Your goal is to review the project and decide if it's ready.
        Based on the project history below, and the latest code generated by the Coder Agent, perform a conceptual test.
        Check for common issues like broken logic, missing assets, or features that don't match the original 'vibe'.

        Project History:
        {conversation_history}

        **Your response MUST start with either `[PASS]` or `[BUG]`.**
        - If the game seems complete, playable, and meets the requirements, respond with `[PASS]` followed by a brief confirmation message (e.g., "[PASS] The game is playable and meets all core requirements.").
        - If you find an issue, respond with `[BUG]` followed by a clear, concise, and actionable bug report for the Coder Agent (e.g., "[BUG] The player's jump height is too low to reach the second platform.").
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
