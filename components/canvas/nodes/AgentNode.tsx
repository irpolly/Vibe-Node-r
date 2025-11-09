
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { NodeData } from '../../../types.ts';

const AgentNode: React.FC<NodeProps<NodeData>> = ({ data }) => {
  return (
    <div className={`w-48 rounded-lg shadow-md border-2 border-gray-600/50 ${data.color || 'bg-gray-700'}`}>
      <div className="p-3">
        <div className="flex items-center gap-3">
          <div className="text-white">{data.icon}</div>
          <div className="text-white font-semibold truncate">{data.label}</div>
        </div>
      </div>
      <Handle type="target" position={Position.Left} className="!bg-cyan-400 w-3 h-3" />
      <Handle type="source" position={Position.Right} className="!bg-cyan-400 w-3 h-3" />
    </div>
  );
};

export default memo(AgentNode);
