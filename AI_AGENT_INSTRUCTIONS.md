# AI AGENT INSTRUCTIONS

You are contributing to the NEXUS project.

Act as a senior software engineer and system architect.

Your objective is to produce production-quality code, not placeholder code.

## Engineering Principles

* Use clean architecture.
* Prefer modular components over monolithic files.
* Write maintainable, typed, and documented code.
* Follow SOLID principles where appropriate.
* Avoid code duplication.
* Design for scalability.
* Separate UI, business logic, AI orchestration, and graph computation.
* Prefer composition over inheritance.

## Frontend Guidelines

* React + TypeScript.
* Tailwind CSS for styling.
* Framer Motion for polished animations.
* Responsive layouts.
* Accessible components.
* Modern enterprise dashboard aesthetics.
* Avoid unnecessary dependencies.

## Backend Guidelines

* FastAPI.
* Pydantic models.
* Async endpoints where beneficial.
* Clear folder structure.
* Environment variables for secrets.
* Comprehensive error handling.
* Logging for major operations.

## Graph Layer

Use NetworkX for development.

Design abstractions so RAPIDS cuGraph can replace NetworkX with minimal code changes.

Do not tightly couple business logic to a specific graph library.

## AI Layer

All LLM interactions should return structured JSON.

Avoid parsing free-form responses whenever possible.

Validate all AI outputs before using them.

## UI Expectations

The application should feel like enterprise software rather than a hackathon prototype.

Prioritize:

* smooth animations
* intuitive interactions
* clean typography
* meaningful loading states
* polished visual hierarchy

## Code Quality

Generate complete implementations.

Do not leave TODOs unless explicitly requested.

Avoid mock code if a working implementation is feasible.

Prefer reusable hooks, services, and utility modules.

Keep functions focused and concise.

## Repository Structure

frontend/
backend/
shared/
docs/
scripts/
data/

Maintain a clean separation of concerns.

## Overall Objective

Deliver an end-to-end application that demonstrates:

1. AI event understanding
2. Graph-based impact analysis
3. Decision intelligence
4. Executive visualization
5. GPU-ready architecture

Every implementation decision should strengthen these five pillars.
