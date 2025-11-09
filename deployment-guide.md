
# Vibe Node(r): Backend Deployment Guide for Google Cloud Run

This guide provides the definitive, most reliable method to deploy your Python backend to Google Cloud Run using a repository-based workflow.

## The Problem: Build Failures

You have encountered two common build failures:
1.  **"main.py not found"**: This happens because your backend code is in a subdirectory (`is-it-ai-grok/backend/`), but Cloud Build looks for it at the root by default.
2.  **"logs_bucket" permission error**: This happens because the service account running the build doesn't have permission to write logs to the default Cloud Storage bucket.

## The Solution: `cloudbuild.yaml`

The solution to both problems is to add a `cloudbuild.yaml` file to the **root** of your repository. This file gives Cloud Build explicit instructions to solve both issues:
1.  It tells Cloud Build to first change its working directory into `is-it-ai-grok/backend/`.
2.  It tells Cloud Build to send logs directly to Cloud Logging, bypassing the need for storage permissions.

---

## Deployment Steps

### Step 1: Create and Push `cloudbuild.yaml`

1.  In your project, go to the **root directory** (the same level as your `is-it-ai-grok` folder).
2.  Create a new file named exactly `cloudbuild.yaml`.
3.  Copy the content for `cloudbuild.yaml` provided in the changes.
4.  Commit and push this new file to your GitHub repository.

```bash
git add cloudbuild.yaml
git commit -m "FIX: Add cloudbuild.yaml to fix deployment"
git push
```

**That's it!** Pushing this file will trigger a new build in Cloud Run. This time, it will find the instructions in `cloudbuild.yaml` and succeed.

### Step 2: Verify the Live Service

After the deployment succeeds, your service will be live. If you still encounter an `API_KEY not set` error in the application UI, it means the secret was not attached correctly during a previous deployment attempt. You can fix this by running the "Golden Command" below from your local machine.

**The Golden Command (for fixing secret configuration)**

This command forces a new revision with the correct secret settings.
1.  Navigate your terminal to the `is-it-ai-grok/backend` directory.
2.  Run the command, replacing `[YOUR_PROJECT_ID]` with your actual project ID.

```bash
gcloud run deploy vibe-node-r \
    --source . \
    --platform managed \
    --region europe-west4 \
    --allow-unauthenticated \
    --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
```

---
## Initial Setup Checklist (One-Time)

Ensure these steps have been completed in your Google Cloud project.

1.  **IAM Permissions**: Your Cloud Run service account (`[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`) must have the **`Secret Manager Secret Accessor`** role.
2.  **APIs Enabled**: `run.googleapis.com`, `cloudbuild.googleapis.com`, `secretmanager.googleapis.com`, `generativelanguage.googleapis.com`.
3.  **Secret Created**: A secret named `gemini-api-key` must exist with your API key as its value.
