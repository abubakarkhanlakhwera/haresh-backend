# Haresh Backend

Python/FastAPI backend for an AI-assisted web application with image-analysis and agent-oriented service logic.

## Overview

This repository is the backend half of an AI-assisted product. It exposes Python API logic that can support a web frontend with AI responses, image-analysis workflows, and assistant-style interactions.

Live endpoint: [haresh-backend.vercel.app](https://haresh-backend.vercel.app)
Frontend: [haresh-frontend](https://github.com/abubakarkhanlakhwera/haresh-frontend)

## What This Shows

- FastAPI backend structure
- AI service integration through OpenAI-related packages
- Image-analysis service logic
- Deployment-oriented configuration with Vercel
- Backend/frontend separation for an AI product

## Tech Stack

- Python
- FastAPI and Starlette
- OpenAI / OpenAI Agents SDK packages
- Pydantic and pydantic-settings
- Uvicorn
- Vercel deployment config

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

Copy `.env.example` to `.env` and fill in local values.

```text
OPENAI_API_KEY=
ALLOWED_ORIGINS=
```

Never commit API keys, user uploads, private images, or production configuration.

## API Documentation

When running locally, FastAPI documentation is typically available at:

```text
http://localhost:8000/docs
```

## Roadmap

- Document each endpoint with request/response examples
- Add tests for API routes and AI service wrappers
- Add structured error handling and request validation docs
- Add rate-limit and privacy notes before production use
- Add deployment instructions for Vercel and local Docker

## Author

Muhammad AbuBakar Siddique
Portfolio: [abees.me](https://abees.me)
