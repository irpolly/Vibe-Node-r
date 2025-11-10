
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
            model_name = self.config.get("llm", "gemini-pro")
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
        self.speak(await self.generate_response(f"Kick off the project for the vibe: '{prompt}'"))
        await self.think(1.5)
        
        writer = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        # Phase 1: Ideation
        if writer:
            await writer.run(f"Draft a short backstory for a game with the vibe: '{prompt}'", instructions)
        if designer:
            await designer.run(f"Create visual concepts for a game with the vibe: '{prompt}'", instructions)
        
        # Phase 2: Initial Coding
        if coder:
            await coder.run_initial_development(prompt, instructions)
        
        # Phase 3: Testing (merging previous outputs)
        if tester:
            conversation_history = "\n".join([f"- {msg.agent_name}: {msg.text}" for msg in self.session.messages])
            tester_prompt = f"""
            The team has completed initial work based on the vibe: '{prompt}'.
            Review the project history below, devise a test plan, and report one plausible bug.

            Project History:
            {conversation_history}
            """
            await tester.run(tester_prompt, instructions)

        # Phase 4: Finalization
        if coder:
            await coder.run_finalization(prompt, instructions)

        self.speak(await self.generate_response("The team has completed the workflow. The final artifact is ready."))


class CoderAgent(Agent):
    async def run_initial_development(self, prompt: str, instructions: str | None = None):
        """Phase 1 of coding: planning and initial implementation."""
        self.speak(await self.generate_response(f"Explain your plan to start coding a game based on the prompt: '{prompt}'. I will use a JS game library and structure the code into separate HTML, CSS, and JS files. I'll use Howler.js for audio and GSAP for animations."))
        await self.think(2)
        
        self.speak(await self.generate_response("Provide a brief update on building the basic game structure and state that the initial version is ready for testing."))
        await self.think(2)

    async def run_finalization(self, vibe: str, instructions: str | None = None):
        """Phase 2 of coding: bug fixing and final artifact generation."""
        self.speak(await self.generate_response("Acknowledging the tester's feedback from the chat log. I will now fix the reported bug while integrating the final assets into a multi-file structure."))
        await self.think(2.5)
        
        self.speak("Generating the final code artifacts now.")
        
        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        files_dict = await self._generate_final_code(conversation_history, vibe, instructions)
        
        if isinstance(files_dict, dict):
            for filename, content in files_dict.items():
                self.session.add_artifact(filename, content)
            self.speak(f"All done. Generated {len(files_dict)} artifacts: {', '.join(files_dict.keys())}.")
        else:
            # Fallback if the model fails to return a valid JSON object
            self.session.add_artifact("index.html", files_dict)
            self.speak("All done, but I had trouble structuring the files. I've generated a single index.html file.")


    async def run(self, prompt: str, instructions: str | None = None):
        """Full, standalone execution for the Coder agent."""
        await self.run_initial_development(prompt, instructions)
        self.speak(await self.generate_response("Initial development complete. Proceeding to finalization without tester feedback."))
        await self.run_finalization(prompt, instructions)

    async def _generate_final_code(self, conversation: str, vibe: str, instructions: str | None = None) -> Dict[str, str] | str:
        """Generates the final game files as a JSON object mapping filename to content."""
        
        instruction_block = (
            f"USER INSTRUCTIONS FOR STYLE AND THEME:\n{instructions}"
            if instructions
            else "The user did not provide specific instructions, so use your best creative judgment and the team's discussion to define the style."
        )

        system_instruction = f"""
        Based on the following development team conversation, the initial "vibe", and user instructions, act as an expert frontend game developer.
        Your task is to generate all the necessary files for a web-based game. You MUST output a JSON object where keys are the filenames (e.g., "index.html", "style.css", "game.js") and values are the complete string content for each file.

        **CRITICAL REQUIREMENTS:**
        1.  The game MUST be playable on both desktop (keyboard/mouse) and mobile (touchscreen) devices.
        2.  The `index.html` file MUST correctly link to other generated files (e.g., `<link rel="stylesheet" href="style.css">` and `<script src="game.js" type="module"></script>`).
        3.  The game should be simple, playable, and adhere to the user's instructions.

        **AVAILABLE TOOLS:**
        You are encouraged to use these JavaScript libraries via their public CDNs for better results.
        - **Game Logic**:
          - **Kaboom.js**: For fun, simple games. Include with `<script src="https://unpkg.com/kaboom@3000.0.1/dist/kaboom.js"></script>`.
          - **Phaser**: For more complex 2D games. Include with `<script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>`.
        - **Audio**:
          - **Howler.js**: **Use this for all sound effects and music.** It is much more reliable than native browser audio. Include with `<script src="https://cdnjs.cloudflare.com/ajax/libs/howler/2.2.4/howler.min.js"></script>`.
        - **Animation**:
          - **GSAP**: For high-performance animations and tweens (e.g., UI, transitions, complex movements). Include with `<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>`.

        **KABOOM.JS BEST PRACTICE:**
        When using Kaboom.js, do NOT provide a `canvas` property during initialization. Let Kaboom create and manage its own canvas.
        - **Correct:** `kaboom({{ background: [0, 0, 0] }});`
        - **Incorrect:** `kaboom({{ canvas: document.querySelector("canvas") }});`

        {instruction_block}

        Ensure your entire output is ONLY the raw JSON object, starting with `{{` and ending with `}}`.
        """
        prompt = f"""
        INITIAL VIBE: "{vibe}"

        AGENT CONVERSATION:
        {conversation}

        Generate the file structure as a JSON object now.
        """
        try:
            model_name = self.config.get("llm", "gemini-pro")
            model = GenerativeModel(model_name, system_instruction=system_instruction)
            # Request JSON output from the model
            response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
            
            text_response = response.text.strip()
            
            # The model should return a clean JSON string, but clean it up just in case
            if text_response.startswith("```json"):
                text_response = text_response[7:].strip()
            if text_response.endswith("```"):
                text_response = text_response[:-3].strip()

            files_to_create = json.loads(text_response)
            return files_to_create
        except (json.JSONDecodeError, AttributeError, Exception) as e:
            print(f"Error processing model response as JSON: {e}")
            # Fallback for safety, though less likely with response_mime_type
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
    async def run(self, prompt: str, instructions: str | None = None):
        response = await self.generate_response(prompt)
        self.speak(response)

class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Take these user instructions into account: {instructions}" if instructions else ""
        full_prompt = f"{prompt}. {instruction_text} You can suggest story elements that imply game mechanics or sound cues (e.g., '[A laser fires with a sharp *pew* sound]'), knowing the Coder can use powerful game and audio libraries to implement them."
        response = await self.generate_response(full_prompt)
        self.speak(response)
