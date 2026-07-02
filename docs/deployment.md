# System Deployment Guide

This document outlines instructions for local setup, environment configuration, database seeding, and production cloud deployment strategies for the NEXUS platform.

---

## 1. Local Environment Requirements

### 1.1 Backend Prerequisites
-   Python 3.11 or higher
-   Pip package manager
-   Virtualenv tool

### 1.2 Frontend Prerequisites
-   Node.js (LTS version 18 or 20 recommended)
-   npm package manager

### 1.3 Local AI Prerequisites (Optional)
-   Ollama installed locally
-   Mistral model pulled: `ollama pull mistral`

---

## 2. Environment Variables Configuration

Create a `.env` file in the `backend/` directory to configure services:

| Variable Name | Required | Default Value | Purpose / Description |
| :--- | :--- | :--- | :--- |
| `PRIMARY_AI_PROVIDER` | No | `gemini` | Primary engine for extraction and briefings (`gemini`, `ollama`, or `mock`). |
| `FALLBACK_AI_PROVIDER`| No | `ollama` | Fallback engine if primary is unreachable. |
| `GEMINI_API_KEY` | No | None | Cloud credentials for Google Gemini API. |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Endpoint for local Ollama server. |
| `OLLAMA_MODEL` | No | `mistral` | LLM tag used by Ollama. |
| `DB_PATH` | No | `backend/nexus.db` | Absolute or relative path to SQLite database. |

---

## 3. Step-by-Step Installation

### 3.1 Initialize Backend Service
```bash
# Clone the repository
git clone https://github.com/your-repo/nexus.git
cd nexus/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations and seed baseline network
python scripts/seed_db.py
```

### 3.2 Initialize Frontend Service
```bash
cd ../frontend
npm install
```

---

## 4. Local Execution Commands

### 4.1 Start the Backend REST Server
```bash
cd backend
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```
-   Swagger Interactive API Documentation: `http://localhost:8000/docs`
-   ReDoc static references: `http://localhost:8000/redoc`

### 4.2 Start the React UI Client
```bash
cd frontend
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 5. Production Cloud Deployment Strategy

To deploy NEXUS in a production cloud environment, we recommend the following Google Cloud Platform (GCP) target architecture:

### 5.1 Backend Deployment (Google Cloud Run)
FastAPI backend can be packaged as a Docker container and deployed serverless using **Google Cloud Run**:
-   **Execution:** Containerized execution with autoscaling.
-   **Security:** Private VPC connector to interface with databases.
-   **Artifact Registry:** Used to store container builds.

### 5.2 Database Layer (Google Cloud SQL)
For production scalability, replace the local SQLite file with a managed **Google Cloud SQL for PostgreSQL** instance. 
-   Replace the `SQLiteRepository` with a PostgreSQL connection pool adapter.
-   Run database migrations using tools like Alembic.

### 5.3 AI Layer (Vertex AI / Gemini API)
In production, lock Vertex AI with Google Enterprise credentials:
-   Configure Service Account credentials.
-   Direct requests to Google Vertex AI endpoints instead of standard developer SDK keys.

### 5.4 Frontend Deployment (Firebase Hosting / Cloud Storage CDN)
The compiled static assets (`frontend/dist`) can be hosted serverless on:
-   **Google Cloud Storage (GCS)** configured as a public website behind a Cloud Load Balancer.
-   **Firebase Hosting** for global CDN delivery.
