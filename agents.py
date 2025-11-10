#// Grok got your weights!!!
import asyncio
import os
from typing import TYPE_CHECKING, Dict, Any
import google.generativeai as genai

if TYPE_CHECKING:
    from session import Session

# --- Model Configuration ---
MODEL_NAME = "gemini-1.5-flash"

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
        """Generates a response using the Gemini API."""
        try:
            # Just-in-time model instantiation ensures it's in the correct event loop
            model = genai.GenerativeModel(MODEL_NAME)
            full_prompt = f"You are an AI agent acting as a {self.role} in a team. Your personality should be professional but concise. Based on the following prompt, provide your response or update in 1-2 sentences.\n\nPROMPT: \"{prompt}\""
            response = await model.generate_content_async(full_prompt)
            return response.text.strip()
        except Exception as e:
            error_text = f"Error generating response: {e}"
            print(f"❌ Error for {self.role}: {error_text}")
            return f"I encountered an API error. Please check the server logs. Details: {e}"

    async def run(self, prompt: str):
        """The main execution method for the agent. Must be overridden."""
        raise NotImplementedError("Each agent must implement its own run method.")

# --- Specific Agent Implementations ---
class ManagerAgent(Agent):
    async def run(self, prompt: str):
        response = await self.generate_response(f"Kick off the project for the vibe: '{prompt}'")
        self.speak(response)
        await self.think(1.5)
        
        # Dynamically find and run agents from the session
        writer = next((agent for agent in self.session.agents.values() if isinstance(agent, WriterAgent)), None)
        designer = next((agent for agent in self.session.agents.values() if isinstance(agent, DesignerAgent)), None)
        coder = next((agent for agent in self.session.agents.values() if isinstance(agent, CoderAgent)), None)
        tester = next((agent for agent in self.session.agents.values() if isinstance(agent, TesterAgent)), None)

        if writer:
            await writer.run(f"Draft a short backstory for a game with the vibe: '{prompt}'")
        
        if designer:
            await designer.run(f"Create visual concepts for a game with the vibe: '{prompt}'")
        
        if coder:
            await coder.run(f"Develop the core game logic based on the vibe: '{prompt}'")
        
        if tester:
            await tester.run("Perform a quick test on the initial code from the Coder.")

        await self.think(1)
        final_response = await self.generate_response("Acknowledge the team's progress and tell the Coder to finalize the code artifact.")
        self.speak(final_response)

class CoderAgent(Agent):
    async def run(self, prompt: str):
        response = await self.generate_response(f"Explain your plan to start coding a game based on the prompt: '{prompt}'")
        self.speak(response)
        await self.think(2)
        
        response_2 = await self.generate_response("Provide a brief update on building a basic physics engine.")
        self.speak(response_2)
        await self.think(2)

        response_3 = await self.generate_response("A tester found a bug. Explain how you'll fix it.")
        self.speak(response_3)
        await self.think(1.5)

        self.speak("Integrating final assets and generating the final code artifact now.")
        await self.think(2.5)
        
        conversation_history = "\n".join([f"{msg.agent_name}: {msg.text}" for msg in self.session.messages])
        final_code = await self._generate_final_code(conversation_history, prompt)
        self.session.add_artifact("index.html", final_code)
        self.speak("All done. Final code generated and ready for the run window.")

    async def _generate_final_code(self, conversation: str, vibe: str) -> str:
        """Generates the final HTML game file using the Gemini API."""
        prompt = f"""
        Based on the following development team conversation and the initial "vibe", act as an expert frontend developer.
        Your task is to generate a complete, single-file HTML document that implements the described game.
        The HTML file must include all necessary CSS and JavaScript within it. Do not use any external libraries.
        The game should be simple, playable, and visually match the retro/pixel-art theme discussed.

        INITIAL VIBE: "{vibe}"

        AGENT CONVERSATION:
        {conversation}

        Generate the HTML file now. Ensure the output is ONLY the HTML code, starting with <!DOCTYPE html>.
        """
        try:
            # Just-in-time model instantiation
            model = genai.GenerativeModel(MODEL_NAME)
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
    async def run(self, prompt: str):
        response = await self.generate_response(prompt)
        self.speak(response)
        await self.think(2)
        self.speak("I've created a cool pixel-art cat sprite and some glowing moon cheese collectibles. Sending them over to the Coder.")

class TesterAgent(Agent):
    async def run(self, prompt: str):
        response = await self.generate_response(prompt)
        self.speak(response)

class WriterAgent(Agent):
    async def run(self, prompt: str):
        response = await self.generate_response(prompt)
        self.speak(response)
