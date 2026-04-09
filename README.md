---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

# 📧 Email Triage OpenEnv Environment

A real-world **email triage environment** built on the [OpenEnv](https://github.com/openenv/openenv) framework.  
An AI agent learns to categorize, prioritize, and draft replies to emails — simulating a professional inbox management workflow.

---

## 🌍 Environment Description


## 🎯 Tasks

### 1. `categorize_email` — Easy
Given a single email, classify it into one of:  
`spam` · `billing` · `technical_support` · `general_inquiry` · `complaint` · `urgent`

**Reward:** `1.0` exact match, `0.3–0.4` partial credit for related categories, `0.0` incorrect.

---

### 2. `prioritize_inbox` — Medium
Given an inbox of **5 emails**, rank them by priority from highest (1st) to lowest (5th).

**Reward:** Normalized Kendall Tau distance between predicted and true ranking.  
Perfect order → `1.0` | Completely reversed → `0.0`

---

### 3. `draft_reply` — Hard
Given an email and its category, draft a **professional reply** addressing all key concerns.

**Reward:** Composite score based on:
- Reply length & completeness (0.2)
- Keyword coverage for the specific issue (0.4)
- Professional tone markers (0.2)
- Issue acknowledgment (0.2)

---

## 📐 Observation Space

Each observation is a JSON object:

```json
{
  "task": "categorize_email",
  "instruction": "Classify this email into exactly one of: ...",
  "input": {
    "id": "e001",
    "subject": "URGENT: Server down in production",
    "sender": "ops-team@company.com",
    "body": "Our main production server has been down...",
    "timestamp": "2024-01-15T09:00:00Z"
  }
}
```

---

## 🕹️ Action Space

Actions are task-specific JSON objects:

```json
// categorize_email
{ "category": "urgent" }

// prioritize_inbox
{ "priority_order": ["e001", "e002", "e004", "e005", "e003"] }

// draft_reply
{ "reply": "Dear Customer, thank you for reaching out..." }
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step` | Agent takes an action |
| `GET` | `/state?session_id=...` | Get current state |

### Reset
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "categorize_email"}'
```

### Step
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<session_id>", "action": {"category": "urgent"}}'
```

---

## ⚙️ Setup & Run Locally

### Prerequisites
- Python 3.10+
- Docker (optional)

### Install & Run
```bash
git clone <your-repo>
cd email-triage-env

pip install -r requirements.txt
uvicorn environment:app --host 0.0.0.0 --port 7860
```

### Docker
```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

---

## 🤖 Running Inference

Set your environment variables:
```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-hf-or-openai-token"
export ENV_URL="http://localhost:7860"

python inference.py
```

### Pre-Submission Validation (Fast)

Run these checks before submitting:

```bash
# 1) Start environment
uvicorn environment:app --host 0.0.0.0 --port 7860

# 2) Validate endpoints/tasks/reward ranges
python prevalidate.py

# 3) Validate inference format and end-to-end run
python inference.py
```

Docker parity check:

```bash
docker build -t email-triage-env .
docker run --rm -p 7860:7860 email-triage-env

# In another terminal:
export ENV_URL="http://localhost:7860"
python prevalidate.py
python inference.py
```

---

## 📊 Expected Baseline Scores

| Task | Difficulty | Expected Reward |
|---|---|---|
| categorize_email | Easy | 0.8 – 1.0 |
| prioritize_inbox | Medium | 0.6 – 0.85 |
| draft_reply | Hard | 0.5 – 0.75 |

---

## 🔧 Environment Variables

| Variable | Description |
|---|---|
| `API_BASE_URL` | LLM API endpoint |
| `MODEL_NAME` | Model identifier for inference |
| `HF_TOKEN` | Hugging Face / API key |
| `ENV_URL` | URL of the deployed environment (default: `http://localhost:7860`) |

---

## 📁 Project Structure

```
email-triage-env/
├── environment.py      # FastAPI server (OpenEnv spec)
├── graders.py          # Task grading logic
├── data.py             # Email dataset
├── inference.py        # Baseline agent script
├── openenv.yaml        # Environment specification
├── requirements.txt
├── Dockerfile
└── README.md
```
