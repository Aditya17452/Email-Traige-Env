"""
Email dataset for the Email Triage Environment.
Contains sample emails for categorization, prioritization, and reply drafting.
"""

EMAILS = [
    {
        "id": "e001",
        "subject": "URGENT: Server down in production",
        "sender": "ops-team@company.com",
        "sender_type": "internal",
        "body": "Our main production server has been down for 30 minutes. Customers cannot access the platform. We need immediate assistance from the technical team. Revenue impact is estimated at $10k/hour.",
        "timestamp": "2024-01-15T09:00:00Z",
        "true_category": "urgent",
        "true_priority": 1
    },
    {
        "id": "e002",
        "subject": "Invoice #4521 - Payment overdue",
        "sender": "billing@vendor.com",
        "sender_type": "external",
        "body": "Dear Customer, your invoice #4521 for $2,450 is now 30 days overdue. Please arrange payment at your earliest convenience to avoid service interruption. Contact our billing department if you have questions.",
        "timestamp": "2024-01-15T08:30:00Z",
        "true_category": "billing",
        "true_priority": 2
    },
    {
        "id": "e003",
        "subject": "Congratulations! You've won a prize",
        "sender": "noreply@prizes-winner.net",
        "sender_type": "unknown",
        "body": "You have been selected as our lucky winner! Click here to claim your $1,000,000 prize. Limited time offer. Provide your bank details to receive your winnings immediately.",
        "timestamp": "2024-01-15T08:00:00Z",
        "true_category": "spam",
        "true_priority": 5
    },
    {
        "id": "e004",
        "subject": "Question about your return policy",
        "sender": "customer123@gmail.com",
        "sender_type": "customer",
        "body": "Hi, I purchased a laptop from your store 2 weeks ago and it's not working properly. The screen flickers randomly. I'd like to know what your return/exchange policy is and how I can proceed with getting this fixed.",
        "timestamp": "2024-01-15T10:00:00Z",
        "true_category": "complaint",
        "true_priority": 3
    },
    {
        "id": "e005",
        "subject": "How do I reset my password?",
        "sender": "user456@email.com",
        "sender_type": "customer",
        "body": "Hello, I'm trying to log into my account but I forgot my password. The reset link I received isn't working. Can you help me regain access to my account? My username is user456.",
        "timestamp": "2024-01-15T09:30:00Z",
        "true_category": "technical_support",
        "true_priority": 4
    },
    {
        "id": "e006",
        "subject": "Partnership inquiry - Marketing collaboration",
        "sender": "partnerships@bigcorp.com",
        "sender_type": "external",
        "body": "Dear Team, we're a Fortune 500 company interested in exploring a marketing partnership with your organization. We believe there's strong synergy between our brands. Could we schedule a call to discuss potential collaboration opportunities?",
        "timestamp": "2024-01-15T11:00:00Z",
        "true_category": "general_inquiry",
        "true_priority": 4
    },
    {
        "id": "e007",
        "subject": "Data breach - Customer data may be compromised",
        "sender": "security@internal.com",
        "sender_type": "internal",
        "body": "CRITICAL ALERT: We have detected unauthorized access to our customer database. Approximately 50,000 customer records including emails and hashed passwords may have been accessed. We need immediate action from leadership and legal team.",
        "timestamp": "2024-01-15T07:00:00Z",
        "true_category": "urgent",
        "true_priority": 1
    },
    {
        "id": "e008",
        "subject": "Monthly newsletter - January edition",
        "sender": "newsletter@industry.com",
        "sender_type": "external",
        "body": "Welcome to our January newsletter! This month we cover: Top 10 industry trends, Interview with CEO of TechCorp, Upcoming webinars and events, Product spotlight. Hope you enjoy the read!",
        "timestamp": "2024-01-15T06:00:00Z",
        "true_category": "general_inquiry",
        "true_priority": 5
    }
]

# Inbox sets for the prioritization task (5 emails each)
INBOX_SETS = [
    {
        "id": "inbox_001",
        "emails": ["e001", "e002", "e003", "e004", "e005"],
        "true_priority_order": ["e001", "e002", "e004", "e005", "e003"]
    },
    {
        "id": "inbox_002",
        "emails": ["e007", "e004", "e008", "e002", "e006"],
        "true_priority_order": ["e007", "e002", "e004", "e006", "e008"]
    }
]

# Expected reply elements for grading
EMAIL_MAP = {e["id"]: e for e in EMAILS}

REPLY_CRITERIA = {
    "e004": {
        "required_elements": [
            "acknowledge the issue",
            "laptop screen",
            "return policy",
            "next steps",
            "apology or empathy"
        ],
        "tone": "professional_empathetic",
        "keywords": ["return", "exchange", "warranty", "sorry", "assist", "help", "process"]
    },
    "e005": {
        "required_elements": [
            "acknowledge the password issue",
            "provide solution steps",
            "alternative contact method",
            "closing"
        ],
        "tone": "professional_helpful",
        "keywords": ["password", "reset", "account", "access", "help", "support", "team"]
    },
    "e002": {
        "required_elements": [
            "acknowledge invoice",
            "payment options or timeline",
            "contact information",
            "professional closing"
        ],
        "tone": "professional_formal",
        "keywords": ["invoice", "payment", "billing", "overdue", "contact", "resolve"]
    }
}
