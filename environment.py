"""
Email Triage OpenEnv Environment
FastAPI server implementing the full OpenEnv spec:
  - GET  /tasks       → list all tasks
  - POST /reset       → reset to a task episode
  - POST /step        → agent takes an action
  - GET  /state       → current state
  - GET  /health      → health check (returns 200)
"""

import json
import random
import uuid
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from data import EMAILS, INBOX_SETS, EMAIL_MAP
from graders import grade_categorize, grade_prioritize, grade_reply

app = FastAPI(
    title="Email Triage OpenEnv",
    description="A real-world email triage environment for AI agents.",
    version="1.0.0"
)

# ── In-memory session store ─────────────────────────────────────────────────
sessions: dict[str, dict] = {}


# ── Pydantic Models ─────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str
    session_id: Optional[str] = None
    seed: Optional[int] = None

class StepRequest(BaseModel):
    session_id: str
    action: dict[str, Any]

class TaskInfo(BaseModel):
    id: str
    name: str
    difficulty: str
    description: str
    reward_range: list[float]


# ── Helpers ─────────────────────────────────────────────────────────────────

def _pick_email_for_task(task_id: str, seed: Optional[int]) -> dict:
    rng = random.Random(seed)
    if task_id == "categorize_email":
        return rng.choice(EMAILS)
    elif task_id == "prioritize_inbox":
        return rng.choice(INBOX_SETS)
    elif task_id == "draft_reply":
        # Only emails that have reply criteria
        from data import REPLY_CRITERIA
        eligible = [e for e in EMAILS if e["id"] in REPLY_CRITERIA]
        return rng.choice(eligible)
    raise ValueError(f"Unknown task_id: {task_id}")


def _build_observation(task_id: str, data: dict) -> dict:
    if task_id == "categorize_email":
        return {
            "task": "categorize_email",
            "instruction": "Classify this email into exactly one of: spam, billing, technical_support, general_inquiry, complaint, urgent",
            "email": {
                "id": data["id"],
                "subject": data["subject"],
                "sender": data["sender"],
                "body": data["body"],
                "timestamp": data["timestamp"]
            }
        }
    elif task_id == "prioritize_inbox":
        emails_in_inbox = [EMAIL_MAP[eid] for eid in data["emails"]]
        return {
            "task": "prioritize_inbox",
            "instruction": "Rank these 5 emails by priority. Return a list of email IDs ordered from highest priority (1st) to lowest (5th).",
            "inbox_id": data["id"],
            "emails": [
                {
                    "id": e["id"],
                    "subject": e["subject"],
                    "sender": e["sender"],
                    "body": e["body"][:200] + "..." if len(e["body"]) > 200 else e["body"],
                    "timestamp": e["timestamp"]
                }
                for e in emails_in_inbox
            ]
        }
    elif task_id == "draft_reply":
        return {
            "task": "draft_reply",
            "instruction": "Draft a professional reply to this email. Address all key points, maintain appropriate tone, and provide clear next steps or resolution.",
            "email": {
                "id": data["id"],
                "subject": data["subject"],
                "sender": data["sender"],
                "body": data["body"],
                "timestamp": data["timestamp"],
                "category": data["true_category"]
            }
        }


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "environment": "email-triage-env"}

@app.get("/")
def root():
    return {"status": "ok", "environment": "email-triage-env", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {
                "id": "categorize_email",
                "name": "Categorize Email",
                "difficulty": "easy",
                "description": "Classify a given email into the correct category.",
                "reward_range": [0.0, 1.0]
            },
            {
                "id": "prioritize_inbox",
                "name": "Prioritize Inbox",
                "difficulty": "medium",
                "description": "Rank 5 emails by priority from most to least urgent.",
                "reward_range": [0.0, 1.0]
            },
            {
                "id": "draft_reply",
                "name": "Draft Email Reply",
                "difficulty": "hard",
                "description": "Draft a professional reply that addresses the email's key concerns.",
                "reward_range": [0.0, 1.0]
            }
        ]
    }


@app.post("/reset")
def reset(req: ResetRequest):
    valid_tasks = ["categorize_email", "prioritize_inbox", "draft_reply"]
    if req.task_id not in valid_tasks:
        raise HTTPException(status_code=400, detail=f"Invalid task_id. Must be one of: {valid_tasks}")

    session_id = req.session_id or str(uuid.uuid4())
    data = _pick_email_for_task(req.task_id, req.seed)
    observation = _build_observation(req.task_id, data)

    sessions[session_id] = {
        "session_id": session_id,
        "task_id": req.task_id,
        "data": data,
        "observation": observation,
        "step_count": 0,
        "done": False,
        "last_reward": None,
        "last_feedback": None
    }

    return {
        "session_id": session_id,
        "task_id": req.task_id,
        "observation": observation,
        "done": False,
        "step": 0
    }


@app.post("/step")
def step(req: StepRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")
    if session["done"]:
        raise HTTPException(status_code=400, detail="Episode is done. Call /reset to start a new episode.")

    task_id = session["task_id"]
    action = req.action
    data = session["data"]

    # Grade the action
    if task_id == "categorize_email":
        category = action.get("category", "")
        result = grade_categorize(data["id"], category)

    elif task_id == "prioritize_inbox":
        order = action.get("priority_order", [])
        result = grade_prioritize(data["id"], order)

    elif task_id == "draft_reply":
        reply = action.get("reply", "")
        result = grade_reply(data["id"], reply)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown task_id: {task_id}")

    session["step_count"] += 1
    session["done"] = True  # single-step episodes
    session["last_reward"] = result["reward"]
    session["last_feedback"] = result["feedback"]

    return {
        "session_id": req.session_id,
        "task_id": task_id,
        "action": action,
        "reward": result["reward"],
        "feedback": result["feedback"],
        "done": True,
        "step": session["step_count"]
    }


@app.get("/state")
def state(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "session_id": session_id,
        "task_id": session["task_id"],
        "observation": session["observation"],
        "step_count": session["step_count"],
        "done": session["done"],
        "last_reward": session["last_reward"],
        "last_feedback": session["last_feedback"]
    }
