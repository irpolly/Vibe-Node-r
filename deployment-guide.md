
# Vibe Node(r): Final Deployment Guide

This guide provides the definitive method to deploy your unified frontend and backend application to Google Cloud Run.

## Architecture Overview

Your application is now a single, self-contained service. The `Dockerfile` uses a **multi-stage build** to achieve this:
1.  **Stage 1 (Node.js)**: It builds your React frontend into a folder of static files (`build/`).
2.  **Stage 2 (Python)**: It copies the static files from Stage 1 into the final Python container's `build/` directory.
3.  **Result**: The Python Flask server runs, serving both the static frontend files (your app's UI at `/`) and the backend API (at `/api/...`) from the same container. This eliminates all CORS issues and simplifies deployment.

---

## Deployment Steps

### Step 1: Initial Setup (Do This Once)

If you have already done these steps, you can skip to Step 2.

1.  **Authenticate gcloud**: `gcloud auth login`
2.  **Set Project**: `gcloud config set project [YOUR_PROJECT_ID]`
3.  **Enable APIs**: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com generativelanguage.googleapis.com`
4.  **Create API Key Secret**:
    ```bash
    gcloud secrets create gemini-api-key --replication-policy="automatic"
    printf "[YOUR_API_KEY]" | gcloud secrets versions add gemini-api-key --data-file=-
    ```
5.  **Grant Secret Access**:
    ```bash
    export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
    gcloud secrets add-iam-policy-binding gemini-api-key \
      --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"
    ```

---

## Step 2: The Golden Command (Deploy Everything)

This single command builds and deploys your entire unified application.

1.  **Navigate to Your Project's Root Directory**: Open your terminal and `cd` into the top-level folder that contains your `Dockerfile`, `package.json`, and `main.py`.

2.  **Run the Command**: Copy and paste the following command into your terminal. **Replace `[YOUR_PROJECT_ID]` with your actual project ID.**

    ```bash
    gcloud run deploy vibe-node-r \
        --source . \
        --platform managed \
        --region europe-west4 \
        --allow-unauthenticated \
        --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
    ```

After this command succeeds, your backend and frontend will be live at the same public URL. Visiting the URL will now show your application.

---

## Troubleshooting

### ERROR: "COPY failed: stat app/build: file does not exist"

This error means the `Dockerfile` is trying to copy the frontend build output from the wrong directory.
*   **Cause**: The frontend build tool (Vite) creates a `dist` directory by default, but the `Dockerfile` was looking for a `build` directory.
*   **Solution**: Ensure your `vite.config.ts` specifies `build: { outDir: 'build' }` and your `Dockerfile`'s final `COPY` command is `COPY --from=builder /app/build ./build`.

### ERROR: "Container failed to start"

This means your application crashed instantly.
*   **Cause**: The most common cause is an issue with the API Key. Either the IAM permission is missing, or the secret was not attached correctly.
*   **Solution**: Carefully re-run the commands in Step 1.5 (Grant Secret Access) and Step 2 (The Golden Command) to ensure the permissions and configuration are correct. Use the "Logs URL" from the error message to see the specific error inside the container.
