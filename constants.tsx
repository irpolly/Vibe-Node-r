
import React from 'react';
import { Node, Edge } from 'reactflow';
import { NodeData, AgentConfig } from './types.ts';

export const CodeIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 15" />
  </svg>
);

export const DesignIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
  </svg>
);

export const TestIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
  </svg>
);

export const ManagerIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m-7.5-2.962 3.996 3.996m0 0A5.25 5.25 0 0 1 12 18a5.25 5.25 0 0 1-7.071-7.071M12 6A5.25 5.25 0 0 1 19.071 13.07" />
  </svg>
);

export const WriterIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
  </svg>
);

export const TriggerIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
    </svg>
);

export const ToolIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 0 1 1.45.12l.773.774c.39.39.44 1.022.12 1.45l-.527.737c-.25.35-.272.806-.108 1.204.165.397.505.71.93.78l.893.15c.543.09.94.56.94 1.11v1.093c0 .55-.397 1.02-.94 1.11l-.893.149c-.425.07-.765.383-.93.78-.165.398-.143.854.108 1.204l.527.738c.32.427.27 1.06-.12 1.45l-.773.773a1.125 1.125 0 0 1-1.45.12l-.737-.527c-.35-.25-.806-.272-1.204-.108-.397.165-.71.505-.78.93l-.15.893c-.09.543-.56.94-1.11.94h-1.093c-.55 0-1.02-.397-1.11-.94l-.149-.893c-.07-.425-.383-.765-.78-.93-.398-.165-.854-.143-1.204.108l-.738.527a1.125 1.125 0 0 1-1.45-.12l-.773-.773a1.125 1.125 0 0 1-.12-1.45l.527-.737c.25-.35.272-.806.108-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.11v-1.093c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.764-.384.93-.78.164-.398.142-.855-.108-1.205l-.527-.737a1.125 1.125 0 0 1 .12-1.45l.773-.774a1.125 1.125 0 0 1 1.45-.12l.737.527c.35.25.807.272 1.205.108.397-.165.71-.505.78-.93l.15-.893Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
);

export const TrashIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
  </svg>
);

export const AlignIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
  </svg>
);

export const GitHubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" {...props}>
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"></path>
  </svg>
);

export const DownloadIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
  </svg>
);

export const ChatLogIcon = (props: React.SVGProps<SVGSVGElement>) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.75h16.5m-16.5 3.75h16.5m-16.5 3.75h16.5M5.25 6H18a2.25 2.25 0 0 1 2.25 2.25v10.5A2.25 2.25 0 0 1 18 21H6a2.25 2.25 0 0 1-2.25-2.25V8.25A2.25 2.25 0 0 1 6 6h.75Z" />
    </svg>
);

export const BackIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
  </svg>
);


export const AGENT_TEMPLATES: Record<string, { icon: React.ReactNode, color: string, config: AgentConfig }> = {
  coder: {
    icon: <CodeIcon className="w-6 h-6" />,
    color: 'bg-sky-500',
    config: { role: 'Coder Agent', goal: 'Write, debug, and refactor high-quality code based on specifications.', llm: 'gemini-2.5-flash', tools: ['code_interpreter', 'file_system'] }
  },
  designer: {
    icon: <DesignIcon className="w-6 h-6" />,
    color: 'bg-purple-500',
    config: { role: 'Designer Agent', goal: 'Create visually appealing UI/UX mockups and assets.', llm: 'gemini-2.5-flash', tools: ['image_generator', 'style_analyzer', 'Audio Synthesis'] }
  },
  tester: {
    icon: <TestIcon className="w-6 h-6" />,
    color: 'bg-green-500',
    config: { role: 'Tester Agent', goal: 'Create and run tests to ensure code quality and find bugs.', llm: 'gemini-2.5-flash', tools: ['test_executor', 'bug_reporter'] }
  },
  manager: {
    icon: <ManagerIcon className="w-6 h-6" />,
    color: 'bg-orange-500',
    config: { role: 'Manager Agent', goal: 'Coordinate agent tasks, manage project state, and report progress.', llm: 'gemini-2.5-flash', tools: ['task_scheduler', 'progress_tracker'] }
  },
  writer: {
    icon: <WriterIcon className="w-6 h-6" />,
    color: 'bg-rose-500',
    config: { role: 'Writer Agent', goal: 'Generate human-like text for documentation, scripts, or content.', llm: 'gemini-2.5-flash', tools: ['text_generator', 'tone_analyzer'] }
  }
};

export const INITIAL_NODES: Node<NodeData>[] = [
  { id: '1', type: 'triggerNode', position: { x: 0, y: 0 }, data: { label: 'Vibe Input', type: 'trigger', icon: <TriggerIcon className="w-8 h-8 text-amber-400" /> } },
  { id: '2', type: 'agentNode', position: { x: 0, y: 0 }, data: { ...AGENT_TEMPLATES.manager, label: 'Manager Agent', templateKey: 'manager' } },
  { id: '3', type: 'agentNode', position: { x: 0, y: 0 }, data: { ...AGENT_TEMPLATES.writer, label: 'Writer Agent', templateKey: 'writer' } },
  { id: '4', type: 'agentNode', position: { x: 0, y: 0 }, data: { ...AGENT_TEMPLATES.designer, label: 'Designer Agent', templateKey: 'designer' } },
  { id: '5', type: 'agentNode', position: { x: 0, y: 0 }, data: { ...AGENT_TEMPLATES.coder, label: 'Coder Agent', templateKey: 'coder' } },
  { id: '6', type: 'agentNode', position: { x: 0, y: 0 }, data: { ...AGENT_TEMPLATES.tester, label: 'Tester Agent', templateKey: 'tester' } },
  { id: '7', type: 'toolNode', position: { x: 0, y: 0 }, data: { label: 'Audio Synthesis', type: 'tool', icon: <ToolIcon className="w-6 h-6" /> } },
  { id: '8', type: 'toolNode', position: { x: 0, y: 0 }, data: { label: 'Code Generator', type: 'tool', icon: <ToolIcon className="w-6 h-6" /> } },
];

export const INITIAL_EDGES: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3' },
  { id: 'e2-4', source: '2', target: '4' },
  { id: 'e2-5', source: '2', target: '5' },
  { id: 'e4-7', source: '4', target: '7' },
  { id: 'e5-6', source: '5', target: '6' },
  { id: 'e6-8', source: '6', target: '8' },
];
