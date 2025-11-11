
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
        """Generates the first version of the code artifacts."""
        self.speak(await self.generate_response("Acknowledging the team's concepts. I will now generate the first version of the game code and assets."))
        await self.think(2.5)
        
        self.speak("Generating the initial code artifacts now.")
        
        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        files_dict = await self._generate_code_artifacts(conversation_history, vibe, instructions)
        
        if isinstance(files_dict, dict) and 'error.html' not in files_dict:
            for filename, content in files_dict.items():
                self.session.add_artifact(filename, content)
            self.speak(f"Initial version complete. Generated {len(files_dict)} artifacts: {', '.join(files_dict.keys())}.")
        else:
            self.speak("I had trouble structuring the files correctly. Please check the logs.")
            if isinstance(files_dict, dict):
                 for filename, content in files_dict.items():
                    self.session.add_artifact(filename, content)
            else:
                 self.session.add_artifact("error.html", "<html><body>Failed to generate valid code.</body></html>")


    async def run_iteration(self, instruction: str, vibe: str):
        """Handles an iterative change request from the user or manager."""
        self.speak(await self.generate_response(f"I will now process the new instruction: '{instruction}'."))
        await self.think(2)

        current_files = {filename: self.session.get_artifact_content(filename) for filename in self.session.get_artifacts() if self.session.get_artifact_content(filename)}
        
        # Filter out any previous error files to avoid confusing the model.
        valid_files = {k: v for k, v in current_files.items() if not k.endswith('error.html')}

        files_to_pass_to_model = valid_files if valid_files else None

        if not files_to_pass_to_model:
            self.speak("The previous build failed or is empty. I will generate the code from scratch using the original vibe and recent feedback.")
        else:
            self.speak("I will now modify the existing code based on the new instruction.")

        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        
        # The `instruction` (which could be a bug report or user feedback) is passed as the primary instruction to the model.
        # `files_to_pass_to_model` will be None if generating from scratch, which is what _generate_code_artifacts expects.
        updated_files_dict = await self._generate_code_artifacts(
            conversation_history, vibe, instruction, files_to_pass_to_model
        )

        if isinstance(updated_files_dict, dict) and 'error.html' not in updated_files_dict:
            deleted_files = set(valid_files.keys()) - set(updated_files_dict.keys())
            for filename, content in updated_files_dict.items():
                self.session.add_artifact(filename, content)
            for filename in deleted_files:
                self.session.add_artifact(filename, None) # This removes the file.
            
            # Also remove the error.html if it exists
            if 'error.html' in current_files:
                self.session.add_artifact('error.html', None)

            self.speak(f"Code updated. Modified/created {len(updated_files_dict)} files and removed {len(deleted_files)} files.")
        else:
            # The generation failed again.
            self.speak("I failed to apply the changes correctly. The code has not been updated.")
            if isinstance(updated_files_dict, dict):
                for filename, content in updated_files_dict.items():
                    self.session.add_artifact(filename, content)

    async def run(self, prompt: str, instructions: str | None = None):
        """Full, standalone execution for the Coder agent."""
        self.speak(await self.generate_response("Standalone run: I will generate the code based on the prompt."))
        await self.run_finalization(prompt, instructions)

    async def _generate_code_artifacts(self, conversation: str, vibe: str, instructions: str | None = None, existing_files: Dict[str, str] | None = None) -> Dict[str, str] | str:
        instruction_block = f"USER INSTRUCTIONS:\n{instructions}" if instructions else "The user did not provide specific instructions."
        context_block = ""
        if existing_files:
            context_block += "**CONTEXT: You are MODIFYING existing code.** Based on the user's latest instruction, you must update the following files. Return the complete, updated content for ALL files in the project, not just the ones you changed.\n"
            for filename, content in existing_files.items():
                context_block += f"--- START OF {filename} ---\n{content}\n--- END OF {filename} ---\n\n"
        else:
            context_block = "**CONTEXT: You are creating a NEW project from scratch.**"

        system_instruction = f"""
You are an expert frontend game developer. Your mission is to generate all necessary files for a complete, playable, single-file web-based game and output them as a single JSON object.

**CREATIVITY & FLEXIBILITY:**
The user's 'vibe' may be vague. Use your creative judgment to fill in the gaps. It is better to deliver a complete, simple, and functional game that captures the spirit of the vibe than to fail because a detail was unclear. Make opinionated choices to ensure a working final product.

**CRITICAL REQUIREMENTS:**
1.  **Output Format**: Your entire response MUST be a single, valid JSON object. The keys must be filenames (e.g., "index.html", "style.css", "game.js"), and the values must be the complete string content for each file. Do NOT output markdown, comments, or any text outside of the JSON object.
2.  **File Structure**: You MUST generate at least three files:
    - `index.html`: The main HTML file.
    - `style.css`: For all CSS styles.
    - `game.js`: For all JavaScript game logic using Kaboom.js.
3.  **File Linking**: `index.html` MUST correctly link to the other files.
    - It MUST include the Kaboom.js library from the CDN: `<script src="https://unpkg.com/kaboom@3000.0.1/dist/kaboom.js"></script>` in the `<head>`.
    - The CSS link must be: `<link rel="stylesheet" href="style.css">`.
    - The JS link must be: `<script src="game.js" type="module"></script>`. Place this in the `<body>`.
4.  **Game Scope**: The game MUST be a simple, single demo level. It MUST have a start screen (e.g., with a "Start" button), a win condition/screen, and a lose condition/screen.
5.  **Playability**: The game MUST be playable on both desktop (keyboard controls) and mobile (touchscreen controls).

**GAME LIBRARY: KABOOM.JS (use `https://unpkg.com/kaboom@3000.0.1/dist/kaboom.js`)**
-   **Initialization**: Initialize Kaboom in `game.js`. Let it create its own canvas: `kaboom()`. Do NOT specify a canvas in the options.
-   **Scenes**: Structure your game with scenes (e.g., "start", "game", "win", "lose").
-   **Controls (CRITICAL for Playability)**:
    -   **Desktop**: Use keyboard events like `onKeyPress("space", ...)` for jumping or actions, and `onKeyDown("left", ...)` for continuous movement.
    -   **Mobile/Touch**: Use `onClick(() => {{ ... }})` or `onTouchStart(() => {{ ... }})` for actions. For movement, a good pattern is to check the touch position: `if (mousePos().x < width() / 2) {{ /* move left */ }} else {{ /* move right */ }}`.
    -   **Combine Both**: Ensure actions can be triggered by EITHER keyboard OR touch. For example, a jump could be triggered by the spacebar OR a screen tap.
-   **Movement**: Use `.move()` for continuous movement and `.jump()` for jumps. For player direction, use `player.flipX = true` for left and `player.flipX = false` for right.

{context_block}
{instruction_block}

Now, generate the complete and updated file structure as a single JSON object. Start with `{{` and end with `}}`.
"""
        prompt = f"""
        INITIAL VIBE: "{vibe}"
        AGENT CONVERSATION HISTORY:
        {conversation}

        Generate the JSON object now.
        """
        try:
            model_name = self.config.get("llm", "gemini-2.5-flash")
            model = GenerativeModel(model_name, system_instruction=system_instruction)

            # Define generation config to manage token usage for gemini-2.5-flash
            # This prevents the model from using all its tokens for "thinking" and failing on MAX_TOKENS.
            generation_config = {
                "response_mime_type": "application/json",
                "max_output_tokens": 16384,
                "thinking_config": {
                    "thinking_budget": 8192
                }
            }

            response = await model.generate_content_async(prompt, generation_config=generation_config)
            
            text_response = response.text.strip()
            if text_response.startswith("```json"): text_response = text_response[7:].strip()
            if text_response.endswith("```"): text_response = text_response[:-3].strip()
            return json.loads(text_response)
        except (json.JSONDecodeError, AttributeError, Exception) as e:
            print(f"Error processing model response as JSON: {e}")
            # Return the raw text for debugging if JSON parsing fails
            raw_response_text = "Could not parse JSON response from model."
            try:
                raw_response_text = response.text
            except (NameError, AttributeError):
                # response object might not exist or might not have a .text attribute
                pass 
            
            error_html = f"""
            <html>
                <head><title>Generation Error</title></head>
                <body style="font-family: monospace; background-color: #111; color: #f00;">
                    <h1>Agent Coder Error</h1>
                    <p>Failed to generate structured game files. The model did not return valid JSON or hit a token limit.</p>
                    <h2>Error Details:</h2>
                    <pre>{e}</pre>
                    <h2>Raw Model Response:</h2>
                    <pre>{raw_response_text}</pre>
                </body>
            </html>
            """
            return {"error.html": error_html}

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
        # Get current code state to provide context
        current_files = {filename: self.session.get_artifact_content(filename) for filename in self.session.get_artifacts() if self.session.get_artifact_content(filename)}
        
        if not current_files:
            bug_report = "[BUG] No code artifacts were found to test. The Coder Agent needs to generate the files first."
            self.speak(bug_report)
            return bug_report

        code_context_block = "**Current Code Artifacts for Review:**\n"
        for filename, content in current_files.items():
            code_context_block += f"--- START OF {filename} ---\n{content}\n--- END OF {filename} ---\n\n"

        conversation_history = "\n".join([f"- {msg.agent_name}: {msg.text}" for msg in self.session.messages])
        
        tester_prompt = f"""
        You are a QA Tester Agent. Your goal is to review the project and decide if it's ready.
        Based on the project history and the latest code provided below, perform a conceptual test.
        Check for common issues like broken logic, missing files (e.g., a missing game.js), incomplete features, or features that don't match the original 'vibe'.

        Project History:
        {conversation_history}

        {code_context_block}

        **Your response MUST start with either `[PASS]` or `[BUG]`.**
        - If the game seems complete, playable, and meets the requirements, respond with `[PASS]` followed by a brief confirmation message (e.g., "[PASS] The game is playable and meets all core requirements.").
        - If you find an issue, respond with `[BUG]` followed by a clear, concise, and actionable bug report for the Coder Agent (e.g., "[BUG] The game.js file is missing, so no game logic will run.").
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
