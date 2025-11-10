
import React, { useState, useEffect } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { AgentConfig } from '@/types';

interface AgentConfigModalProps {
  node: { data: { config: AgentConfig } };
  onClose: () => void;
  onSave: (config: AgentConfig) => void;
}

const AgentConfigModal: React.FC<AgentConfigModalProps> = ({ node, onClose, onSave }) => {
  const [config, setConfig] = useState<AgentConfig>(node.data.config);

  useEffect(() => {
    setConfig(node.data.config);
  }, [node]);

  const handleSave = () => {
    onSave(config);
  };

  const handleToolChange = (tool: string) => {
    const newTools = config.tools.includes(tool)
      ? config.tools.filter(t => t !== tool)
      : [...config.tools, tool];
    setConfig({ ...config, tools: newTools });
  };

  return (
    <Modal title="Configure Agent" onClose={onClose}>
      <div className="space-y-4 text-gray-300">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
          <input
            type="text"
            value={config.role}
            onChange={(e) => setConfig({ ...config, role: e.target.value })}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Goal</label>
          <textarea
            value={config.goal}
            onChange={(e) => setConfig({ ...config, goal: e.target.value })}
            rows={3}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">LLM</label>
          <select
            value={config.llm}
            onChange={(e) => setConfig({ ...config, llm: e.target.value as AgentConfig['llm'] })}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <option value="gemini-2.5-flash">gemini-2.5-flash</option>
            <option value="gemini-pro">gemini-pro</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Tools</label>
          <div className="flex flex-wrap gap-2">
            {['code_interpreter', 'file_system', 'image_generator', 'style_analyzer', 'test_executor', 'bug_reporter', 'task_scheduler', 'progress_tracker', 'text_generator', 'tone_analyzer'].map(tool => (
              <label key={tool} className="flex items-center gap-2 bg-gray-700 px-3 py-1 rounded-full cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.tools.includes(tool)}
                  onChange={() => handleToolChange(tool)}
                  className="form-checkbox h-4 w-4 rounded text-cyan-500 bg-gray-800 border-gray-600 focus:ring-cyan-500"
                />
                <span className="text-sm">{tool}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-6 flex justify-end gap-3">
        <Button onClick={onClose} variant="secondary">Cancel</Button>
        <Button onClick={handleSave} variant="primary">Save</Button>
      </div>
    </Modal>
  );
};

export default AgentConfigModal;
