"""
Baseline Inference Script for Email Triage OpenEnv Environment.
Uses OpenAI-compatible client to interact with the environment.

Required env vars:
  API_BASE_URL  - LLM API endpoint
  MODEL_NAME    - model identifier
  HF_TOKEN      - Hugging Face / API key

Emits structured logs in [START] / [STEP] / [END] format.
"""

import os
import json
import time
import requests
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")
ENV_URL      = os.environ.get("ENV_URL", "http://localhost:7860")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or "no-key"
)

TASKS = [
    "categorize_email",
    "prioritize_inbox",
    "draft_reply"
]

# ── LLM Agent Prompts ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert email triage assistant. 
You will receive email data and must respond ONLY with valid JSON — no explanation, no markdown.

For categorize_email: respond with {"category": "<one of: spam, billing, technical_support, general_inquiry, complaint, urgent>"}

For prioritize_inbox: respond with {"priority_order": ["<email_id_1>", "<email_id_2>", "<email_id_3>", "<email_id_4>", "<email_id_5>"]} ordered highest to lowest priority.

For draft_reply: respond with {"reply": "<your professional email reply here>"}
"""

def call_llm(observation: dict) -> dict:
    """Call the LLM with the current observation and return parsed action."""
    prompt = json.dumps(observation, indent=2)
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    
    return json.loads(content)


def run_task(task_id: str) -> dict:
    """Run one episode of a task and return the result."""
    
    # Reset environment
    reset_resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
    reset_resp.raise_for_status()
    reset_data = reset_resp.json()
    
    session_id  = reset_data["session_id"]
    observation = reset_data["observation"]
    
    print(json.dumps({
        "event": "[START]",
        "task_id": task_id,
        "session_id": session_id,
        "observation": observation
    }))
    
    # Agent takes action
    action = call_llm(observation)
    
    # Step in environment
    step_resp = requests.post(f"{ENV_URL}/step", json={
        "session_id": session_id,
        "action": action
    })
    step_resp.raise_for_status()
    step_data = step_resp.json()
    
    reward   = step_data["reward"]
    feedback = step_data["feedback"]
    done     = step_data["done"]
    
    print(json.dumps({
        "event": "[STEP]",
        "task_id": task_id,
        "session_id": session_id,
        "step": step_data["step"],
        "action": action,
        "reward": reward,
        "feedback": feedback,
        "done": done
    }))
    
    print(json.dumps({
        "event": "[END]",
        "task_id": task_id,
        "session_id": session_id,
        "total_reward": reward,
        "steps": step_data["step"],
        "done": done
    }))
    
    return {
        "task_id": task_id,
        "reward": reward,
        "feedback": feedback
    }


def main():
    print(json.dumps({"event": "[INFO]", "message": "Starting Email Triage baseline inference", "env_url": ENV_URL}))
    
    results = []
    for task_id in TASKS:
        print(json.dumps({"event": "[INFO]", "message": f"Running task: {task_id}"}))
        try:
            result = run_task(task_id)
            results.append(result)
        except Exception as e:
            print(json.dumps({"event": "[ERROR]", "task_id": task_id, "error": str(e)}))
            results.append({"task_id": task_id, "reward": 0.0, "error": str(e)})
        
        time.sleep(1)  # Rate limit buffer
    
    # Summary
    total = sum(r["reward"] for r in results)
    avg   = total / len(results) if results else 0
    
    print(json.dumps({
        "event": "[SUMMARY]",
        "results": results,
        "average_reward": round(avg, 4),
        "total_reward": round(total, 4),
        "tasks_completed": len(results)
    }))
    
    return results


if __name__ == "__main__":
    main()
