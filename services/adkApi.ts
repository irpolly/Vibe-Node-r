
import { SerializedWorkflow } from '../types.ts';

const API_BASE_URL = import.meta.env?.DEV ? "http://127.0.0.1:5000" : "";

/**
 * Deploys a workflow to the backend.
 * @param workflowData The workflow configuration to deploy.
 * @returns A promise that resolves with the deployment result, including the new workflowId.
 */
export const deployWorkflow = async (workflowData: Omit<SerializedWorkflow, 'viewport'>): Promise<{ success: boolean; workflowId: string }> => {
  console.log("Deploying workflow to backend:", workflowData);
  const response = await fetch(`${API_BASE_URL}/api/deploy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflowData),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ description: 'An unknown error occurred during deployment.' }));
    throw new Error(error.description || 'Failed to deploy workflow');
  }
  return response.json();
};

/**
 * Starts the execution of a deployed workflow.
 * @param workflowId The ID of the session to run.
 * @param vibe The user's input prompt.
 * @param instructions Optional detailed instructions for the agents.
 * @returns A promise that resolves when the run command is accepted.
 */
export const runWorkflow = async (workflowId: string, vibe: string, instructions: string): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflowId, vibe, instructions }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ description: 'An unknown error occurred while starting the run.' }));
    throw new Error(error.description || 'Failed to start workflow run');
  }
  return response.json();
};

/**
 * Fetches the current status of a running workflow session.
 * @param workflowId The ID of the session to check.
 * @returns A promise that resolves with the session status, messages, and artifacts.
 */
export const getSessionStatus = async (workflowId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/status/${workflowId}`);
  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to fetch session status:", response.status, errorText);
    throw new Error(`Failed to fetch session status (${response.status})`);
  }
  return response.json();
};

/**
 * Fetches the content of a generated artifact.
 * @param workflowId The ID of the session containing the artifact.
 * @param filename The name of the artifact file.
 * @returns A promise that resolves with the text content of the artifact.
 */
export const getArtifactContent = async (workflowId: string, filename: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/api/artifacts/${workflowId}/${filename}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch artifact: ${filename}`);
    }
    return response.text();
};
