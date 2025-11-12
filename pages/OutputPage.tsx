import React, { useState, useEffect, useRef } from 'react';
import Button from '../components/ui/Button.tsx';
import Spinner from '../components/ui/Spinner.tsx';
import Toast from '../components/ui/Toast.tsx';
import Emulator from '../components/ui/Emulator.tsx';
import { GitHubIcon, DownloadIcon, BackIcon, ManagerIcon, CodeIcon, DesignIcon, TestIcon, WriterIcon, ChatLogIcon, RotateIcon, ZipIcon, SendIcon, ResetIcon } from '../constants.tsx';
import { ChatMessage } from '../types.ts';
import { runWorkflow, getSessionStatus, instructAgent } from '../services/adkApi.ts';
import { GAME_IDEAS } from '../lib/gameIdeas.ts';

interface OutputPageProps {
  onBack: () => void;
  workflowId: string | null;
}

const initialCode = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body, html {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #111827; /* bg-gray-900 */
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: monospace;
      color: #4b5563; /* gray-600 */
    }
    .container {
      text-align: center;
    }
    .spinner {
      border: 4px solid #4b5563; /* gray-600 */
      border-top: 4px solid #38bdf8; /* cyan-400 */
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 1rem;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="spinner"></div>
    <p>Awaiting agent output...</p>
  </div>
</body>
</html>
`;

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

const API_BASE_URL = import.meta.env?.DEV ? "http://127.0.0.1:5000" : "";

const OutputPage: React.FC<OutputPageProps> = ({ onBack, workflowId }) => {
  const [vibe, setVibe] = useState('');
  const [instructions, setInstructions] = useState('');
  const [iterationInstruction, setIterationInstruction] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [agentMessages, setAgentMessages] = useState<ChatMessage[]>([]);
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const [isMobileView, setIsMobileView] = useState(false);

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const pollingIntervalRef = useRef<number | null>(null);

  // Set a random vibe on initial load
  useEffect(() => {
    setVibe(GAME_IDEAS[Math.floor(Math.random() * GAME_IDEAS.length)]);
  }, []);

  // Detect mobile screen for emulator snapping
  useEffect(() => {
    const checkMobile = () => setIsMobileView(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentMessages]);

  // synopsis setup and event listeners
  useEffect(() => {
   if (!gameOutput) return;

    // === LIVE DESIGN SYNOPSIS ===
    UIManager.setSynopsis(`
  # ECHO OF SELF – LIVE DESIGN

  **Core Loop**: Ael + Shadow = one soul, two minds.  
  **Win**: Loyalty >90 → Harmony  
  **Lose**: Rebellion =100 → Dark Ending  

  **5 Levels**:  
  1. Whispering Woods (tutorial)  
  2. Ruined City (combat)  
  3. Arcane Library (puzzle)  
  4. Shadow Plane (inverted)  
  5. Final Arena (choice)  

  **Vibe**: *“What if your shadow had opinions?”*
    `);

  // === LEVEL COMPLETION LISTENER ===
  const handleLevelComplete = ((e: CustomEvent) => {
    UIManager.log(`Level ${e.detail.level} complete! Moving to ${e.detail.next}`);
  }) as EventListener;
  window.addEventListener('levelcomplete', handleLevelComplete);

  return () => {
    window.removeEventListener('levelcomplete', handleLevelComplete);
  };
}, [gameOutput]);

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

  const startPolling = (id: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    pollingIntervalRef.current = window.setInterval(() => {
      pollStatus(id);
    }, 2000);
  };

  const pollStatus = async (id: string) => {
    try {
      const statusData = await getSessionStatus(id);
      
      const newMessages = statusData.messages.map((msg: any) => ({
        id: `${msg.timestamp}-${msg.agent_name}`,
        agent: { name: msg.agent_name, color: agentColors[msg.agent_name] || 'text-gray-400' },
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
        
        setArtifacts(statusData.artifacts || []);

        if (statusData.status === 'COMPLETED' && statusData.artifacts.length > 0) {
            const htmlArtifact = statusData.artifacts.find((a: string) => a.endsWith('.html'));
            if (htmlArtifact && workflowId) {
                // Add a cache-busting query param to force iframe reload
                const url = `${API_BASE_URL}/api/artifacts/${workflowId}/${htmlArtifact}?t=${new Date().getTime()}`;
                setPreviewUrl(url);
            } else {
                setPreviewUrl(null);
                if (iframeRef.current) {
                    iframeRef.current.srcdoc = '<html><body><p>No HTML file was generated.</p></body></html>';
                }
            }
        }
      }
    } catch (error: any) {
      console.error("Polling failed:", error);
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      setIsLoading(false);
      showToast(error.message || 'Could not get workflow status.', 'error');
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
    setArtifacts([]);
    setPreviewUrl(null);
    if (iframeRef.current) {
        iframeRef.current.src = 'about:blank';
        iframeRef.current.srcdoc = initialCode;
    }

    try {
      await runWorkflow(workflowId, vibe, instructions);
      startPolling(workflowId);
    } catch (error: any) {
      setIsLoading(false);
      showToast(error.message, 'error');
    }
  };

  const handleSendInstruction = async () => {
    if (!iterationInstruction.trim()) {
      showToast('Please enter an instruction to send.', 'error');
      return;
    }
    if (!workflowId) {
      showToast('No active workflow session found.', 'error');
      return;
    }
    if (isLoading) {
      showToast('An operation is already in progress.', 'error');
      return;
    }

    setIsLoading(true);
    try {
      await instructAgent(workflowId, iterationInstruction);
      setIterationInstruction(''); // Clear input after sending
      startPolling(workflowId);
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
    const logContent = agentMessages.map(msg => `[${msg.timestamp}] ${msg.agent.name}: ${msg.text}`).join('\n');
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

  const handleRestartEmulator = () => {
    if (iframeRef.current) {
        if (previewUrl && iframeRef.current.src) {
            // Force a full reload of the iframe content by re-setting its src
            // A new timestamp acts as a cache-buster
            const url = new URL(iframeRef.current.src);
            url.searchParams.set('t', new Date().getTime().toString());
            iframeRef.current.src = url.toString();
            showToast("Emulator restarting...", "success");
        } else {
            // If no preview is loaded, just reset to the initial placeholder
            iframeRef.current.src = 'about:blank';
            iframeRef.current.srcdoc = initialCode;
            showToast("Emulator reset to initial state.", "success");
        }
    }
  };

  return (
    <div className="bg-gray-900 text-white w-screen h-screen flex flex-col">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <header className="flex-shrink-0 bg-gray-800/50 p-3 border-b border-gray-700 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
            <Button onClick={onBack} variant="ghost"><BackIcon className="w-5 h-5" /> Back to Builder</Button>
            <div className="w-px h-6 bg-gray-600"></div>
            <h1 className="text-lg font-bold text-cyan-400">Vibe-to-Code Output</h1>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={handleSaveChatLog} variant="secondary"><ChatLogIcon className="w-5 h-5" /> Save Log</Button>
          {workflowId && (
            <a href={`${API_BASE_URL}/api/artifacts/zip/${workflowId}`} download={`vibe-artifacts-${workflowId}.zip`}>
              <Button variant="secondary"><ZipIcon className="w-5 h-5" /> Download .zip</Button>
            </a>
          )}
          <a href="https://github.com/new?template_name=vibe-coding-hackathon&template_owner=google-cloud-run-hackathon" target="_blank" rel="noopener noreferrer">
            <Button variant="secondary"><GitHubIcon className="w-5 h-5" /> Create Repo</Button>
          </a>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 p-4 overflow-hidden">
        {/* Left Column */}
        <div className="flex flex-col gap-4 h-full overflow-y-auto pr-2">
          <div className="flex-shrink-0">
            <label htmlFor="vibe-input" className="block text-sm font-medium text-gray-300 mb-2">1. Vibe Input</label>
            <div className="flex gap-2">
              <input
                id="vibe-input"
                type="text"
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
                className="flex-grow bg-gray-700 border border-gray-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                placeholder="e.g., a simple breakout game"
              />
              <Button onClick={handleRun} disabled={isLoading} className="px-6">
                {isLoading ? <Spinner /> : 'Run'}
              </Button>
            </div>
          </div>
          <div className="flex-shrink-0">
            <label htmlFor="instructions-input" className="block text-sm font-medium text-gray-300 mb-2">2. Specific Instructions (Optional)</label>
            <textarea
                id="instructions-input"
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                rows={3}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                placeholder="e.g., 'Use a dark, minimalist theme with blue accents.'"
            />
          </div>
          
          <div className="flex-1 bg-gray-800 rounded-lg overflow-hidden border border-gray-700 relative flex flex-col min-h-[300px]">
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
                    <p className="text-gray-200 whitespace-pre-wrap">{msg.text}</p>
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
            <div className="flex-shrink-0 border-t border-gray-700 p-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={iterationInstruction}
                  onChange={(e) => setIterationInstruction(e.target.value)}
                  className="flex-grow bg-gray-700 border border-gray-600 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="Instruct agents to fix or change something..."
                  disabled={isLoading || !workflowId || artifacts.length === 0}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendInstruction()}
                />
                <Button onClick={handleSendInstruction} disabled={isLoading || !workflowId || artifacts.length === 0}>
                  <SendIcon className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col h-full overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-300">3. Live Preview</h2>
            <div className="flex items-center gap-2">
              <Button onClick={() => setOrientation(o => o === 'portrait' ? 'landscape' : 'portrait')} variant="ghost">
                <RotateIcon className="w-5 h-5" />
                Rotate
              </Button>
              <Button onClick={handleRestartEmulator} variant="ghost" disabled={isLoading}>
                <ResetIcon className="w-5 h-5" />
                Restart
              </Button>
            </div>
          </div>
          <div className="flex-1 flex items-center justify-center w-full min-h-0">
            <Emulator
              ref={iframeRef}
              src={previewUrl}
              srcDoc={initialCode}
              orientation={orientation}
              isMobileView={isMobileView}
            />
          </div>
          {artifacts.length > 0 && (
            <div className="mt-4 flex-shrink-0">
                <h2 className="text-lg font-semibold mb-2 text-gray-300">4. Generated Artifacts</h2>
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-3 space-y-2">
                    {artifacts.map(artifact => (
                        <a
                            key={artifact}
                            href={`${API_BASE_URL}/api/artifacts/${workflowId}/${artifact}`}
                            download={artifact}
                            className="flex items-center justify-between p-2 bg-gray-700 rounded-md hover:bg-gray-600 transition-colors"
                            aria-label={`Download ${artifact}`}
                        >
                            <span className="text-gray-200">{artifact}</span>
                            <DownloadIcon className="w-5 h-5 text-cyan-400" />
                        </a>
                    ))}
                </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OutputPage;
// ADD THIS useEffect (anywhere in the file)
useEffect(() => {
  if (!gameOutput) return;
  UIManager.setSynopsis(`...`); // ← paste synopsis
  const handler = ((e: CustomEvent) => UIManager.log(...)) as EventListener;
  window.addEventListener('levelcomplete', handler);
  return () => window.removeEventListener('levelcomplete', handler);
}, [gameOutput]);

// IN YOUR EXISTING LEVEL COMPLETE LOGIC
this.events.emit('levelcomplete', { 
  level: this.levelData.name, 
  next: LEVELS[this.currentLevel + 1]?.name || 'Win' 
});

// Or via window (if scene is sandboxed)
window.dispatchEvent(new CustomEvent('levelcomplete', { 
  detail: { level: 'Forest', next: 'City' } 
}));
