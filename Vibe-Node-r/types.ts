
import { Node, Edge } from 'reactflow';

export interface AgentConfig {
  role: string;
  goal: string;
  llm: 'gemini-2.5-flash' | 'gemini-pro';
  tools: string[];
}

export interface NodeData {
  label: string;
  type: 'agent' | 'trigger' | 'tool';
  icon?: React.ReactNode;
  config?: AgentConfig | Record<string, any>;
  color?: string;
  templateKey?: string;
}

export interface Workflow {
  nodes: Node<NodeData>[];
  edges: Edge[];
  viewport?: any;
}

// Represents the data shape when serialized (e.g., for localStorage)
export interface SerializedNodeData extends Omit<NodeData, 'icon'> {}

export interface SerializedWorkflow {
  nodes: Node<SerializedNodeData>[];
  edges: Edge[];
  viewport?: any;
}


export interface ChatMessage {
  id: string;
  agent: {
    name: string;
    color: string;
  };
  text: string;
  timestamp: string;
}
