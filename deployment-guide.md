
# Vibe Node(r): Backend Deployment Guide for Google Cloud Run

This guide provides the definitive, most reliable method to deploy your Python backend to Google Cloud Run using a repository-based workflow.

## The Problem: Monorepo Structure

Your project is structured as a "monorepo," where the backend code (including the `Dockerfile`) is located in a subdirectory (`is-it-ai-grok/backend/`) instead of the root.

By default, Cloud Build looks for the `Dockerfile` at the root of the repository. When it doesn't find it, the build fails with a "main.py not found" or similar error.

## The Solution: `cloudbuild.yaml`

The solution is to add a `cloudbuild.yaml` file to the **root** of your repository. This file gives Cloud Build explicit instructions on how to build your project.

The provided `cloudbuild.yaml` tells Cloud Build:
1.  First, change your working directory into `is-it-ai-grok/backend/`.
2.  Then, run the `docker build` command from within that directory.
3.  Finally, push the resulting image to Artifact Registry.

This ensures the build happens in the correct location, using the correct files.

---

## Deployment Steps

### Step 1: Verify Your Repository Structure

Ensure your project has the following structure in your GitHub repository:

```
.
├── is-it-ai-grok/
│   └── backend/
│       ├── Dockerfile
│       ├── main.py
│       ├── agents.py
│       ├── session.py
│       └── requirements.txt
├── cloudbuild.yaml  <-- THIS FILE MUST BE AT THE ROOT
└── ... (your frontend files)
```

### Step 2: Verify Your `Dockerfile`

Open the `is-it-ai-grok/backend/Dockerfile` file in your repository. **Confirm that it does NOT contain the line `ENV API_KEY=""`.** This is critical.

### Step 3: Push to GitHub to Deploy

With the `cloudbuild.yaml` file at the root of your repository, the automatic build trigger in Cloud Run will now work correctly.

1.  Commit the `cloudbuild.yaml` file and any other changes to your local Git repository.
2.  Push the changes to your main branch on GitHub.

```bash
git add .
git commit -m "Add cloudbuild.yaml for monorepo deployment"
git push
```

This will automatically trigger a new build in Cloud Build. Because `cloudbuild.yaml` is present, it will follow the correct steps, and the deployment will succeed.

---

## Initial Setup & Troubleshooting

If you are still facing issues, double-check these one-time setup steps.

1.  **IAM Permissions**: Ensure your Cloud Run service account (`[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`) has the **`Secret Manager Secret Accessor`** role in the IAM settings.
2.  **Secret Variable**: In the Cloud Run UI, go to your service > Edit & Deploy New Revision > Variables & Secrets. Ensure you have a variable named `API_KEY` that is correctly referencing the `gemini-api-key` secret.
