
import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  Controls,
  Background,
  Connection,
  Edge,
  Node,
} from 'reactflow';

import Sidebar from '../components/sidebar/Sidebar.tsx';
import Toolbar from '../components/toolbar/Toolbar.tsx';
import AgentConfigModal from '../components/modals/AgentConfigModal.tsx';
import SubmissionModal from '../components/modals/SubmissionModal.tsx';
import Toast from '../components/ui/Toast.tsx';
import AgentNode from '../components/canvas/nodes/AgentNode.tsx';
import TriggerNode from '../components/canvas/nodes/TriggerNode.tsx';
import ToolNode from '../components/canvas/nodes/ToolNode.tsx';

import { deployWorkflow } from '../services/adkApi.ts';
import { AGENT_TEMPLATES, INITIAL_NODES, INITIAL_EDGES, ToolIcon, TriggerIcon } from '../constants.tsx';
import { NodeData, SerializedWorkflow } from '../types.ts';
import { generateSvg } from '../lib/svgGenerator.ts';
import { reconstructNodeIcons } from '../lib/utils.ts';

const nodeTypes = {
  agentNode: AgentNode,
  triggerNode: TriggerNode,
  toolNode: ToolNode,
};

interface BuilderPageProps {
  onFinalizeSuccess: (workflowId: string) => void;
}

const getLayoutedNodes = (nodesToLayout: Node<NodeData>[], edgesToLayout: Edge[]): Node<NodeData>[] => {
    if (nodesToLayout.length === 0) return [];

    const adj: { [key: string]: string[] } = {};
    const inDegree: { [key: string]: number } = {};

    nodesToLayout.forEach(node => {
        adj[node.id] = [];
        inDegree[node.id] = 0;
    });

    edgesToLayout.forEach(edge => {
        if (adj[edge.source]) {
            adj[edge.source].push(edge.target);
        }
        if (inDegree[edge.target] !== undefined) {
            inDegree[edge.target]++;
        }
    });

    const queue: string[] = nodesToLayout.filter(node => inDegree[node.id] === 0).map(n => n.id);
    
    const layers: { [level: number]: string[] } = {};
    let level = 0;

    while (queue.length > 0) {
        const levelSize = queue.length;
        layers[level] = [];
        for (let i = 0; i < levelSize; i++) {
            const u = queue.shift()!;
            layers[level].push(u);
            
            (adj[u] || []).forEach(v => {
                inDegree[v]--;
                if (inDegree[v] === 0) {
                    queue.push(v);
                }
            });
        }
        level++;
    }

    const COLUMN_WIDTH = 280;
    const ROW_HEIGHT = 180;

    const newNodes = [...nodesToLayout];
    const nodeMap = new Map(newNodes.map(n => [n.id, n]));

    Object.keys(layers).forEach(levelStr => {
        const currentLevel = parseInt(levelStr, 10);
        const nodesInLevel = layers[currentLevel];
        const numNodes = nodesInLevel.length;
        const levelHeight = (numNodes - 1) * ROW_HEIGHT;
        const startY = -levelHeight / 2;

        nodesInLevel.forEach((nodeId, i) => {
            const node = nodeMap.get(nodeId);
            if (node) {
                node.position = {
                    x: currentLevel * COLUMN_WIDTH,
                    y: startY + i * ROW_HEIGHT,
                };
            }
        });
    });
    return newNodes;
}

const BuilderPageContent: React.FC<BuilderPageProps> = ({ onFinalizeSuccess }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition, getViewport, setViewport } = useReactFlow();
  
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [isSubmissionModalOpen, setSubmissionModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isDeletingMode, setIsDeletingMode] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleAutoAlign = useCallback(() => {
    const layoutedNodes = getLayoutedNodes(nodes, edges);
    setNodes(layoutedNodes);
    showToast("Workflow aligned!", "success");
  }, [nodes, edges, setNodes]);

  const handleResetLayout = useCallback(() => {
    const reconstructedInitialNodes = reconstructNodeIcons(INITIAL_NODES);
    const layoutedNodes = getLayoutedNodes(reconstructedInitialNodes, INITIAL_EDGES);
    setNodes(layoutedNodes);
    setEdges(INITIAL_EDGES);
    showToast("Layout reset to default.", "success");
  }, [setNodes, setEdges]);

  // Auto-load session on mount
  useEffect(() => {
    const savedStateJSON = localStorage.getItem('vibe-coder-autosave');
    if (savedStateJSON) {
      try {
        const savedState: SerializedWorkflow = JSON.parse(savedStateJSON);
        const reconstructedNodes = reconstructNodeIcons(savedState.nodes);
        setNodes(reconstructedNodes);
        setEdges(savedState.edges || []);
        if (savedState.viewport) {
          setViewport(savedState.viewport);
        }
        showToast("Restored previous session.", "success");
      } catch (e) {
        console.error("Could not restore session:", e);
        handleResetLayout();
      }
    } else {
        handleResetLayout();
    }
    setIsInitialLoad(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-save session on change (debounced)
  useEffect(() => {
    if (isInitialLoad) return;

    const handler = setTimeout(() => {
      const serializableNodes = nodes.map(node => {
          const { icon, ...restData } = node.data;
          return { ...node, data: restData };
      });
      const workflow: SerializedWorkflow = { nodes: serializableNodes, edges, viewport: getViewport() };
      localStorage.setItem('vibe-coder-autosave', JSON.stringify(workflow));
    }, 1000);

    return () => {
      clearTimeout(handler);
    };
  }, [nodes, edges, getViewport, isInitialLoad]);

  const onConnect = useCallback((params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      if (!reactFlowWrapper.current) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const transferData = JSON.parse(event.dataTransfer.getData('application/reactflow'));
      const type = transferData.type;
      const dropData = transferData.data;
      
      const position = screenToFlowPosition({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      let data: NodeData;

      if (type === 'agent') {
        const template = AGENT_TEMPLATES[dropData.templateKey as keyof typeof AGENT_TEMPLATES];
        if (!template) {
            console.error("Invalid agent template key:", dropData.templateKey);
            return;
        }
        data = {
          label: template.config.role,
          type: 'agent',
          icon: template.icon,
          color: template.color,
          config: template.config,
          templateKey: dropData.templateKey,
        };
      } else if (type === 'trigger') {
        data = {
          label: dropData.label,
          type: 'trigger',
          icon: <TriggerIcon className="w-8 h-8 text-amber-400" />,
        };
      } else if (type === 'tool') {
        data = {
          label: dropData.label,
          type: 'tool',
          icon: <ToolIcon className="w-6 h-6" />,
        };
      } else {
        console.error('Unknown node type dropped:', type);
        return;
      }

      const newNode = {
        id: `${type}-${+new Date()}`,
        type: `${type}Node`,
        position,
        data,
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes]
  );

  const onNodeDoubleClick = useCallback((_: React.MouseEvent, node: any) => {
    if (node.type === 'agentNode') {
      setSelectedNode(node);
    }
  }, []);

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      if (isDeletingMode) {
        setEdges((eds) => eds.filter((e) => e.id !== edge.id));
      }
    },
    [isDeletingMode, setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (isDeletingMode) {
        setNodes((nds) => nds.filter((n) => n.id !== node.id));
      }
    },
    [isDeletingMode, setNodes]
  );

  const handleToggleDeleteMode = () => {
    setIsDeletingMode(prev => !prev);
  };

  const handleSaveConfig = (newConfig: any) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNode.id) {
          n.data = { ...n.data, config: newConfig, label: newConfig.role };
        }
        return n;
      })
    );
    setSelectedNode(null);
  };

  const handleFinalize = async () => {
    if (nodes.filter(n => n.type === 'agentNode').length < 2) {
      showToast("Workflow must contain at least two agents.", "error");
      return;
    }
    setIsLoading(true);
    try {
      const serializableNodes = nodes.map(node => {
          const { icon, ...restData } = node.data;
          return { ...node, data: restData };
      });
      const workflowData: SerializedWorkflow = { nodes: serializableNodes, edges, viewport: getViewport() };
      
      const result = await deployWorkflow(workflowData);
      showToast("Workflow finalized! Transitioning to output view...");
      onFinalizeSuccess(result.workflowId);
    } catch (error: any) {
      console.error("Finalization failed:", error);
      showToast(error.message || "Failed to finalize workflow.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadSvg = () => {
    const svgString = generateSvg(nodes, edges);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vibe-workflow-architecture.svg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`w-screen h-screen flex flex-col bg-gray-900`} ref={reactFlowWrapper}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <Toolbar
        onFinalize={handleFinalize}
        onToggleDeleteMode={handleToggleDeleteMode}
        isDeletingMode={isDeletingMode}
        onShowSubmission={() => setSubmissionModalOpen(true)}
        onAutoAlign={handleAutoAlign}
        onResetLayout={handleResetLayout}
        isLoading={isLoading}
      />
      <div className="flex flex-1 h-full">
        <Sidebar />
        <div className="flex-grow h-full" >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeDoubleClick={onNodeDoubleClick}
            onEdgeClick={onEdgeClick}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            className={`bg-gray-800/50 ${isDeletingMode ? 'delete-mode' : ''}`}
          >
            <Background color="#4a5568" gap={16} />
            <Controls />
          </ReactFlow>
        </div>
      </div>
      {selectedNode && (
        <AgentConfigModal
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onSave={handleSaveConfig}
        />
      )}
      {isSubmissionModalOpen && (
        <SubmissionModal
          onClose={() => setSubmissionModalOpen(false)}
          onDownloadSvg={handleDownloadSvg}
        />
      )}
    </div>
  );
};

const BuilderPage: React.FC<BuilderPageProps> = ({ onFinalizeSuccess }) => (
  <ReactFlowProvider>
    <BuilderPageContent onFinalizeSuccess={onFinalizeSuccess} />
  </ReactFlowProvider>
);

export default BuilderPage;
