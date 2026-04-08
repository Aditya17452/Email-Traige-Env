"""
Graders for the Email Triage Environment.
Each grader returns a reward in [0.0, 1.0].
"""

from data import EMAILS, INBOX_SETS, REPLY_CRITERIA

EMAIL_MAP = {e["id"]: e for e in EMAILS}

VALID_CATEGORIES = ["spam", "billing", "technical_support", "general_inquiry", "complaint", "urgent"]

# ── Task 1: Categorize Email ────────────────────────────────────────────────

def grade_categorize(email_id: str, predicted_category: str) -> dict:
    """
    Grade the categorization of a single email.
    Exact match → 1.0
    Related category (partial credit) → 0.4
    Wrong → 0.0
    """
    email = EMAIL_MAP.get(email_id)
    if not email:
        return {"reward": 0.0, "feedback": f"Unknown email id: {email_id}"}

    pred = predicted_category.strip().lower().replace(" ", "_")
    true = email["true_category"]

    if pred == true:
        return {"reward": 1.0, "feedback": f"Correct! Category is '{true}'."}

    # Partial credit: related categories
    partial_credit_map = {
        ("urgent", "technical_support"): 0.4,
        ("urgent", "complaint"): 0.4,
        ("complaint", "general_inquiry"): 0.3,
        ("technical_support", "complaint"): 0.3,
        ("billing", "complaint"): 0.3,
    }
    pair = tuple(sorted([pred, true]))
    partial = partial_credit_map.get(pair, 0.0)

    if partial > 0:
        return {
            "reward": partial,
            "feedback": f"Partially correct. Predicted '{pred}', true is '{true}'. Related but not exact."
        }

    return {
        "reward": 0.0,
        "feedback": f"Incorrect. Predicted '{pred}', true is '{true}'."
    }


# ── Task 2: Prioritize Inbox ────────────────────────────────────────────────

def grade_prioritize(inbox_id: str, predicted_order: list) -> dict:
    """
    Grade inbox prioritization using normalized Kendall Tau distance.
    Perfect order → 1.0
    Completely reversed → 0.0
    Partial credit for partially correct orderings.
    """
    inbox = next((i for i in INBOX_SETS if i["id"] == inbox_id), None)
    if not inbox:
        return {"reward": 0.0, "feedback": f"Unknown inbox id: {inbox_id}"}

    true_order = inbox["true_priority_order"]
    n = len(true_order)

    if len(predicted_order) != n:
        return {
            "reward": 0.0,
            "feedback": f"Expected {n} email IDs in order, got {len(predicted_order)}."
        }

    # Check all IDs are valid
    if set(predicted_order) != set(true_order):
        return {
            "reward": 0.0,
            "feedback": f"Email IDs don't match. Expected: {true_order}"
        }

    # Kendall Tau: count concordant vs discordant pairs
    true_rank = {eid: i for i, eid in enumerate(true_order)}
    pred_rank = {eid: i for i, eid in enumerate(predicted_order)}

    concordant = 0
    discordant = 0
    total_pairs = n * (n - 1) / 2

    for i in range(n):
        for j in range(i + 1, n):
            ei, ej = true_order[i], true_order[j]
            true_rel = true_rank[ei] < true_rank[ej]  # ei before ej in truth
            pred_rel = pred_rank[ei] < pred_rank[ej]  # ei before ej in prediction
            if true_rel == pred_rel:
                concordant += 1
            else:
                discordant += 1

    tau = (concordant - discordant) / total_pairs  # range [-1, 1]
    reward = (tau + 1) / 2  # normalize to [0, 1]

    return {
        "reward": round(reward, 4),
        "feedback": f"Kendall Tau: {tau:.3f}. Reward: {reward:.3f}. True order: {true_order}"
    }


# ── Task 3: Draft Reply ─────────────────────────────────────────────────────

def grade_reply(email_id: str, reply_text: str) -> dict:
    """
    Grade the drafted reply.
    Scoring breakdown:
    - Length/completeness: 0.2
    - Keyword coverage: 0.4
    - Professional tone markers: 0.2
    - Addresses sender by acknowledging their issue: 0.2
    """
    if email_id not in REPLY_CRITERIA:
        # Generic grading for emails without specific criteria
        return _generic_reply_grade(reply_text)

    criteria = REPLY_CRITERIA[email_id]
    reply_lower = reply_text.lower()
    score = 0.0
    feedback_parts = []

    # 1. Length/completeness (0.2) — at least 50 words
    word_count = len(reply_text.split())
    if word_count >= 100:
        score += 0.2
        feedback_parts.append("✓ Reply is sufficiently detailed")
    elif word_count >= 50:
        score += 0.1
        feedback_parts.append("~ Reply is somewhat brief")
    else:
        feedback_parts.append("✗ Reply is too short (< 50 words)")

    # 2. Keyword coverage (0.4)
    keywords = criteria["keywords"]
    matched = [kw for kw in keywords if kw.lower() in reply_lower]
    keyword_score = (len(matched) / len(keywords)) * 0.4
    score += keyword_score
    feedback_parts.append(f"Keywords matched: {len(matched)}/{len(keywords)}: {matched}")

    # 3. Professional tone (0.2)
    tone_markers = ["dear", "sincerely", "regards", "thank you", "please", "we apologize",
                    "we're sorry", "happy to help", "feel free", "best regards", "kind regards"]
    tone_hits = sum(1 for t in tone_markers if t in reply_lower)
    tone_score = min(tone_hits / 3, 1.0) * 0.2
    score += tone_score
    if tone_hits >= 2:
        feedback_parts.append("✓ Professional tone detected")
    else:
        feedback_parts.append("✗ Tone could be more professional")

    # 4. Acknowledges the issue (0.2)
    issue_keywords = criteria.get("required_elements", [])
    issue_hit = any(word in reply_lower for elem in issue_keywords for word in elem.split())
    if issue_hit:
        score += 0.2
        feedback_parts.append("✓ Acknowledges the issue")
    else:
        feedback_parts.append("✗ Does not clearly acknowledge the issue")

    return {
        "reward": round(min(score, 1.0), 4),
        "feedback": " | ".join(feedback_parts)
    }


def _generic_reply_grade(reply_text: str) -> dict:
    """Fallback grader for emails without specific criteria."""
    reply_lower = reply_text.lower()
    score = 0.0

    word_count = len(reply_text.split())
    if word_count >= 80:
        score += 0.3
    elif word_count >= 40:
        score += 0.15

    tone_markers = ["dear", "sincerely", "regards", "thank you", "please", "happy to help"]
    if any(t in reply_lower for t in tone_markers):
        score += 0.4

    if any(w in reply_lower for w in ["will", "can", "shall", "assist", "help", "resolve"]):
        score += 0.3

    return {"reward": round(min(score, 1.0), 4), "feedback": "Generic grading applied."}
