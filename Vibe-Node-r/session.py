
import os
import time
from agents import ManagerAgent, CoderAgent, DesignerAgent, TesterAgent, WriterAgent, Agent
from typing import List, Dict, Any
import asyncio

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
    def __init__(self, session_id: str):
        self.id = session_id
        self.messages: List[Message] = []
        self.artifacts: List[str] = []
        self.shared_state = {}
        self._prepare_agents()  # ← agents created here

    def _prepare_agents(self):
        from agents import ManagerAgent, CoderAgent, DesignerAgent, TesterAgent, WriterAgent
        self.agents = {
            "manager": ManagerAgent("manager", {"role": "Manager"}, self),
            "writer": WriterAgent("writer", {"role": "Writer"}, self),
            "designer": DesignerAgent("designer", {"role": "Designer"}, self),
            "coder": CoderAgent("coder", {"role": "Coder"}, self),
            "tester": TesterAgent("tester", {"role": "Tester"}, self),
        }

    def get_shared(self, key: str):
        """Get from shared state."""
        return self.shared_state.get(key)

    def set_shared(self, key: str, value: any):
        """Set in shared state."""
        self.shared_state[key] = value

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
            # If content is None, remove the file if it exists
            if content is None:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    if filename in self.artifacts:
                        self.artifacts.remove(filename)
                    print(f"Artifact '{filename}' deleted for session {self.session_id}")
                return

            # Otherwise, write or overwrite the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if filename not in self.artifacts:
                self.artifacts.append(filename)
            print(f"Artifact '{filename}' created/updated for session {self.session_id}")
        except Exception as e:
            print(f"Error managing artifact for session {self.session_id}: {e}")

    def get_artifact_content(self, filename: str) -> str | None:
        """Reads the content of a specific artifact file."""
        try:
            filepath = os.path.join(self.artifact_path, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"Error reading artifact {filename}: {e}")
            return None

    def _run_async_task(self, coro):
        """Helper to run an async coroutine in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # The Vertex AI SDK is now initialized once at application startup in main.py
            loop.run_until_complete(coro)
            self.status = "COMPLETED"
            self.add_message("System", "Task completed successfully.")
            print(f"✅ Task for session {self.session_id} completed.")
        except Exception as e:
            self.status = "FAILED"
            error_message = f"Workflow failed: {e}"
            self.add_message("System", error_message)
            print(f"❌ {error_message}")
        finally:
            loop.close()

    def run_workflow(self, vibe: str, instructions: str | None = None):
        """The main runner for the initial agentic workflow."""
        self.status = "RUNNING"
        self.add_message("System", f"Workflow started with vibe: '{vibe}'")
        
        if not self.root_agent_id or self.root_agent_id not in self.agents:
            self.status = "FAILED"
            self.add_message("System", "Root agent not found or configured.")
            return
            
        root_agent = self.agents[self.root_agent_id]
        self._run_async_task(root_agent.run(vibe, instructions))

    def run_instruction(self, instruction: str):
        """Runs a follow-up instruction for iterative development."""
        self.status = "RUNNING"
        self.add_message("System", f"Received new instruction: '{instruction}'")

        # The ManagerAgent is always the entry point for new instructions
        manager_agent = next((agent for agent in self.agents.values() if isinstance(agent, ManagerAgent)), None)
        
        if not manager_agent:
            self.status = "FAILED"
            self.add_message("System", "Manager Agent not found in this workflow to handle the instruction.")
            return
            
        self._run_async_task(manager_agent.run_instruction(instruction))

    # --- Getters ---
    def get_status(self) -> str:
        return self.status

    def is_running(self) -> bool:
        return self.status == "RUNNING"

    def get_messages(self) -> List[Message]:
        return self.messages

    def get_artifacts(self) -> List[str]:
        return self.artifacts
