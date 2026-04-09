import random
import uuid
import os
import uvicorn

from typing import Any, Optional, Dict
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from data import EMAILS, INBOX_SETS, EMAIL_MAP
from graders import grade_categorize, grade_prioritize, grade_reply

app = FastAPI()

sessions = {}

TASKS = ["categorize_email", "prioritize_inbox", "draft_reply"]


def _build_observation(task_id: str, data: dict) -> dict:
    if task_id == "categorize_email":
        instruction = (
            "Classify this email into exactly one category: "
            "spam, billing, technical_support, general_inquiry, complaint, urgent."
        )
    elif task_id == "prioritize_inbox":
        instruction = "Rank the listed email IDs from highest to lowest priority."
    else:
        instruction = "Draft a professional email reply that addresses the sender's issue."

    return {
        "task": task_id,
        "instruction": instruction,
        "input": data,
    }


class ObservationModel(BaseModel):
    task: str
    instruction: str
    input: Dict[str, Any]


class ActionModel(BaseModel):
    category: Optional[str] = None
    priority_order: Optional[list[str]] = None
    reply: Optional[str] = None


class RewardModel(BaseModel):
    reward: float
    feedback: str


class ResetResponseModel(BaseModel):
    session_id: str
    task_id: str
    observation: ObservationModel
    done: bool
    step: int


class StateResponseModel(BaseModel):
    session_id: str
    task_id: str
    observation: ObservationModel
    done: bool
    step: int


class StepResponseModel(BaseModel):
    session_id: str
    task_id: str
    reward: float
    feedback: str
    observation: Optional[ObservationModel] = None
    done: bool
    step: int

class StepRequest(BaseModel):
    session_id: str
    action: ActionModel

# ---------- ROOT ----------
@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- TASKS ----------
@app.get("/tasks")
def list_tasks():
    return {"tasks": TASKS}


# ---------- STATE ----------
@app.get("/state", response_model=StateResponseModel)
def state(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "task_id": session["task_id"],
        "observation": _build_observation(session["task_id"], session["data"]),
        "done": session.get("done", False),
        "step": session.get("step", 0),
    }

# ---------- RESET ----------
@app.post("/reset", response_model=ResetResponseModel)
async def reset(request: Request):
    try:
        body = await request.json()
    except:
        body = {}

    task_id = body.get("task_id", "categorize_email")
    session_id = str(uuid.uuid4())

    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id '{task_id}'")

    if task_id == "categorize_email":
        data = random.choice(EMAILS)

    elif task_id == "prioritize_inbox":
        data = random.choice(INBOX_SETS)

    elif task_id == "draft_reply":
        from data import REPLY_CRITERIA
        eligible = [e for e in EMAILS if e["id"] in REPLY_CRITERIA]
        data = random.choice(eligible)

    sessions[session_id] = {
        "task_id": task_id,
        "data": data,
        "done": False,
        "step": 0,
    }

    return {
        "session_id": session_id,
        "task_id": task_id,
        "observation": _build_observation(task_id, data),
        "done": False,
        "step": 0
    }

# ---------- STEP ----------
@app.post("/step", response_model=StepResponseModel)
def step(req: StepRequest):
    session = sessions.get(req.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get("done"):
        raise HTTPException(status_code=400, detail="Episode already finished")

    task_id = session["task_id"]
    data = session["data"]
    action = req.action.model_dump(exclude_none=True)

    if task_id == "categorize_email":
        result = grade_categorize(data["id"], action.get("category", ""))

    elif task_id == "prioritize_inbox":
        result = grade_prioritize(data["id"], action.get("priority_order", []))

    elif task_id == "draft_reply":
        result = grade_reply(data["id"], action.get("reply", ""))

    else:
        raise HTTPException(status_code=400, detail="Invalid task")

    # ✅ UPDATE STEP COUNTER
    session["step"] = session.get("step", 0) + 1

    # ✅ MARK DONE
    session["done"] = True

    return {
        "session_id": req.session_id,   # optional but good
        "task_id": task_id,
        "reward": result["reward"],
        "feedback": result["feedback"],
        "observation": None,
        "done": True,
        "step": session["step"]         # 🔥 CRITICAL FIX
    }
# ---------- RUN SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)