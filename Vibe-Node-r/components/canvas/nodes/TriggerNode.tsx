
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { NodeData } from '../../../types.ts';

const TriggerNode: React.FC<NodeProps<NodeData>> = ({ data }) => {
  return (
    <div className="w-48 bg-gray-800 rounded-full shadow-md border-2 border-amber-400/50 flex items-center justify-center p-3">
      <div className="flex items-center gap-3">
        {data.icon}
        <div className="text-white font-semibold">{data.label}</div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-cyan-400 w-3 h-3" />
    </div>
  );
};

export default memo(TriggerNode);
