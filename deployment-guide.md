
# Vibe Coder: Backend Deployment Guide for Google Cloud Run

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

### Step 3: Create an Artifact Registry Repository

Your container image needs a place to live. We'll create a Docker repository in Artifact Registry.

```bash
# Choose a region (e.g., us-central1)

# Create the repository
gcloud artifacts repositories create vibe-coder-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Vibe Coder app"
```

### Step 4: Build and Push the Container Image

Navigate to the directory containing your backend files (`main.py`, `Dockerfile`, etc.). Use Cloud Build to build the container image and push it to your new Artifact Registry repository.

```bash
# Get your Project ID
export PROJECT_ID=$(gcloud config get-value project)

# Build the image using Cloud Build
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/vibe-coder-repo/vibe-coder-backend:latest
```
This command automatically finds your `Dockerfile`, builds the image in the cloud, and pushes it to the registry.

### Step 5: Deploy to Cloud Run

Now, deploy the container image from Artifact Registry to Cloud Run. This command also securely mounts the API key from Secret Manager as an environment variable.

```bash
# Deploy the service
gcloud run deploy vibe-node-r \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/vibe-coder-repo/vibe-coder-backend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
```

**Command Breakdown:**
*   `gcloud run deploy vibe-node-r`: Deploys a service named `vibe-node-r`. **Note:** Service names must be all lowercase and contain only letters, numbers, and hyphens.
*   `--image ...`: Specifies the container image you just built.
*   `--platform managed`: Uses the fully managed Cloud Run environment.
*   `--region $REGION`: Deploys to the region you specified.
*   `--allow-unauthenticated`: **IMPORTANT**: This makes your API public. For a production app, you would set up authentication. For this hackathon, it's the simplest way to allow your frontend to call it.
*   `--set-env-vars="API_KEY=SECRET:gemini-api-key:latest"`: This is the crucial part for security. It tells Cloud Run to fetch the latest version of the `gemini-api-key` secret from Secret Manager and mount it as an environment variable named `API_KEY` inside your container. Your Python code (`os.environ["API_KEY"]`) will then be able to access it securely.

### Step 6: Update Your Frontend

After the deployment command finishes, it will output the **Service URL**. It will look something like this:
`https://vibe-node-r-xxxxxxxxxx-uc.a.run.app`

1.  Copy this URL.
2.  Open your frontend code and go to the file `services/adkApi.ts`.
3.  Replace the placeholder `"[YOUR_CLOUD_RUN_SERVICE_URL]"` with your actual service URL.

**Example:**
```typescript
// Before
const API_BASE_URL = "[YOUR_CLOUD_RUN_SERVICE_URL]";

// After
const API_BASE_URL = "https://vibe-node-r-xxxxxxxxxx-uc.a.run.app";
```

Your frontend application is now fully configured to communicate with your live, scalable, and secure backend running on Google Cloud Run.

---

## Troubleshooting

### "Container failed to start" Error

If your deployment fails with an error like `The user-provided container failed to start and listen on the port...`, it means the application inside your container crashed.

*   **Cause**: This often happens because a production web server is not installed. The `flask run` command is for development only. For production, a server like `gunicorn` is needed.
*   **Solution**: Ensure `gunicorn` is listed in your `requirements.txt` file. The `Dockerfile` is already configured to use it.

### "Invalid Reference Format" Error

If your build fails with an error like `invalid argument ... for "-t, --tag" flag: invalid reference format`, this is almost always a naming issue.

*   **Cause**: Cloud services (including Cloud Build and Docker) have strict naming conventions for resources like repositories and services. Your GitHub repository name might contain characters that are not allowed in a Docker image tag, such as uppercase letters or trailing hyphens.
*   **Solution**: Ensure your resource names (like your GitHub repo name if using "Build from repository", or the service name in the `gcloud run deploy` command) adhere to these rules:
    *   Must contain only **lowercase letters, numbers, and hyphens**.
    *   Must start with a letter.
    *   Must not end with a hyphen.

**Example:**
*   **Invalid Name**: `Vibe-Node-r-`
*   **Valid Name**: `vibe-node-r`
