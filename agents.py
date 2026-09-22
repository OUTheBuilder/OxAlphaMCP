AGENTS = {
    "chat": {
        "name": "Chat",
        "icon": "💬",
        "template": "{text}"
    },
    "study": {
        "name": "Study Guide",
        "icon": "📚",
        "template": "Create a clear, structured study guide about:\n\n{text}\n\nUse headings, bullet points, key terms, and a short summary at the end."
    },
    "quiz": {
        "name": "Practice Quiz",
        "icon": "❓",
        "template": "Create 5 practice questions (with answers at the end) about:\n\n{text}"
    },
    "explain": {
        "name": "Explain Simply",
        "icon": "🧠",
        "template": "Explain this in the simplest possible terms, using an analogy:\n\n{text}"
    },
    "summary": {
        "name": "Summarize",
        "icon": "📝",
        "template": "Summarize the following in 5 bullet points:\n\n{text}"
    },
    "code": {
        "name": "Code Helper",
        "icon": "💻",
        "template": "Help with this code or coding task. Explain clearly and give working code:\n\n{text}"
    },
    "ideas": {
        "name": "Idea Generator",
        "icon": "💡",
        "template": "Generate 10 creative, practical ideas about:\n\n{text}\n\nNumber them and add one-line explanations."
    },
    "team": {
        "name": "Team Mode",
        "icon": "👥",
        "template": (
            "Simulate a team of three experts (an Analyst, a Creative, and a Critic) "
            "discussing the following topic. Show each perspective, then give a final "
            "combined recommendation.\n\nTopic: {text}"
        )
    },
}

PROVIDERS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_hint": "sk-or-..."
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_hint": "gsk_..."
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "key_hint": "AIza..."
    },
}

def build_prompt(agent_key: str, text: str) -> str:
    agent = AGENTS.get(agent_key, AGENTS["chat"])
    return agent["template"].format(text=text)
