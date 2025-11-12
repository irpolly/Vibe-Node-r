// lib/utils.ts (full file with patch—keep your existing exports)
import { clsx } from 'clsx';
import { type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { NodeData } from '../types.ts';  // Add if needed for types

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Your other utils: generateId, isValidConnection, etc.
// ...

// ADD THIS FUNCTION (or tweak if it exists elsewhere)
export function reconstructNodeIcons(nodes: NodeData[]): NodeData[] {
  return nodes.map(node => ({
    ...node,
    data: {
      ...node.data,
      icon: node.data.icon || generateSvg(node.type),  // Fallback to SVG gen if missin'
      // Add any icon recon logic: e.g., resize, colorize based on type
      // If deprecated, stub as: return nodes; // Or migrate to svgGenerator
    },
  }));
}

// If it's async or needs more (e.g., for persistent storage):
// export async function reconstructNodeIcons(nodes: NodeData[]): Promise<NodeData[]> { ... }