
import React from 'react';
import { Node } from 'reactflow';
import { NodeData, SerializedNodeData } from '../types.ts';
import { AGENT_TEMPLATES, TriggerIcon, ToolIcon } from '../constants.tsx';

/**
 * Reconstructs node data with React component icons after being loaded from serialization.
 * @param nodes An array of nodes, where the `data.icon` property is missing.
 * @returns An array of nodes with the `data.icon` property restored.
 */
export const reconstructNodeIcons = (nodes: Node<SerializedNodeData>[]): Node<NodeData>[] => {
  return nodes.map(node => {
    let icon: React.ReactNode;

    // Determine the node type based on the `type` property of the React Flow node object
    const nodeType = node.type;

    switch (nodeType) {
      case 'agentNode':
        const key = node.data.templateKey;
        icon = key && AGENT_TEMPLATES[key] ? AGENT_TEMPLATES[key].icon : React.createElement('div', null);
        break;
      case 'triggerNode':
        icon = React.createElement(TriggerIcon, { className: "w-8 h-8 text-amber-400" });
        break;
      case 'toolNode':
        icon = React.createElement(ToolIcon, { className: "w-6 h-6" });
        break;
      default:
        icon = React.createElement('div', null); // Fallback for unknown node types
    }

    return {
      ...node,
      data: {
        ...node.data,
        icon: icon,
      },
    } as Node<NodeData>;
  });
};
