# Resume Analyser

A full-stack monorepo scaffold for analysing resumes against job descriptions. The backend uses FastAPI with MongoDB, and the frontend uses Next.js App Router, TypeScript, and Tailwind CSS.

## Backend setup

1. Change to `backend`.
2. Create and activate a Python virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and supply MongoDB and JWT values.
5. Run the API with `fastapi dev main.py`.

The API will be available at `http://localhost:8000`.

## Frontend setup

1. Change to `frontend`.
2. Install dependencies with `npm install`.
3. Start the development server with `npm run dev`.

The frontend will be available at `http://localhost:3000`.
