# SYSTEM ARCHITECTURE

## Architecture Philosophy

The project follows a modular microservice-inspired architecture.

Every major capability is isolated into independent components.

Frontend and backend communicate through REST APIs.

The backend performs orchestration while AI and graph analytics remain independent modules.

---

# Frontend

Framework

React

Language

TypeScript

Styling

Tailwind CSS

Animations

Framer Motion

Graph Visualization

React Flow or Cytoscape.js

Charts

Recharts

Icons

Lucide React

---

Frontend Responsibilities

• Dashboard

• News input

• Graph visualization

• KPI cards

• Simulation controls

• Recommendation panel

• Executive summary

---

# Backend

Framework

FastAPI

Language

Python 3.12+

Responsibilities

• API layer

• Gemini integration

• Dataset loading

• Graph analytics

• Simulation engine

• Recommendation engine

---

# AI Layer

Model

Google Gemini

Responsibilities

Extract structured information from unstructured news.

Expected JSON

{
"event": "...",
"location": "...",
"severity": "...",
"duration": "...",
"confidence": 0.98
}

---

# Data Layer

Hackathon

Local JSON

SQLite

Production

Google BigQuery

Data includes

Suppliers

Factories

Ports

Products

Warehouses

Shipping Routes

Bills of Materials

---

# Graph Engine

Preferred

NetworkX for development

RAPIDS cuGraph for GPU acceleration

Graph Nodes

Supplier

Factory

Warehouse

Port

Distribution Center

Product

Graph Edges

supplies

ships_to

depends_on

manufactures

stores

imports

exports

---

# Simulation Engine

Responsibilities

Receive disruption event

Locate affected node

Reduce or remove connectivity

Recalculate impact

Estimate affected downstream entities

Generate KPIs

---

# Recommendation Engine

Input

Graph analysis results

Business rules

LLM reasoning

Output

Alternative supplier

Estimated delay

Estimated cost

Confidence score

Suggested actions

---

# Dashboard Components

Navigation

Executive KPIs

Graph

Timeline

Risk Heatmap

Recommendation Panel

Terminal Animation

Scenario Simulator

---

# API Endpoints

POST /analyze-news

POST /simulate

GET /graph

GET /kpis

GET /recommendations

GET /timeline

---

# Development Priorities

Priority 1

End-to-end workflow

Priority 2

Graph visualization

Priority 3

Simulation

Priority 4

Performance optimization

Priority 5

GPU integration

Priority 6

Production cloud deployment

Every module should remain independently replaceable.
