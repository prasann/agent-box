"""Registry metadata used by the Mission Control API and dashboard."""

AGENT_MANIFESTS = [
    {
        "id": "text",
        "name": "Text",
        "description": "Fix grammar or rewrite pasted text with Azure OpenAI.",
        "icon": "Type",
        "actions": [
            {
                "id": "fix",
                "name": "Fix grammar",
                "description": "Correct grammar and typos while preserving style.",
                "destructive": False,
                "long_running": False,
                "inputs": [{"name": "text", "type": "textarea", "required": True}],
            },
            {
                "id": "rewrite",
                "name": "Rewrite",
                "description": "Rewrite text for clarity and professionalism.",
                "destructive": False,
                "long_running": False,
                "inputs": [{"name": "text", "type": "textarea", "required": True}],
            },
        ],
    },
    {
        "id": "library",
        "name": "Library",
        "description": "Browse agents, prompts, skills, instructions, and hooks.",
        "icon": "Library",
        "actions": [],
    },
    {
        "id": "shell",
        "name": "Shell",
        "description": "Preview a safe cleanup of your zsh history.",
        "icon": "Terminal",
        "actions": [
            {
                "id": "preview",
                "name": "Preview purge",
                "description": "Show cleanup impact without changing history.",
                "destructive": False,
                "long_running": False,
                "inputs": [],
            }
        ],
    },
]
