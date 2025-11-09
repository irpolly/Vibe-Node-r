
import { SerializedWorkflow } from '../types.ts';
import * as adkService from './adkService.ts';

/**
 * Deploys a workflow to the simulated ADK service.
 * @param workflowData The workflow configuration to deploy.
 * @returns A promise that resolves with the deployment result, including the new workflowId.
 */
export const deployWorkflow = async (workflowData: Omit<SerializedWorkflow, 'viewport'>): Promise<{ success: boolean; workflowId:string }> => {
  console.log("Deploying workflow to ADK service:", workflowData);
  const sessionId = adkService.deploy(workflowData);
  return { success: true, workflowId: sessionId };
};

/**
 * Starts the execution of a deployed workflow in the simulated ADK service.
 * @param workflowId The ID of the session to run.
 * @param vibe The user's input prompt.
 * @returns A promise that resolves when the run command is accepted.
 */
export const runWorkflow = async (workflowId: string, vibe: string): Promise<{ success: boolean; message: string }> => {
    console.log(`Starting run for workflow ${workflowId} with vibe: "${vibe}"`);
    adkService.run(workflowId, vibe);
    return { success: true, message: "Workflow execution started." };
};

/**
 * Fetches the current status of a running workflow session from the ADK service.
 * @param workflowId The ID of the session to check.
 * @returns A promise that resolves with the session status, messages, and artifacts.
 */
export const getSessionStatus = async (workflowId: string) => {
  console.log(`Getting status for ${workflowId}`);
  return adkService.getStatus(workflowId);
};

/**
 * Fetches the content of a generated artifact from the ADK service.
 * @param workflowId The ID of the session containing the artifact.
 * @param filename The name of the artifact file.
 * @returns A promise that resolves with the text content of the artifact.
 */
export const getArtifactContent = async (workflowId: string, filename: string): Promise<string> => {
    console.log(`Getting artifact ${filename} for ${workflowId}`);
    return adkService.getArtifact(workflowId, filename);
};
