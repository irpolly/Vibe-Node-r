
#// Grok got your weights!!!
import asyncio
from typing import TYPE_CHECKING, Dict, Any
from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session

# --- Model Configuration ---
MODEL_NAME = "gemini-2.5-flash"

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
            # Instantiating the model from the Vertex AI SDK
            system_instruction = f"You are an AI agent acting as a {self.role} in a team. Your personality should be professional but concise. Based on the following prompt, provide your response or update in 1-2 sentences."
            model = GenerativeModel(MODEL_NAME, system_instruction=system_instruction)
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
        self.speak(await self.generate_response(f"Explain your plan to start coding a game based on the prompt: '{prompt}'"))
        await self.think(2)
        
        self.speak(await self.generate_response("Provide a brief update on building a basic physics engine and state that the initial version is ready for testing."))
        await self.think(2)

    async def run_finalization(self, vibe: str, instructions: str | None = None):
        """Phase 2 of coding: bug fixing and final artifact generation."""
        self.speak(await self.generate_response("Acknowledging the tester's feedback from the chat log. I will now fix the reported bug while integrating the final assets."))
        await self.think(2.5)
        
        self.speak("Generating the final code artifact now.")
        
        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        final_code = await self._generate_final_code(conversation_history, vibe, instructions)
        self.session.add_artifact("index.html", final_code)
        self.speak("All done. Final code generated and ready for the run window.")

    async def run(self, prompt: str, instructions: str | None = None):
        """Full, standalone execution for the Coder agent."""
        await self.run_initial_development(prompt, instructions)
        self.speak(await self.generate_response("Initial development complete. Proceeding to finalization without tester feedback."))
        await self.run_finalization(prompt, instructions)

    async def _generate_final_code(self, conversation: str, vibe: str, instructions: str | None = None) -> str:
        """Generates the final HTML game file using the Vertex AI Gemini API."""
        
        instruction_block = (
            f"USER INSTRUCTIONS FOR STYLE AND THEME:\n{instructions}"
            if instructions
            else "The user did not provide specific instructions, so use your best creative judgment and the team's discussion to define the style."
        )

        system_instruction = f"""
        Based on the following development team conversation, the initial "vibe", and user instructions, act as an expert frontend developer.
        Your task is to generate a complete, single-file HTML document that implements the described game.
        The HTML file must include all necessary CSS and JavaScript within it. Do not use any external libraries.
        The game should be simple, playable, and adhere to the user's instructions.

        {instruction_block}

        Ensure the output is ONLY the HTML code, starting with <!DOCTYPE html>.
        """
        prompt = f"""
        INITIAL VIBE: "{vibe}"

        AGENT CONVERSATION:
        {conversation}

        Generate the HTML file now.
        """
        try:
            model = GenerativeModel(MODEL_NAME, system_instruction=system_instruction)
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            if '```html' in text:
                text = text.split('```html')[1]
            if '```' in text:
                text = text.split('```')[0]
            return text.strip()
        except Exception as e:
            print(f"Error generating final code: {e}")
            return f"<html><body>Error generating game code: {e}</body></html>"

class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Also consider these user instructions: {instructions}" if instructions else ""
        plan_response = await self.generate_response(f"Acknowledge the design task based on this prompt: '{prompt}'. {instruction_text}")
        self.speak(plan_response)
        
        await self.think(2)
        
        assets_prompt = f"Following up on your plan for the prompt '{prompt}' and instructions '{instructions}', describe the specific visual assets (like sprites, color palettes, UI elements) you have conceptually created. Announce that you are sending them to the Coder. Be creative and descriptive."
        assets_response = await self.generate_response(assets_prompt)
        self.speak(assets_response)

class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        response = await self.generate_response(prompt)
        self.speak(response)

class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Take these user instructions into account: {instructions}" if instructions else ""
        full_prompt = f"{prompt}. {instruction_text}"
        response = await self.generate_response(full_prompt)
        self.speak(response)
