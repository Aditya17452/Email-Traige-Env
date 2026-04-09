"""
Quick pre-submission validator for the Email Triage OpenEnv project.

Checks:
- /health returns 200
- /reset, /state, /step work for all tasks
- step reward is within [0.0, 1.0]
"""

import os
import sys
from typing import Any

import requests


ENV_URL = os.getenv("ENV_URL", "http://localhost:7860").rstrip("/")
TIMEOUT = 30
TASKS = ["categorize_email", "prioritize_inbox", "draft_reply"]


def _extract_input_payload(observation: dict[str, Any]) -> dict[str, Any]:
    if isinstance(observation, dict) and isinstance(observation.get("input"), dict):
        return observation["input"]
    return observation if isinstance(observation, dict) else {}


def _sample_action(task_id: str, observation: dict[str, Any]) -> dict[str, Any]:
    payload = _extract_input_payload(observation)

    if task_id == "categorize_email":
        text = f"{payload.get('subject', '')} {payload.get('body', '')}".lower()
        if any(k in text for k in ["urgent", "critical", "server down", "breach"]):
            return {"category": "urgent"}
        if any(k in text for k in ["invoice", "payment", "billing", "overdue"]):
            return {"category": "billing"}
        if any(k in text for k in ["password", "reset", "login", "access"]):
            return {"category": "technical_support"}
        if any(k in text for k in ["return", "exchange", "flicker", "complaint"]):
            return {"category": "complaint"}
        if any(k in text for k in ["prize", "winner", "bank details", "click here"]):
            return {"category": "spam"}
        return {"category": "general_inquiry"}

    if task_id == "prioritize_inbox":
        email_ids = payload.get("emails", [])
        if not isinstance(email_ids, list):
            email_ids = []
        ranked = sorted(email_ids, key=lambda eid: (eid not in ["e001", "e007"], eid))
        return {"priority_order": ranked}

    return {
        "reply": (
            "Dear Customer, thank you for your email. We understand the issue and apologize "
            "for the inconvenience. Our support team will assist you with the next steps and "
            "provide a resolution as quickly as possible. Please share any additional details "
            "if needed. Kind regards, Support Team."
        )
    }


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        print(f"[OK] {message}")
    else:
        print(f"[FAIL] {message}")
        failures.append(message)


def main() -> int:
    failures: list[str] = []

    try:
        health = requests.get(f"{ENV_URL}/health", timeout=TIMEOUT)
        _require(health.status_code == 200, "/health returns 200", failures)
    except Exception as exc:
        print(f"[FAIL] health check error: {exc}")
        return 1

    for task_id in TASKS:
        try:
            reset_resp = requests.post(
                f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=TIMEOUT
            )
            _require(reset_resp.status_code == 200, f"/reset works for {task_id}", failures)
            if reset_resp.status_code != 200:
                continue

            reset_data = reset_resp.json()
            session_id = reset_data.get("session_id")
            observation = reset_data.get("observation", {})
            _require(bool(session_id), f"session_id returned for {task_id}", failures)

            state_resp = requests.get(
                f"{ENV_URL}/state", params={"session_id": session_id}, timeout=TIMEOUT
            )
            _require(state_resp.status_code == 200, f"/state works for {task_id}", failures)

            action = _sample_action(task_id, observation)
            step_resp = requests.post(
                f"{ENV_URL}/step",
                json={"session_id": session_id, "action": action},
                timeout=TIMEOUT,
            )
            _require(step_resp.status_code == 200, f"/step works for {task_id}", failures)
            if step_resp.status_code != 200:
                continue

            step_data = step_resp.json()
            reward = step_data.get("reward")
            done = step_data.get("done")
            in_range = isinstance(reward, (int, float)) and 0.0 <= float(reward) <= 1.0
            _require(in_range, f"reward in [0,1] for {task_id}", failures)
            _require(isinstance(done, bool), f"done is bool for {task_id}", failures)

        except Exception as exc:
            failures.append(f"{task_id} execution error: {exc}")
            print(f"[FAIL] {task_id} execution error: {exc}")

    if failures:
        print("\nPre-validation FAILED")
        for issue in failures:
            print(f" - {issue}")
        return 1

    print("\nPre-validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
