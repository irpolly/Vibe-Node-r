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

    def generate(self, context: str, vibe: str) -> str:
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

        if typ == "Coder":
            ag = CoderAgent(instr)
        elif typ == "Tester":
            ag = TesterAgent(instr)
        else:                                 # generic (Manager, Designer, etc.)
            ag = BaseAgent(title, f"Perform {typ} tasks", instr, tools)

        ag.role = title                     # user-chosen title becomes the role
        agents[nid] = ag

    return agents