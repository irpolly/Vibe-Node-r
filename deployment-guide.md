
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

After this command succeeds, your backend will be live and correctly configured. The frontend is already set up to use the correct URL.

---

## Troubleshooting

### ERROR: (gcloud.run.deploy) argument --source: expected one argument

If you see this error, it means you forgot the `.` at the end of the `--source` flag.

*   **Incorrect**: `gcloud run deploy --source`
*   **Correct**: `gcloud run deploy --source .`

### ERROR: "Container failed to start"

This means your application crashed instantly.
*   **Cause**: The most common cause is that your local `Dockerfile` still contains the line `ENV API_KEY=""`.
*   **Solution**: Open your local `Dockerfile`, delete that line, save the file, and re-run the Golden Command from Step 2.
