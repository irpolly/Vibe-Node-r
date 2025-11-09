
# Vibe Node(r): The Definitive Backend Deployment Guide

This guide provides the single, most reliable method to deploy your Python backend to Google Cloud Run. Follow these steps exactly.

## Step 1: Initial Setup (Do This Once)

If you have already done these steps, you can skip to Step 2.

1.  **Authenticate gcloud**:
    ```bash
    gcloud auth login
    ```
2.  **Set Your Project**:
    ```bash
    gcloud config set project [YOUR_PROJECT_ID]
    ```
    (Replace `[YOUR_PROJECT_ID]` with `cloud-run-hackathon-477510`)

3.  **Enable APIs**:
    ```bash
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
    ```
4.  **Create API Key Secret**:
    ```bash
    gcloud secrets create gemini-api-key --replication-policy="automatic"
    printf "[YOUR_API_KEY]" | gcloud secrets versions add gemini-api-key --data-file=-
    ```
    (Replace `[YOUR_API_KEY]` with your actual key)

5.  **Grant Secret Access**:
    ```bash
    export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
    gcloud secrets add-iam-policy-binding gemini-api-key \
      --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"
    ```

---

## Step 2: The Golden Command (Deploy Your Backend)

This is the only command you need to deploy your service. It builds the code from your local machine and deploys it, bypassing any GitHub issues.

1.  **Navigate to Your Backend Directory**: Open your terminal and `cd` into the folder that contains your `main.py`, `Dockerfile`, and other backend files.

2.  **Run the Command**: Copy and paste the following command into your terminal. **Replace `[YOUR_PROJECT_ID]` with your actual project ID.**

    ```bash
    gcloud run deploy vibe-node-r \
        --source . \
        --platform managed \
        --region europe-west4 \
        --allow-unauthenticated \
        --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
    ```

**Command Breakdown:**
*   `gcloud run deploy vibe-node-r`: Deploys a service named `vibe-node-r`.
*   `--source .`: This is the crucial part. The `.` tells `gcloud` to use the code in your **current local directory** as the source.
*   `--set-env-vars="API_KEY=SECRET:gemini-api-key:latest"`: This securely attaches your API key to the running service.

After this command succeeds, your backend will be live and correctly configured. The frontend is already set up to use the correct URL, so the application should work immediately.

---

## Troubleshooting

### ERROR: "Container failed to start"

This means your application crashed instantly. **You must check the application logs.**

1.  Find the **Logs URL** in the error message from your failed deployment.
2.  Click on it to open the Google Cloud Logging viewer.
3.  Look for red error messages from your Python application. This will tell you the *exact line of code* that is causing the crash.

**Common Causes:**
*   **Missing API Key**: The `gcloud run deploy` command was run without the `--set-env-vars="API_KEY=SECRET:..."` flag, or the IAM permissions from Step 1.5 were not set correctly. The logs will show a `ValueError` from `agents.py`.
*   **`ENV API_KEY` in Dockerfile**: **Do not set `ENV API_KEY=""` in your Dockerfile.** This creates a race condition where the app reads an empty key and crashes before Cloud Run can inject the real secret.
*   **"Event loop is closed"**: This is an `asyncio` error. It means the Gemini API client was initialized in the wrong thread. The solution is to use "just-in-time" initialization, creating the `GenerativeModel` object inside the `async` function where it's used, not in the `__init__` constructor.

### ERROR: (gcloud.run.deploy) argument --source: expected one argument

If you see this error, it means you forgot the `.` at the end of the `--source` flag.

*   **Incorrect**: `gcloud run deploy --source`
*   **Correct**: `gcloud run deploy --source .`
