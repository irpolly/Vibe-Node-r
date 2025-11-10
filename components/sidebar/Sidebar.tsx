
import React from 'react';
import { AGENT_TEMPLATES, TriggerIcon, ToolIcon } from '../../constants.tsx';

const Sidebar: React.FC = () => {
  const onDragStart = (event: React.DragEvent, type: string, data: any) => {
    const transferData = JSON.stringify({ type, data });
    event.dataTransfer.setData('application/reactflow', transferData);
    event.dataTransfer.effectAllowed = 'move';
  };

  const toolNodes = [
    { label: 'Code Generator' },
    { label: 'Audio Synthesis' },
  ];

  return (
    <aside className="w-64 bg-gray-900 p-4 border-r border-gray-700/50 flex flex-col gap-4">
      <h2 className="text-lg font-bold text-cyan-400">Available Nodes</h2>
      
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-400">Trigger</h3>
        <div
          className="p-3 bg-gray-800 rounded-lg cursor-grab flex items-center gap-3 hover:bg-gray-700 hover:ring-2 hover:ring-cyan-500 transition-all"
          onDragStart={(event) => onDragStart(event, 'trigger', { label: 'Vibe Input' })}
          draggable
        >
          <TriggerIcon className="w-6 h-6 text-amber-400" />
          <span className="font-medium">Vibe Input</span>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-400">Agents</h3>
        {Object.entries(AGENT_TEMPLATES).map(([key, template]) => (
          <div
            key={key}
            className="p-3 bg-gray-800 rounded-lg cursor-grab flex items-center gap-3 hover:bg-gray-700 hover:ring-2 hover:ring-cyan-500 transition-all"
            onDragStart={(event) => onDragStart(event, 'agent', { templateKey: key })}
            draggable
          >
            {template.icon}
            <span className="font-medium">{template.config.role}</span>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
          Tools
        </h3>
        {toolNodes.map((tool, index) => (
          <div
            key={index}
            className="p-3 bg-gray-800 rounded-lg cursor-grab flex items-center gap-3 hover:bg-gray-700 hover:ring-2 hover:ring-cyan-500 transition-all"
            onDragStart={(event) => onDragStart(event, 'tool', { label: tool.label })}
            draggable
          >
            <ToolIcon className="w-6 h-6" />
            <span className="font-medium">{tool.label}</span>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;
