# NEXUS Deployment Guide

This document provides complete instructions for containerized local execution, multi-container Docker Compose orchestration, and production deployments on Google Cloud Run using Artifact Registry and Cloud Build.

---

## 1. Local Containerized Setup

You can build and run individual components of the NEXUS platform using Docker.

### 1.1 Backend Container
Build and run the FastAPI backend:
```bash
# Build the backend container from the backend directory
cd backend
docker build -t nexus-backend .
cd ..

# Run the backend container on port 8000
docker run -d -p 8000:8080 --name nexus-api \
  -e GEMINI_API_KEY="your_api_key_here" \
  -e PRIMARY_AI_PROVIDER="gemini" \
  -e LOG_LEVEL="INFO" \
  -e APP_ENV="production" \
  nexus-backend
```
-   **Note:** The backend automatically checks if `nexus.db` is missing or empty on startup. If so, it seeds the 33-node network baseline automatically.

### 1.2 Frontend Container
Build and run the static Vite frontend:
```bash
# Build the frontend container using Node builder and Nginx runtime
docker build -t nexus-frontend \
  --build-arg VITE_API_URL="http://localhost:8000/api" \
  -f frontend/Dockerfile ./frontend

# Run the frontend container on port 8080
docker run -d -p 8080:8080 --name nexus-ui nexus-frontend
```

---

## 2. Multi-Container Orchestration (Docker Compose)

Docker Compose allows you to spin up the entire integrated ecosystem (frontend and backend) locally in production configuration.

### 2.1 Start Orchestration
From the root directory, run:
```bash
docker compose up --build -d
```

### 2.2 Verify Local Execution Ports
-   **Frontend Console:** Available at `http://localhost:8080`
-   **Backend API Documentation:** Available at `http://localhost:8000/docs`
-   **Local AI Fallback Route:** Configured to map `host.docker.internal` so the containerized backend can query an Ollama instance running natively on the host machine.

---

## 3. Google Cloud Run Deployment

Google Cloud Run provides a serverless execution environment for containerized services. Follow these steps to build and deploy NEXUS.

### 3.1 Setup Artifact Registry
Create repositories for the frontend and backend Docker images:
```bash
# Set variables
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

# Create registry repository for backend
gcloud artifacts repositories create nexus-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="NEXUS Docker Registry"
```

### 3.2 Build and Push Images using Cloud Build
Use Cloud Build to build and push container images to your registry:
```bash
# Build backend image from the backend directory
cd backend
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/nexus-repo/backend:latest .
cd ..

# Build frontend image (specify backend URL build argument)
BACKEND_URL="https://nexus-backend-xxxxx-uc.a.run.app"
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/nexus-repo/frontend:latest \
    --config=cloudbuild-frontend.yaml \
    ./frontend
```
*(See section 3.5 for frontend build configurations)*

### 3.3 Deploy Backend to Cloud Run
Deploy the backend API service:
```bash
gcloud run deploy nexus-backend \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/nexus-repo/backend:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --set-env-vars="PRIMARY_AI_PROVIDER=gemini,GEMINI_API_KEY=your_api_key_here,APP_ENV=production,CORS_ORIGINS=https://nexus-frontend-xxxxx-uc.a.run.app"
```
Record the resulting **Service URL** of the backend (e.g., `https://nexus-backend-xxxxx-uc.a.run.app`).

### 3.4 Deploy Frontend to Cloud Run
Deploy the frontend static server:
```bash
gcloud run deploy nexus-frontend \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/nexus-repo/frontend:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated
```

### 3.5 Cloud Build Frontend Configuration
For building the frontend with the `VITE_API_URL` build argument via Cloud Build, use the following `cloudbuild-frontend.yaml` configuration:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '--build-arg', 'VITE_API_URL=https://nexus-backend-xxxxx-uc.a.run.app/api',
      '-t', 'us-central1-docker.pkg.dev/your-gcp-project-id/nexus-repo/frontend:latest',
      '-f', 'Dockerfile',
      '.'
    ]
images:
  - 'us-central1-docker.pkg.dev/your-gcp-project-id/nexus-repo/frontend:latest'
```

---

## 4. Production Environment Variables Reference

Configure these environment variables in the Cloud Run console under **Variables & Secrets**:

### 4.1 Backend Service Variables
-   **`GEMINI_API_KEY` (Required in Cloud):** Google Gemini API developer key.
-   **`PRIMARY_AI_PROVIDER` (Default: `gemini`):** Instructs the app to use Google Gemini for processing. Do not use `ollama` in Cloud Run.
-   **`APP_ENV` (Default: `production`):** Sets running mode.
-   **`LOG_LEVEL` (Default: `INFO`):** Controls logging verbosity.
-   **`CORS_ORIGINS`:** Production frontend Cloud Run URL (e.g., `https://nexus-frontend-xxxxx-uc.a.run.app`).

### 4.2 Frontend Build Variables
-   **`VITE_API_URL`:** Complete URL pointing to the deployed backend Cloud Run service, suffixing the `/api` route.

---

## 5. Revision Rollbacks

If a deployment revision contains a regression, you can rollback immediately to a previous healthy revision using the gcloud CLI:

```bash
# List all revisions for a service
gcloud run revisions list --service=nexus-backend --region=$REGION

# Route 100% of traffic back to a specific revision ID
gcloud run services update-traffic nexus-backend \
    --to-revisions=nexus-backend-00002-xyz=100 \
    --region=$REGION
```

---

## 6. Troubleshooting Deployment Issues

### 6.1 Database Verification
If you suspect the database failed to seed:
1. Check Cloud Run service log stream.
2. Search for the log: `[DATABASE] SQLite database file missing or empty at '...'. Seeding database automatically...`
3. Look for the completion confirmation: `[DATABASE] Database seeded successfully.`

### 6.2 CORS Outages
If nodes fail to render or news alert submissions return connection errors:
- Open browser developer tools (F12) and inspect Console warnings.
- If CORS errors appear, verify that the backend's `CORS_ORIGINS` environment variable matches the exact URL (including `https://` prefix, excluding trailing slash) of the frontend service.

### 6.3 Missing Gemini Key
If news alerts analyze indefinitely and return errors:
- Verify that `GEMINI_API_KEY` is correctly defined in the Cloud Run service variables.
- Ensure the key is active and has sufficient quota allocations.
