# AgentFlow  
### Autonomous Decision Intelligence Agent (LangGraph + FastAPI + n8n)

AgentFlow is a multi-service agentic system that demonstrates autonomous reasoning, structured tool execution, and workflow automation in a production-style architecture.

This project combines:

- A model inference layer (FastAPI + local LLM)
- An agent reasoning layer (LangGraph)
- A workflow automation layer (n8n)
- A multi-container deployment strategy

The goal is to showcase end-to-end agent orchestration rather than a simple chat interface.

---

## Project Intent

AgentFlow is designed as a **Decision Intelligence Agent** for small business operations.

The system:

1. Accepts natural language input from a user.
2. Uses LangGraph to plan and reason through multi-step decisions.
3. Executes structured tools (e.g., database queries, analytics lookups, integrations).
4. Triggers external automations via n8n (Slack notifications, webhooks, scheduled workflows).
5. Logs tool execution and maintains conversational state.

This project demonstrates system-level thinking across AI inference, agent reasoning, automation, and deployment.

---

## Architecture Overview

### High-Level Flow

