
# Vibe Node(r): Backend Deployment Guide for Google Cloud Run

This guide provides the definitive, most reliable method to deploy your Python backend to Google Cloud Run.

## Prerequisites

1.  **Google Cloud Project**: You need a Google Cloud project with billing enabled.
2.  **gcloud CLI**: Make sure you have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and initialized.
3.  **Enabled APIs**: Ensure the following APIs are enabled for your project:
    *   Cloud Build API (`serviceusage.googleapis.com`)
    *   Artifact Registry API (`artifactregistry.googleapis.com`)
    *   Cloud Run Admin API (`run.googleapis.com`)
    *   Secret Manager API (`secretmanager.googleapis.com`)

    You can enable them with: `gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com`

---

## Deployment Steps

### Step 1: Authenticate and Configure gcloud

First, authenticate your local gcloud CLI and set your project.

```bash
# Log in to your Google Account
gcloud auth login

# Set your project ID
gcloud config set project [YOUR_PROJECT_ID]
```
Replace `[YOUR_PROJECT_ID]` with your actual Google Cloud project ID (e.g., `cloud-run-hackathon-477510`).

### Step 2: Secure Your API Key (If Not Already Done)

If you haven't already, create a secret to hold your API key.

```bash
# Create the secret
gcloud secrets create gemini-api-key --replication-policy="automatic"

# Add your API key to the secret
printf "[YOUR_API_KEY]" | gcloud secrets versions add gemini-api-key --data-file=-
```

### Step 3: Grant Secret Access (If Not Already Done)

Ensure the Cloud Run service identity has permission to access the secret.

```bash
# Get your Google Cloud Project Number
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

# Grant the access role
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 4: Final Sanity Check (CRITICAL)

Before you deploy, **you must verify the `Dockerfile` on your local computer.**

1.  Open the `Dockerfile` in your project folder.
2.  **Confirm that the file does NOT contain the line `ENV API_KEY=""`.** If it does, you must remove it and save the file. This is the most common cause of deployment failure.

### Step 5: The Definitive Build and Deploy Command

Navigate your terminal to the directory containing your backend files (`main.py`, `Dockerfile`, etc.). Run the following single command. This command builds the code from your **local directory** (bypassing any GitHub cache) and deploys it to Cloud Run.

**Replace `[YOUR_PROJECT_ID]` in the command below with your actual project ID.**

```bash
# Build from your local source and deploy the service
gcloud run deploy vibe-node-r \
    --source . \
    --platform managed \
    --region europe-west4 \
    --allow-unauthenticated \
    --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
```

This single `gcloud run deploy --source .` command is the most reliable method. It tells Cloud Build to use the code in your current directory, build it, and deploy the resulting image to Cloud Run all in one atomic step.

### Step 6: Verify Success

After the command finishes, it will output the **Service URL**. Your backend is now live. The frontend is already configured to use the correct URL, so the application should work immediately.
