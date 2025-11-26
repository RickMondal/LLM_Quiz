from __future__ import annotations
import asyncio
import time
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .models import QuizRequest, AcceptResponse, ErrorResponse
from .solver.quiz_solver import QuizSolver

app = FastAPI(title="LLM Analysis Quiz Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/api/quiz", response_model=AcceptResponse, responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def quiz_endpoint(payload: QuizRequest, background_tasks: BackgroundTasks):
    settings = get_settings()
    # Validation
    if not payload.secret:
        raise HTTPException(status_code=400, detail="Missing secret")
    if payload.secret != settings.secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Offload work to background so we can return 200 immediately
    if not settings.disable_solver:
        background_tasks.add_task(run_solver, str(payload.url), settings.email, settings.secret)
    return AcceptResponse(status="accepted", message="Solving started")


async def run_solver(start_url: str, email: str, secret: str) -> None:
    deadline = time.time() + 180.0  # 3 minutes
    solver = QuizSolver(email=email, secret=secret, timeout=45.0)
    try:
        await solver.solve_quiz_chain(start_url, deadline)
    finally:
        await solver.close()
