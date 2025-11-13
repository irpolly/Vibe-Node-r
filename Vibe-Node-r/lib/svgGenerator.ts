
import { Node, Edge } from 'reactflow';
import { NodeData } from '../types.ts';

const NODE_WIDTH = 180;
const NODE_HEIGHT = 60;
const PADDING = 50;

export const generateSvg = (nodes: Node<NodeData>[], edges: Edge[]): string => {
  if (nodes.length === 0) return '<svg></svg>';

  const minX = Math.min(...nodes.map(n => n.position.x));
  const maxX = Math.max(...nodes.map(n => n.position.x + (n.width || NODE_WIDTH)));
  const minY = Math.min(...nodes.map(n => n.position.y));
  const maxY = Math.max(...nodes.map(n => n.position.y + (n.height || NODE_HEIGHT)));

  const width = maxX - minX + PADDING * 2;
  const height = maxY - minY + PADDING * 2;

  const nodeSvgs = nodes.map(node => {
    const x = node.position.x - minX + PADDING;
    const y = node.position.y - minY + PADDING;
    const isTrigger = node.type === 'triggerNode';
    const color = isTrigger ? '#f59e0b' : '#0891b2'; // amber-500 or cyan-600

    return `
      <g transform="translate(${x}, ${y})">
        <rect 
          width="${node.width || NODE_WIDTH}" 
          height="${node.height || NODE_HEIGHT}" 
          rx="${isTrigger ? (node.height || NODE_HEIGHT) / 2 : 8}" 
          fill="#2d3748" 
          stroke="${color}" 
          stroke-width="2"
        />
        <text 
          x="${(node.width || NODE_WIDTH) / 2}" 
          y="${(node.height || NODE_HEIGHT) / 2}" 
          fill="#e2e8f0" 
          text-anchor="middle" 
          dominant-baseline="middle" 
          font-family="Inter, sans-serif"
          font-size="14"
          font-weight="500"
        >
          ${node.data.label}
        </text>
      </g>
    `;
  }).join('');

  const edgeSvgs = edges.map(edge => {
    const sourceNode = nodes.find(n => n.id === edge.source);
    const targetNode = nodes.find(n => n.id === edge.target);
    if (!sourceNode || !targetNode) return '';

    const sourceX = sourceNode.position.x - minX + PADDING + (sourceNode.width || NODE_WIDTH);
    const sourceY = sourceNode.position.y - minY + PADDING + (sourceNode.height || NODE_HEIGHT) / 2;
    const targetX = targetNode.position.x - minX + PADDING;
    const targetY = targetNode.position.y - minY + PADDING + (targetNode.height || NODE_HEIGHT) / 2;

    return `
      <path 
        d="M ${sourceX} ${sourceY} C ${sourceX + 50} ${sourceY}, ${targetX - 50} ${targetY}, ${targetX} ${targetY}"
        fill="none"
        stroke="#6366f1"
        stroke-width="2"
        marker-end="url(#arrow)"
      />
    `;
  }).join('');

  return `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" style="background-color: #1a202c;">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />
        </marker>
      </defs>
      ${edgeSvgs}
      ${nodeSvgs}
    </svg>
  `;
};
