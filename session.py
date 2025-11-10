
import os
import time
from agents import ManagerAgent, CoderAgent, DesignerAgent, TesterAgent, WriterAgent, Agent
from typing import List, Dict, Any
import asyncio
import google.generativeai as genai

# --- Data Structures ---
class Message:
    """Represents a single message in the agent chat."""
    def __init__(self, agent_name: str, text: str):
        self.agent_name = agent_name
        self.text = text
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "agent_name": self.agent_name,
            "text": self.text,
            "timestamp": self.timestamp
        }

# --- Session Class ---
class Session:
    """
    Manages a single workflow execution, including its state, agents,
    and generated artifacts. Acts as a virtual environment.
    """
    AGENT_MAP = {
        "Coder Agent": CoderAgent,
        "Designer Agent": DesignerAgent,
        "Tester Agent": TesterAgent,
        "Writer Agent": WriterAgent,
        "Manager Agent": ManagerAgent,
    }

    def __init__(self, session_id: str, workflow_data: Dict[str, Any], artifact_path: str):
        self.session_id = session_id
        self.artifact_path = artifact_path
        self.status = "PENDING"  # PENDING -> RUNNING -> COMPLETED -> FAILED
        self.messages: List[Message] = []
        self.artifacts: List[str] = []
        self.agents: Dict[str, Agent] = {}
        self.root_agent_id: str | None = None
        
        os.makedirs(self.artifact_path, exist_ok=True)
        self._prepare_agents(workflow_data)

    def _prepare_agents(self, workflow_data: Dict[str, Any]):
        """Parses workflow data and instantiates agent objects."""
        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])

        # 1. Instantiate all agents
        for node in nodes:
            if node.get('type') == 'agentNode':
                agent_label = node['data']['label']
                agent_class = self.AGENT_MAP.get(agent_label, ManagerAgent) # Default to Manager
                self.agents[node['id']] = agent_class(
                    node_id=node['id'],
                    config=node['data'].get('config', {}),
                    session=self
                )

        # 2. Find the root agent (connected to the trigger)
        trigger_node_id = next((n['id'] for n in nodes if n.get('type') == 'triggerNode'), None)
        if trigger_node_id:
            root_edge = next((e for e in edges if e['source'] == trigger_node_id), None)
            if root_edge:
                self.root_agent_id = root_edge['target']
        
        # If no explicit root, pick the first available Manager or any agent
        if not self.root_agent_id:
            self.root_agent_id = next(
                (id for id, agent in self.agents.items() if isinstance(agent, ManagerAgent)),
                next(iter(self.agents.keys()), None)
            )
        
        print(f"Session {self.session_id}: Agents prepared. Root is {self.root_agent_id}")

    def add_message(self, agent_name: str, text: str):
        """Adds a message to the session's log."""
        self.messages.append(Message(agent_name, text))

    def add_artifact(self, filename: str, content: str):
        """Saves a file artifact and logs it."""
        try:
            filepath = os.path.join(self.artifact_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.artifacts.append(filename)
            print(f"Artifact '{filename}' created for session {self.session_id}")
        except Exception as e:
            print(f"Error creating artifact for session {self.session_id}: {e}")

    def _run_async_workflow(self, vibe: str):
        """Helper to run the async functions in a new event loop for the thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Configure genai at the start of the thread's life
            # This ensures it's configured in the correct event loop context
            api_key = os.environ.get("API_KEY")
            if not api_key:
                raise ValueError("API_KEY environment variable not found in thread.")
            genai.configure(api_key=api_key)
            print("✅ Gemini API configured successfully within the worker thread.")

            # Now run the agent logic
            if not self.root_agent_id or self.root_agent_id not in self.agents:
                raise ValueError("Root agent not found or configured.")
            
            root_agent = self.agents[self.root_agent_id]
            
            # Run the async execution chain from the root agent
            loop.run_until_complete(root_agent.run(vibe))
            
            self.status = "COMPLETED"
            self.add_message("System", "Workflow completed successfully.")
            print(f"✅ Workflow for session {self.session_id} completed.")

        except Exception as e:
            self.status = "FAILED"
            error_message = f"Workflow failed: {e}"
            self.add_message("System", error_message)
            print(f"❌ {error_message}")
        finally:
            loop.close()

    def run_workflow(self, vibe: str):
        """The main runner for the agentic workflow."""
        self.status = "RUNNING"
        self.add_message("System", f"Workflow started with vibe: '{vibe}'")
        self._run_async_workflow(vibe)


    # --- Getters ---
    def get_status(self) -> str:
        return self.status

    def is_running(self) -> bool:
        return self.status == "RUNNING"

    def get_messages(self) -> List[Message]:
        return self.messages

    def get_artifacts(self) -> List[str]:
        return self.artifacts
