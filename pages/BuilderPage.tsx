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
import { AGENT_TEMPLATES, INITIAL_NODES, INITIAL_EDGES, ToolIcon, TriggerIcon, CheckeredFlagIcon } from '../constants.tsx';
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

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  const handleResetLayout = useCallback(() => {
    const reconstructedInitialNodes = reconstructNodeIcons(INITIAL_NODES);
    setNodes(reconstructedInitialNodes);
    setEdges(INITIAL_EDGES);
    showToast("Layout reset to default.", "success");
  }, [setNodes, setEdges, showToast]);

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
        let icon;
        if (dropData.label === 'Code Generator') {
          icon = <CheckeredFlagIcon className="w-6 h-6" />;
        } else {
          icon = <ToolIcon className="w-6 h-6" />;
        }
        data = {
          label: dropData.label,
          type: 'tool',
          icon: icon,
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
        if (edge.deletable === false) {
          showToast("This connection cannot be deleted.", "error");
          return;
        }
        setEdges((eds) => eds.filter((e) => e.id !== edge.id));
      }
    },
    [isDeletingMode, setEdges, showToast]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (isDeletingMode) {
        if (node.deletable === false) {
          showToast("This node cannot be deleted.", "error");
          return;
        }
        setNodes((nds) => nds.filter((n) => n.id !== node.id));
      }
    },
    [isDeletingMode, setNodes, showToast]
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
          >import React, { useState, useCallback, useRef, useEffect } from 'react';
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
  NodeToolbar,               // ADDED
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
import {
  AGENT_TEMPLATES,
  INITIAL_NODES,
  INITIAL_EDGES,
  ToolIcon,
  TriggerIcon,
  CheckeredFlagIcon,
} from '../constants.tsx';
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

const BuilderPageContent: React.FC<BuilderPageProps> = ({ onFinalizeSuccess }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition, getViewport, setViewport } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // NEW – root selection for ADK
  const [rootNodeId, setRootNodeId] = useState<string | null>(null);

  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [isSubmissionModalOpen, setSubmissionModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isDeletingMode, setIsDeletingMode] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  const showToast = useCallback(
    (message: string, type: 'success' | 'error' = 'success') => {
      setToast({ message, type });
      setTimeout(() => setToast(null), 3000);
    },
    []
  );

  const handleResetLayout = useCallback(() => {
    const reconstructedInitialNodes = reconstructNodeIcons(INITIAL_NODES);
    setNodes(reconstructedInitialNodes);
    setEdges(INITIAL_EDGES);
    setRootNodeId(null);                       // reset root on layout reset
    showToast('Layout reset to default.', 'success');
  }, [setNodes, setEdges, showToast]);

  // Auto-load session on mount
  useEffect(() => {
    const savedStateJSON = localStorage.getItem('vibe-coder-autosave');
    if (savedStateJSON) {
      try {
        const savedState: SerializedWorkflow & { rootNodeId?: string } = JSON.parse(savedStateJSON);
        const reconstructedNodes = reconstructNodeIcons(savedState.nodes);
        setNodes(reconstructedNodes);
        setEdges(savedState.edges || []);
        if (savedState.viewport) setViewport(savedState.viewport);
        setRootNodeId(savedState.rootNodeId ?? null);
        showToast('Restored previous session.', 'success');
      } catch (e) {
        console.error('Could not restore session:', e);
        handleResetLayout();
      }
    } else {
      handleResetLayout();
    }
    setIsInitialLoad(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-save (now also persists rootNodeId)
  useEffect(() => {
    if (isInitialLoad) return;
    const handler = setTimeout(() => {
      const serializableNodes = nodes.map(node => {
        const { icon, ...restData } = node.data;
        return { ...node, data: restData };
      });
      const workflow: SerializedWorkflow & { rootNodeId?: string } = {
        nodes: serializableNodes,
        edges,
        viewport: getViewport(),
        rootNodeId,
      };
      localStorage.setItem('vibe-coder-autosave', JSON.stringify(workflow));
    }, 1000);
    return () => clearTimeout(handler);
  }, [nodes, edges, getViewport, isInitialLoad, rootNodeId]);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges(eds => addEdge(params, eds)),
    [setEdges]
  );

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
          console.error('Invalid agent template key:', dropData.templateKey);
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
        let icon;
        if (dropData.label === 'Code Generator') {
          icon = <CheckeredFlagIcon className="w-6 h-6" />;
        } else {
          icon = <ToolIcon className="w-6 h-6" />;
        }
        data = {
          label: dropData.label,
          type: 'tool',
          icon,
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
      setNodes(nds => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes]
  );

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: any) => {
      if (node.type === 'agentNode') {
        setSelectedNode(node);
      }
    },
    []
  );

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      if (isDeletingMode) {
        if (edge.deletable === false) {
          showToast('This connection cannot be deleted.', 'error');
          return;
        }
        setEdges(eds => eds.filter(e => e.id !== edge.id));
      }
    },
    [isDeletingMode, setEdges, showToast]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (isDeletingMode) {
        if (node.deletable === false) {
          showToast('This node cannot be deleted.', 'error');
          return;
        }
        setNodes(nds => nds.filter(n => n.id !== node.id));
      }
    },
    [isDeletingMode, setNodes, showToast]
  );

  const handleToggleDeleteMode = () => {
    setIsDeletingMode(prev => !prev);
  };

  const handleSaveConfig = (newConfig: any) => {
    if (!selectedNode) return;
    setNodes(nds =>
      nds.map(n => {
        if (n.id === selectedNode.id) {
          n.data = { ...n.data, config: newConfig, label: newConfig.role };
        }
        return n;
      })
    );
    setSelectedNode(null);
  };

  // NEW – FINALIZE HANDLER (replaces the old one)
  const handleFinalize = async () => {
    const agentNodes = nodes.filter(n => n.type === 'agentNode');
    if (agentNodes.length < 2) {
      showToast('Workflow must contain at least two agents.', 'error');
      return;
    }

    // ---- Auto-pick a sensible root if user forgot ----
    let finalRootId = rootNodeId;
    if (!finalRootId) {
      const manager = agentNodes.find(n => n.data.config?.role?.toLowerCase().includes('manager'));
      finalRootId = manager?.id ?? agentNodes[0].id;
      setRootNodeId(finalRootId);
    }

    setIsLoading(true);
    try {
      const serializableNodes = nodes.map(node => {
        const { icon, ...restData } = node.data;
        return { ...node, data: restData };
      });

      const payload = {
        vibe: '', // will be filled by SubmissionModal or you can add a vibe input here
        root_node_id: finalRootId,
        config: {
          nodes: serializableNodes
            .filter(n => n.type === 'agentNode' || n.type === 'triggerNode' || n.type === 'toolNode')
            .map(n => ({
              id: n.id,
              type: n.data.type ?? 'Base',
              title: n.data.label ?? n.data.type,
              instructions: n.data.config?.instructions ?? '',
              tools: n.data.config?.tools ?? [],
            })),
          edges: edges.map(e => ({
            source: e.source,
            target: e.target,
          })),
        },
      };

      const result = await deployWorkflow(payload); // now expects the new shape
      showToast('Workflow finalized! Transitioning to output view...');
      onFinalizeSuccess(result.workflowId);
    } catch (error: any) {
      console.error('Finalization failed:', error);
      showToast(error.message || 'Failed to finalize workflow.', 'error');
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

  // NEW – render root button inside every node
  const nodeWithToolbar = (node: Node) => (
    <>
      {React.createElement(nodeTypes[node.type as keyof typeof nodeTypes], {
        ...node,
      })}
      <NodeToolbar isVisible={true} position="top">
        <button
          onClick={() => setRootNodeId(node.id)}
          className={`px-2 py-1 text-xs rounded ${
            rootNodeId === node.id
              ? 'bg-yellow-500 text-black'
              : 'bg-gray-600 text-white hover:bg-gray-500'
          }`}
        >
          {rootNodeId === node.id ? 'Root' : 'Set Root'}
        </button>
      </NodeToolbar>
    </>
  );

  return (
    <div className={`w-screen h-screen flex flex-col bg-gray-900`} ref={reactFlowWrapper}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <Toolbar
        onFinalize={handleFinalize}
        onToggleDeleteMode={handleToggleDeleteMode}
        isDeletingMode={isDeletingMode}
        onShowSubmission={() => setSubmissionModalOpen(true)}
        onResetLayout={handleResetLayout}
        isLoading={isLoading}
      />
      <div className="flex flex-1 h-full">
        <Sidebar />
        <div className="flex-grow h-full">
          <ReactFlow
            nodes={nodes.map(node => ({
              ...node,
              // wrap every node with the toolbar (only agent nodes really need it, but it’s harmless)
              type: node.type,
              // React Flow will render the wrapped component via nodeTypes; we override here for the toolbar
            }))}
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
            {/* Render custom node with toolbar */}
            {nodes.map(node => (
              <ReactFlow.Node key={node.id} id={node.id} type={node.type}>
                {nodeWithToolbar(node)}
              </ReactFlow.Node>
            ))}
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
