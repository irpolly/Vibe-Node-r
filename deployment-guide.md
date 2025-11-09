
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

3.  **Enable APIs (CRITICAL STEP)**:
    This command enables all necessary services, including the Generative Language API.
    ```bash
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com generativelanguage.googleapis.com
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

After this command succeeds, your backend will be live and correctly configured. The frontend is already set up to use the correct URL, so the application should work immediately.

---

## Troubleshooting

### ERROR: "API key not valid"

This error comes directly from Google's servers. It means your application is running correctly but the API key itself is the problem.

*   **Cause 1: Generative Language API is not enabled.** This is the most likely cause.
    *   **Solution**: Run the command from Step 1.3 of this guide: `gcloud services enable generativelanguage.googleapis.com`. Then, redeploy your service using the Golden Command.
*   **Cause 2: The secret value is incorrect.** You may have made a typo when creating the secret.
    *   **Solution**: Update the secret with the correct key by running `printf "[YOUR_CORRECT_API_KEY]" | gcloud secrets versions add gemini-api-key --data-file=-`. Then, you must redeploy your Cloud Run service using the Golden Command to make it pick up the `latest` version of the secret.

### ERROR: "Container failed to start"

This means your application crashed instantly.
*   **Cause**: The most common cause is that your local `Dockerfile` still contains the line `ENV API_KEY=""`.
*   **Solution**: Open your local `Dockerfile`, delete that line, save the file, and re-run the Golden Command from Step 2.
