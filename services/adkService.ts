
// --- Live, In-Browser ADK Runtime powered by the Gemini API ---

import { SerializedWorkflow } from '../types.ts';
// Fix: Corrected the import name from GoogleGenAI to GoogleGenerativeAI
import { GoogleGenerativeAI } from '@google/genai';

// --- Data Structures ---
interface Message {
  agent_name: string;
  text: string;
  timestamp: number;
}

interface Session {
  id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  messages: Message[];
  artifacts: Record<string, string>; // filename -> content
  agents: Record<string, any>; // Simplified agent representation
  rootAgentId: string | null;
}

// In-memory storage for all active sessions.
const SESSIONS: Record<string, Session> = {};

// --- Gemini API Initialization ---
// IMPORTANT: This assumes process.env.API_KEY is available in the execution environment.
// Fix: Corrected instantiation and removed invalid `vertexai: true` parameter.
const genAI = new GoogleGenerativeAI(process.env.API_KEY);
// Fix: Corrected model name to a valid one.
const modelName = 'gemini-1.5-flash';

// --- Helper Functions ---
const think = (durationMs: number) => new Promise(resolve => setTimeout(resolve, durationMs));

const addMessage = (session: Session, agentName: string, text: string) => {
    session.messages.push({
        agent_name: agentName,
        text,
        timestamp: Date.now() / 1000,
    });
};

const generateAgentResponse = async (agentRole: string, prompt: string): Promise<string> => {
    try {
        const fullPrompt = `You are an AI agent acting as a ${agentRole} in a team. Your personality should be professional but concise. Based on the following prompt, provide your response or update in 1-2 sentences.\n\nPROMPT: "${prompt}"`;
        
        // Fix: Updated to the correct SDK usage pattern.
        const model = genAI.getGenerativeModel({ model: modelName });
        const result = await model.generateContent(fullPrompt);
        const response = result.response;
        return response.text();

    } catch (error) {
        console.error(`Error generating response for ${agentRole}:`, error);
        return `I encountered an error while processing the request for: "${prompt}"`;
    }
};

const generateFinalCode = async (conversation: string, vibe: string): Promise<string> => {
    const prompt = `
        Based on the following development team conversation and the initial "vibe", act as an expert frontend developer.
        Your task is to generate a complete, single-file HTML document that implements the described game.
        The HTML file must include all necessary CSS and JavaScript within it. Do not use any external libraries.
        The game should be simple, playable, and visually match the retro/pixel-art theme discussed.

        INITIAL VIBE: "${vibe}"

        AGENT CONVERSATION:
        ${conversation}

        Generate the HTML file now.
    `;
    try {
        // Fix: Updated to the correct SDK usage pattern.
        const model = genAI.getGenerativeModel({ model: modelName });
        const result = await model.generateContent(prompt);
        const response = result.response;
        const text = response.text();
        // Clean up the response to ensure it's just the HTML code
        const code = text.replace(/^```html\n/, '').replace(/\n```$/, '');
        return code;
    } catch (error) {
        console.error('Error generating final code:', error);
        return `<html><body>Error generating game code.</body></html>`;
    }
};


// --- Core Service Logic ---

export const deploy = (workflowData: Omit<SerializedWorkflow, 'viewport'>): string => {
    const sessionId = `session-${Date.now()}`;
    const agents: Record<string, any> = {};
    let rootAgentId: string | null = null;

    workflowData.nodes.forEach(node => {
        if (node.type === 'agentNode') {
            agents[node.id] = { id: node.id, role: node.data.label, config: node.data.config };
        }
    });

    const triggerNode = workflowData.nodes.find(n => n.type === 'triggerNode');
    if (triggerNode) {
        const rootEdge = workflowData.edges.find(e => e.source === triggerNode.id);
        if (rootEdge && agents[rootEdge.target]) {
            rootAgentId = rootEdge.target;
        }
    }

    if (!rootAgentId) {
        const manager = Object.values(agents).find(a => a.role === 'Manager Agent');
        rootAgentId = manager ? manager.id : Object.keys(agents)[0] || null;
    }

    SESSIONS[sessionId] = { id: sessionId, status: 'PENDING', messages: [], artifacts: {}, agents, rootAgentId };
    console.log(`[ADK Service] Deployed session ${sessionId} with root agent ${rootAgentId}`);
    return sessionId;
};

export const run = async (sessionId: string, vibe: string): Promise<void> => {
    const session = SESSIONS[sessionId];
    if (!session || session.status === 'RUNNING') {
        console.error(`[ADK Service] Session ${sessionId} not found or already running.`);
        return;
    }

    session.status = 'RUNNING';
    session.messages = [];
    session.artifacts = {};

    try {
        addMessage(session, 'System', `Workflow started with vibe: "${vibe}"`);
        await think(500);

        let response = await generateAgentResponse('Manager Agent', `Kick off the project for the vibe: "${vibe}"`);
        addMessage(session, 'Manager Agent', response);
        await think(1200);

        response = await generateAgentResponse('Designer Agent', `Describe your visual concepts for a game with the vibe: "${vibe}"`);
        addMessage(session, 'Designer Agent', response);
        await think(1200);

        response = await generateAgentResponse('Coder Agent', `Explain your plan to start coding a game with the vibe: "${vibe}"`);
        addMessage(session, 'Coder Agent', response);
        await think(1200);

        response = await generateAgentResponse('Tester Agent', `Describe how you will test the game based on the vibe: "${vibe}"`);
        addMessage(session, 'Tester Agent', response);
        await think(1200);
        
        response = await generateAgentResponse('Manager Agent', `Acknowledge the team's initial plan and tell them to proceed.`);
        addMessage(session, 'Manager Agent', response);
        await think(1200);

        const conversationHistory = session.messages.map(m => `${m.agent_name}: ${m.text}`).join('\n');
        addMessage(session, 'System', 'Agents are now generating the final code artifact...');
        
        const finalCode = await generateFinalCode(conversationHistory, vibe);
        session.artifacts['index.html'] = finalCode;
        addMessage(session, 'System', 'Artifact "index.html" created.');
        await think(500);

        session.status = 'COMPLETED';
        addMessage(session, 'System', 'Workflow completed successfully.');
        console.log(`[ADK Service] Session ${sessionId} completed.`);

    } catch (error) {
        session.status = 'FAILED';
        const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.';
        addMessage(session, 'System', `Workflow failed: ${errorMessage}`);
        console.error(`[ADK Service] Session ${sessionId} failed:`, error);
    }
};

export const getStatus = (sessionId: string) => {
    const session = SESSIONS[sessionId];
    if (!session) {
        return { status: 'FAILED', messages: [], artifacts: [] };
    }
    return {
        sessionId: session.id,
        status: session.status,
        messages: session.messages,
        artifacts: Object.keys(session.artifacts),
    };
};

export const getArtifact = (sessionId: string, filename: string): string => {
    const session = SESSIONS[sessionId];
    return session?.artifacts[filename] || `Artifact ${filename} not found.`;
};
