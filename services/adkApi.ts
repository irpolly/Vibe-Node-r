
import { SerializedWorkflow } from '../types.ts';

// IMPORTANT: This URL points to your deployed Cloud Run service.
const API_BASE_URL = "https://vibe-node-r-85229041043.europe-west4.run.app";

/**
 * Checks if the API URL is configured and throws an error if not.
 */
const checkApiConfig = () => {
  if (!API_BASE_URL || API_BASE_URL.includes("YOUR_CLOUD_RUN_SERVICE_URL")) {
    throw new Error("Backend API endpoint is not configured. Please follow the deployment-guide.md and update the API_BASE_URL in services/adkApi.ts");
  }
};

/**
 * Deploys a workflow to the backend.
 * @param workflowData The workflow configuration to deploy.
 * @returns A promise that resolves with the deployment result, including the new workflowId.
 */
export const deployWorkflow = async (workflowData: Omit<SerializedWorkflow, 'viewport'>): Promise<{ success: boolean; workflowId: string }> => {
  checkApiConfig();
  console.log("Deploying workflow to backend:", workflowData);
  const response = await fetch(`${API_BASE_URL}/deploy`, {
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
 * @returns A promise that resolves when the run command is accepted.
 */
export const runWorkflow = async (workflowId: string, vibe: string): Promise<{ success: boolean; message: string }> => {
  checkApiConfig();
  const response = await fetch(`${API_BASE_URL}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflowId, vibe }),
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
  checkApiConfig();
  const response = await fetch(`${API_BASE_URL}/status/${workflowId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch session status');
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
    checkApiConfig();
    const response = await fetch(`${API_BASE_URL}/artifacts/${workflowId}/${filename}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch artifact: ${filename}`);
    }
    return response.text();
};
