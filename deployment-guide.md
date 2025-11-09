
# Vibe Node(r): Backend Deployment Guide for Google Cloud Run

This guide provides step-by-step instructions to deploy the Python Flask backend to Google Cloud Run. This will give you a scalable, serverless HTTPS endpoint for your frontend application to interact with.

## Prerequisites

1.  **Google Cloud Project**: You need a Google Cloud project with billing enabled.
2.  **gcloud CLI**: Make sure you have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and initialized.
3.  **Enabled APIs**: Ensure the following APIs are enabled for your project:
    *   Cloud Build API (`serviceusage.googleapis.com`)
    *   Artifact Registry API (`artifactregistry.googleapis.com`)
    *   Cloud Run Admin API (`run.googleapis.com`)
    *   Secret Manager API (`secretmanager.googleapis.com`)

    You can enable them with the following command:
    ```bash
    gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
    ```
4.  **Permissions**: You need sufficient permissions in your project (e.g., `Owner`, `Editor`, or specific roles like `Cloud Run Admin`, `Cloud Build Editor`, `Artifact Registry Administrator`, `Secret Manager Admin`).

---

## Deployment Steps

### Step 1: Authenticate and Configure gcloud

First, authenticate your local gcloud CLI with your Google Account and set your project.

```bash
# Log in to your Google Account
gcloud auth login

# Set your project ID
gcloud config set project [YOUR_PROJECT_ID]
```
Replace `[YOUR_PROJECT_ID]` with your actual Google Cloud project ID.

### Step 2: Secure Your API Key with Secret Manager

It is a security best practice to not expose your API key directly. We will use Google Cloud's Secret Manager.

```bash
# Create a new secret to hold your API key
gcloud secrets create gemini-api-key --replication-policy="automatic"

# Add your API key as the first version of the secret
# Replace [YOUR_API_KEY] with your actual Gemini API key
printf "[YOUR_API_KEY]" | gcloud secrets versions add gemini-api-key --data-file=-
```

### Step 2.5: Grant Secret Access (CRITICAL FIX)

By default, Cloud Run cannot access Secret Manager. You must explicitly grant permission to the Cloud Run service identity.

```bash
# Get your Google Cloud Project Number
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

# Grant the Cloud Run service account access to the secret
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```
**Note:** This command uses the default Compute Engine service account, which Cloud Run uses by default. If you use a custom service account, replace the member email accordingly.

### Step 3: Create an Artifact Registry Repository

Your container image needs a place to live. We'll create a Docker repository in Artifact Registry.

```bash
# Set your region
export REGION=europe-west4

# Create the repository
gcloud artifacts repositories create vibe-coder-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Vibe Node(r) app"
```

### Step 4: Build and Push the Container Image

Navigate to the directory containing your backend files (`main.py`, `Dockerfile`, etc.). Use Cloud Build to build the container image and push it to your new Artifact Registry repository.

```bash
# Get your Project ID
export PROJECT_ID=$(gcloud config get-value project)

# Build the image using Cloud Build
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/vibe-coder-repo/vibe-node-r-backend:latest
```

### Step 5: Deploy to Cloud Run

Now, deploy the container image from Artifact Registry to Cloud Run.

```bash
# Deploy the service
gcloud run deploy vibe-node-r \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/vibe-coder-repo/vibe-node-r-backend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
```

### Step 6: Update Your Frontend

After the deployment command finishes, it will output the **Service URL**. It will look something like this:
`https://vibe-node-r-xxxxxxxxxx-ew.a.run.app`

1.  Copy this URL.
2.  Open your frontend code and go to the file `services/adkApi.ts`.
3.  Replace the placeholder `"[YOUR_CLOUD_RUN_SERVICE_URL]"` with your actual service URL.

Your frontend application is now fully configured to communicate with your live, scalable, and secure backend running on Google Cloud Run.

---

## Troubleshooting

### "Container failed to start" Error

This is the most common error. It means the application inside your container crashed immediately on startup. **The build log is not enough; you must check the application logs.**

1.  Find the **Logs URL** in the error message from your failed deployment.
2.  Click on it to open the Google Cloud Logging viewer.
3.  Look for red error messages from your Python application. This will tell you the *exact line of code* that is causing the crash.

**Common Causes:**
*   **Missing API Key**: The `gcloud run deploy` command was run without the `--set-env-vars="API_KEY=SECRET:..."` flag, or the IAM permissions from Step 2.5 were not set correctly. The logs will show a `RuntimeError` from `agents.py`.
*   **`ENV API_KEY` in Dockerfile**: **Do not set `ENV API_KEY=""` in your Dockerfile.** This creates a race condition where the app reads an empty key and crashes before Cloud Run can inject the real secret. Your Dockerfile should have no mention of `API_KEY`.
*   **Missing Production Server**: Ensure `gunicorn` is listed in your `requirements.txt` file.

### "Conflict for resource" Error

If your deployment fails with an error like `ABORTED: Conflict for resource...`, it means you have a deployment race condition.

*   **Cause**: This happens when a new deployment is triggered while another deployment for the same service is already in progress.
*   **Solution**: Go to the **Cloud Build > History** page in your Google Cloud Console, **cancel** any running builds, wait a minute, and then trigger a single, new build.

### "Invalid Reference Format" Error

*   **Cause**: Your GitHub repository name or the service name you provided contains characters that are not allowed in a Docker image tag (e.g., uppercase letters, special characters).
*   **Solution**: Ensure your resource names adhere to these rules: lowercase letters, numbers, and hyphens only.
