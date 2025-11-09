
# Vibe Node(r): Backend Deployment Guide for Google Cloud Run

This guide provides the definitive, most reliable method to deploy your Python backend to Google Cloud Run.

## Final Deployment Checklist (Start Here)

There are two reliable ways to deploy. **Method A is recommended as it is the most direct.**

### Method A: Deploy from Your Local Machine (Recommended)

This method builds the code directly from your computer, bypassing any potential GitHub cache issues.

1.  **Verify Your Local `Dockerfile`**: Open the `Dockerfile` in your local project folder. **Confirm that it does NOT contain the line `ENV API_KEY=""`.**
2.  **Run The Golden Command**: Navigate your terminal to the directory containing your backend files and run this single command. Replace `[YOUR_PROJECT_ID]` with your actual project ID.

    ```bash
    # Build from your local source and deploy the service
    gcloud run deploy vibe-node-r \
        --source . \
        --platform managed \
        --region europe-west4 \
        --allow-unauthenticated \
        --set-env-vars="API_KEY=SECRET:gemini-api-key:latest"
    ```

### Method B: Deploy from GitHub (UI-Based)

This method uses the automatic build trigger from your Cloud Run service. It requires the `cloudbuild.yaml` file to be in your repository.

1.  **Verify Your GitHub `Dockerfile`**: Go to your GitHub repository and open the `Dockerfile`. **Confirm that it does NOT contain the line `ENV API_KEY=""`.**
2.  **Verify `cloudbuild.yaml`**: Ensure the `cloudbuild.yaml` file exists in your repository.
3.  **Push to GitHub**: Commit and push your latest changes (including the `cloudbuild.yaml` file) to your main branch. This will automatically trigger a new build and deployment in Cloud Run.

---

## Initial Setup & Troubleshooting

### Initial Setup (If Not Already Done)

1.  **Authenticate gcloud**: `gcloud auth login`
2.  **Set Project**: `gcloud config set project [YOUR_PROJECT_ID]`
3.  **Enable APIs**: `gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com`
4.  **Create Secret**:
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

### Verifying the Live Service in the UI

If your deployment fails or the running application gives an `API_KEY not set` error, inspect the live service directly in the Google Cloud Console.

1.  **Find Service Identity**: Go to **Cloud Run > vibe-node-r > Security** tab. Copy the **Service account** email.
2.  **Verify Secret is Mounted**: Go to **Revisions** tab > Click latest revision > **Variables & Secrets** tab. You **MUST** see a variable named `API_KEY` that references the secret `gemini-api-key`. If not, your deployment command was missing the `--set-env-vars` flag. Re-run the Golden Command from Method A.
3.  **Verify IAM Permission**: Go to **IAM & Admin > IAM**. Ensure the service account from Step 1 has the **`Secret Manager Secret Accessor`** role. If not, grant it and then redeploy.
