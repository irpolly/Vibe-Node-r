
import React, { useState, useEffect, useRef } from 'react';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import Toast from '@/components/ui/Toast';
import { GitHubIcon, DownloadIcon, BackIcon, ManagerIcon, CodeIcon, DesignIcon, TestIcon, WriterIcon, ChatLogIcon } from '@/constants';
import { ChatMessage } from '@/types';
import { runWorkflow, getSessionStatus, getArtifactContent } from '@/services/adkApi';

interface OutputPageProps {
  onBack: () => void;
  workflowId: string | null;
}

const initialCode = `<!--
  The generated code for the live preview
  will appear here after the agents finish.
-->`;

const agentAvatars: Record<string, React.ReactNode> = {
    'Manager Agent': <ManagerIcon className="w-6 h-6 text-orange-400" />,
    'Coder Agent': <CodeIcon className="w-6 h-6 text-sky-400" />,
    'Designer Agent': <DesignIcon className="w-6 h-6 text-purple-400" />,
    'Tester Agent': <TestIcon className="w-6 h-6 text-green-400" />,
    'Writer Agent': <WriterIcon className="w-6 h-6 text-rose-400" />,
    'System': <div className="w-6 h-6 text-gray-400">⚙️</div>,
};

const agentColors: Record<string, string> = {
    'Manager Agent': 'text-orange-400',
    'Coder Agent': 'text-sky-400',
    'Designer Agent': 'text-purple-400',
    'Tester Agent': 'text-green-400',
    'Writer Agent': 'text-rose-400',
    'System': 'text-gray-400',
};

const OutputPage: React.FC<OutputPageProps> = ({ onBack, workflowId }) => {
  const [vibe, setVibe] = useState('');
  const [code, setCode] = useState(initialCode);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [agentMessages, setAgentMessages] = useState<ChatMessage[]>([]);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const pollingIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (iframeRef.current) {
      iframeRef.current.srcdoc = code;
    }
  }, [code]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentMessages]);

  // Cleanup polling on component unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const pollStatus = async (id: string) => {
    try {
      const statusData = await getSessionStatus(id);
      
      const newMessages = statusData.messages.map((msg: any) => ({
        id: `${msg.timestamp}-${msg.agent_name}`,
        agent: {
            name: msg.agent_name,
            color: agentColors[msg.agent_name] || 'text-gray-400',
        },
        text: msg.text,
        timestamp: new Date(msg.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }));
      setAgentMessages(newMessages);

      if (statusData.status === 'COMPLETED' || statusData.status === 'FAILED') {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
        }
        setIsLoading(false);
        showToast(`Workflow ${statusData.status.toLowerCase()}!`, statusData.status === 'COMPLETED' ? 'success' : 'error');

        if (statusData.status === 'COMPLETED' && statusData.artifacts.length > 0) {
            const codeArtifact = statusData.artifacts.find((a: string) => a.endsWith('.html'));
            if (codeArtifact && workflowId) {
                const artifactContent = await getArtifactContent(workflowId, codeArtifact);
                setCode(artifactContent);
            }
        }
      }
    } catch (error: any) {
      console.error("Polling failed:", error);
      showToast(error.message, 'error');
      setIsLoading(false);
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    }
  };

  const handleRun = async () => {
    if (!vibe.trim()) {
      showToast('Please enter a vibe first!', 'error');
      return;
    }
    if (!workflowId) {
      showToast('No active workflow session found.', 'error');
      return;
    }

    setIsLoading(true);
    setAgentMessages([]);
    setCode(initialCode);

    try {
      await runWorkflow(workflowId, vibe);
      // Start polling immediately
      pollingIntervalRef.current = window.setInterval(() => {
        pollStatus(workflowId);
      }, 1000);
    } catch (error: any) {
      setIsLoading(false);
      showToast(error.message, 'error');
    }
  };

  const handleSaveChatLog = () => {
    if (agentMessages.length === 0) {
      showToast('No chat log to save.', 'error');
      return;
    }
    const logContent = agentMessages
      .map(msg => `[${msg.timestamp}] ${msg.agent.name}: ${msg.text}`)
      .join('\n');
    
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agent-chat-log.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Chat log saved!', 'success');
  };

  const handleSaveProject = () => {
    if (code === initialCode || isLoading) {
      showToast('No project code to save.', 'error');
      return;
    }
    const blob = new Blob([code], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'index.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Project saved as index.html!', 'success');
  };

  const handleDeploy = (platform: 'GitHub') => {
    showToast(`Simulating deployment to ${platform}...`, 'success');
  };

  return (
    <div className="bg-gray-900 text-white w-screen h-screen flex flex-col">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <header className="flex-shrink-0 bg-gray-800/50 p-3 border-b border-gray-700 flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
            <Button onClick={onBack} variant="ghost"><BackIcon className="w-5 h-5" /> Back to Builder</Button>
            <div className="w-px h-6 bg-gray-600"></div>
            <h1 className="text-lg font-bold text-cyan-400">Vibe-to-Code Output</h1>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={handleSaveChatLog} variant="secondary"><ChatLogIcon className="w-5 h-5" /> Save Chat Log</Button>
          <Button onClick={handleSaveProject} variant="secondary"><DownloadIcon className="w-5 h-5" /> Save Project</Button>
          <Button onClick={() => handleDeploy('GitHub')} variant="secondary"><GitHubIcon className="w-5 h-5" /> Deploy to GitHub</Button>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 p-4 overflow-hidden">
        {/* Left Column */}
        <div className="flex flex-col gap-4 h-full">
          <div className="flex-shrink-0">
            <label htmlFor="vibe-input" className="block text-sm font-medium text-gray-300 mb-2">1. Vibe Input</label>
            <div className="flex gap-2">
              <input
                id="vibe-input"
                type="text"
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
                className="flex-grow bg-gray-700 border border-gray-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                placeholder="e.g., a simple breakout game with a neon aesthetic"
              />
              <Button onClick={handleRun} disabled={isLoading} className="px-6">
                {isLoading ? <Spinner /> : 'Run'}
              </Button>
            </div>
          </div>
          <div className="flex-1 bg-gray-800 rounded-lg overflow-hidden border border-gray-700 relative flex flex-col">
            <div className="flex-shrink-0 bg-gray-900/50 p-2 text-sm text-gray-300 border-b border-gray-700">Agent Output</div>
            <div className="h-full w-full overflow-auto p-4 space-y-4">
              {agentMessages.map((msg) => (
                <div key={msg.id} className="flex items-start gap-3 animate-fade-in">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-gray-700 flex-shrink-0`}>
                      {agentAvatars[msg.agent.name] || msg.agent.name.charAt(0)}
                  </div>
                  <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${msg.agent.color}`}>{msg.agent.name}</span>
                      <span className="text-xs text-gray-500">{msg.timestamp}</span>
                    </div>
                    <p className="text-gray-200">{msg.text}</p>
                  </div>
                </div>
              ))}
              {isLoading && (
                  <div className="flex items-center gap-2 text-gray-400 pt-2">
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse [animation-delay:0.2s]"></div>
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse [animation-delay:0.4s]"></div>
                      <span className="ml-2">Agents are collaborating...</span>
                  </div>
              )}
              {agentMessages.length === 0 && !isLoading && (
                  <div className="flex items-center justify-center h-full text-gray-500">
                      Agent output will appear here...
                  </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col h-full">
          <h2 className="text-lg font-semibold mb-2 text-gray-300">2. Live Preview</h2>
          <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <iframe
              ref={iframeRef}
              title="Live Preview"
              className="w-full h-full bg-white"
              sandbox="allow-scripts"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default OutputPage;
