# Lore Lens

Lore Lens is a knowledge and lore management platform for books, games,
and future media like films and research papers.

## Problem Statement

When reading books or playing narrative-heavy games, key events, characters, and relationships are easy to forget or misremember. Existing tools don’t provide a structured, searchable way to capture and revisit this knowledge over time.

## Tech Stack
- Frontend: React + TypeScript
- Backend: FastAPI
- DB: PostgreSQL

## Core User Flow

1. User creates an account
2. User creates a work (book or game)
3. User adds knowledge entities to the work
4. User views entities grouped by work

## Running the App
- To run the app enter command in main /lore-lens cirectory

```bash
docker compose up --build 
```

you can then see the backend hosted at http://0.0.0.0:8080