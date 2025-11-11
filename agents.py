# agents.py
from __future__ import annotations
import base64
from typing import Dict, Any, List
from vertexai.generative_models import GenerativeModel, GenerationConfig

# ----------------------------------------------------------------------
# Gemini model (use the latest stable flash or pro)
# ----------------------------------------------------------------------
MODEL_NAME = "gemini-1.5-flash-001"          # change to pro if you need more reasoning
model = GenerativeModel(MODEL_NAME)
gen_cfg = GenerationConfig(temperature=0.7, max_output_tokens=4096)

# ----------------------------------------------------------------------
# Base Agent – every node becomes one of these
# ----------------------------------------------------------------------
class BaseAgent:
    def __init__(self, role: str, goal: str, instructions: str, tools: List[str] | None = None):
        self.role = role
        self.goal = goal
        self.instructions = instructions
        self.tools = tools or []

<<<<<<< HEAD
    def generate(self, context: str, vibe: str) -> str:
=======
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
        
        if isinstance(files_dict, dict) and files_dict:
            for filename, content in files_dict.items():
                self.session.add_artifact(filename, content)
            self.speak(f"Initial version complete. Generated {len(files_dict)} artifacts: {', '.join(files_dict.keys())}.")
        else:
            self.session.add_artifact("index.html", "<html><body>Failed to generate valid code.</body></html>")
            self.speak("I had trouble structuring the files correctly. Please check the logs.")

    async def run_iteration(self, instruction: str, vibe: str):
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
            conversation_history, vibe, instruction, current_files
        )

        if isinstance(updated_files_dict, dict) and updated_files_dict:
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
>>>>>>> c756b7b (Update agents.py)
        prompt = f"""
You are **{self.role}**.  
Goal: {self.goal}
Instructions: {self.instructions}
Tools: {', '.join(self.tools) if self.tools else 'none'}

Context: {context}
Vibe: {vibe}

Respond **only** with the requested output (code, description, base64 media, etc.).
If you encounter an error, include a short explanation but keep going.
"""
        resp = model.generate_content(prompt, generation_config=gen_cfg)
        return resp.text.strip()


# ----------------------------------------------------------------------
# Specialised agents (Coder / Tester) – grounded & friendly
# ----------------------------------------------------------------------
class CoderAgent(BaseAgent):
    def __init__(self, instructions: str = ""):
        grounded = f"""
Write **browser-runnable** HTML/JS/CSS only.  
- Use **vanilla** JavaScript or standard browser APIs (Canvas, Web Audio, etc.).  
- **Never** import external CDNs or Node packages unless the vibe explicitly demands it.  
- Structure: `index.html` (complete document), `style.css`, `game.js`.  
- If media is requested, embed it as **data URI** (e.g. `data:image/png;base64,...`).  
{instructions}
"""
        super().__init__("Coder", "Generate clean, library-grounded web code", grounded,
                         tools=["code_execution_sim", "debug_trace"])


class TesterAgent(BaseAgent):
    def __init__(self, instructions: str = "")):
        softened = f"""
Test the supplied code for functionality, UX and edge-cases.  
Return a **confidence score** 1-10 and a **status**:
- PASS (9-10) – works perfectly.  
- WARN (5-8) – works but needs tweaks (list them).  
- FAIL (<5) – broken; provide a minimal patch.  

Focus on vibe alignment, not pixel-perfect perfection.  
{instructions}
"""
        super().__init__("Tester", "Validate and suggest iterative fixes", softened,
                         tools=["unit_test_sim", "browser_emulate"])


# ----------------------------------------------------------------------
# Factory – creates a dict {node_id: BaseAgent} from canvas JSON
# ----------------------------------------------------------------------
def create_agents(canvas_cfg: Dict[str, Any]) -> Dict[str, BaseAgent]:
    agents: Dict[str, BaseAgent] = {}

    for node in canvas_cfg.get("nodes", []):
        nid = node["id"]
        typ = node.get("type", "Base")
        title = node.get("title", typ)
        instr = node.get("instructions", "")
        tools = node.get("tools", [])

<<<<<<< Updated upstream
        if typ == "Coder":
            ag = CoderAgent(instr)
        elif typ == "Tester":
            ag = TesterAgent(instr)
        else:                                 # generic (Manager, Designer, etc.)
            ag = BaseAgent(title, f"Perform {typ} tasks", instr, tools)

        ag.role = title                     # user-chosen title becomes the role
        agents[nid] = ag

    return agents
=======
class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        instruction_text = f"Take these user instructions into account: {instructions}" if instructions else ""
        full_prompt = f"{prompt}. {instruction_text} You can suggest story elements that imply game mechanics or sound cues (e.g., '[A laser fires with a sharp *pew* sound]'), knowing the Coder can use powerful game and audio libraries to implement them."
        response = await self.generate_response(full_prompt)
        self.speak(response)
>>>>>>> Stashed changes
