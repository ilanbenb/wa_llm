# AI Agents & Project Architecture

**AI Assistant Context**: This project is developed using **GitHub Copilot** within **VS Code**. This file serves as the primary context source for the AI assistant regarding the project's architecture, agents, and structure.

---

## Project Structure

The project follows a modular architecture centered around `src/`.

```text
wa_llm/
├── app/                    # Application entry points
│   └── main.py             # FastAPI app initialization and wiring
├── migrations/             # Database migrations (Alembic)
├── notebooks/              # Jupyter notebooks for experiments
├── src/                    # Main source code
│   ├── api/                # API endpoints (FastAPI routers)
│   ├── config/             # Configuration management (Pydantic Settings)
│   ├── handler/            # Message handlers (Router, RAG, Spam, etc.)
│   ├── load_new_kbtopics/  # Logic for splitting chats and ingesting topics
│   ├── models/             # SQLModel database models and Pydantic schemas
│   ├── search/             # Vector search logic (Hybrid search implementation)
│   ├── services/           # Core business logic and external services
│   │   ├── local_model.py  # Local LLM implementation (Hugging Face)
│   │   └── prompt_manager.py # Jinja2 prompt rendering
│   ├── summarize_and_send_to_groups/ # Summarization logic
│   ├── templates/          # Jinja2 prompt templates (*.j2)
│   ├── test_utils/         # Testing utilities and fixtures
│   ├── utils/              # Shared utilities (Model factory, text processing)
│   └── whatsapp/           # WhatsApp API client wrapper
├── .env                    # Environment variables (Secrets)
├── AGENTS.md               # This file (Architecture & Context)
├── docker-compose.yml      # Docker services (DB, WhatsApp, App)
└── pyproject.toml          # Python dependencies and project metadata
```

---

## AI Agents Architecture

The system is designed following **KISS** (Keep It Simple, Stupid), **DRY** (Don't Repeat Yourself), and **Separation of Concerns** principles.

### Design Principles

1.  **Separation of Concerns**:
    *   **Logic vs. Prompts**: Prompts are stored in `src/templates/` (*.j2) and rendered by `prompt_manager`.
    *   **Routing vs. Execution**: The `Router` decides intent; specific handlers execute it.
    *   **Model Abstraction**: `ModelFactory` abstracts the underlying LLM (Cloud vs. Local).

2.  **DRY (Don't Repeat Yourself)**:
    *   **Model Factory**: `src/utils/model_factory.py` centralizes model initialization.
    *   **Base Handler**: Common logic lives in `BaseHandler`.

3.  **KISS**:
    *   **Stateless Agents**: Agents rely on passed context (history, query).
    *   **Pydantic AI**: Used for structured output and type safety.

### Agent Inventory

| Agent | Responsibility | Source File | Prompt Template |
| :--- | :--- | :--- | :--- |
| **Router** | Classifies user intent (`summarize`, `ask_question`, etc.), handles specific group requests, and extracts time windows | `src/handler/router.py` | `intent.j2` |
| **RAG Generation** | Generates answers from retrieved context | `src/handler/knowledge_base_answers.py` | `rag.j2` |
| **Rephrasing** | Rewrites queries for better vector search | `src/handler/knowledge_base_answers.py` | `rephrase.j2` |
| **Summarization** | Summarizes chat history | `src/summarize_and_send_to_groups/__init__.py` | `quick_summary.j2` |
| **Spam Detector** | Detects spam links in groups | `src/handler/whatsapp_group_link_spam.py` | `link_spam_detector.j2` |
| **Conversation Splitter** | Segments chats for KB ingestion | `src/load_new_kbtopics/__init__.py` | `conversation_splitter.j2` |

---

## Data Flow

### Message Processing Pipeline
1.  **User Message** -> **Router Agent**
2.  **Router** decides intent:
    *   `ask_question` -> **Rephrasing Agent** -> **Vector Search** -> **RAG Agent** -> **Response**
    *   `summarize` -> **Security Check (Group Membership)** -> **Summarization Agent** -> **Response**
    *   `about` / `other` -> **Static/Default Response**

### Group Membership & Security
To ensure privacy, the bot verifies that a user is a member of a group before providing a summary.
1.  **Ingestion**: Group members are synced on startup (`init_groups.py`) using bulk upserts.
2.  **Lazy Updates**: Active users are added to the `GroupMember` table when they send a message.
3.  **Live Fallback**: If a user requests a summary but isn't in the DB (e.g., a lurker), the bot checks WhatsApp live participants list.

### Summarization Features
The bot supports flexible summarization requests:
*   **Specific Groups**: Users can ask to summarize a specific group by name (e.g., "Summarize the General group").
*   **Time Windows**: Users can specify a time range (e.g., "last 2 days", "last 4 hours").
    *   **Default**: 24 hours.
    *   **Maximum**: 7 days (168 hours). Requests exceeding this are automatically clamped.
    *   **Context**: Fetches up to 100 messages for longer time windows (vs 30 for default).

### Knowledge Base Ingestion
1.  **Raw Chat Logs** -> **Conversation Splitter Agent**
2.  **Splitter** -> **Topic Extraction**
3.  **Topics** -> **Embedding (Voyage AI)** -> **Vector DB (Postgres)**

---

## Group Management System

The project includes a robust Group Management UI and API designed for stability and safety.

### Key Features
1.  **UI Dashboard**: Accessible at `/group/ui`, allowing users to:
    *   Create groups.
    *   Add participants in bulk.
    *   Send bulk messages.
    *   List and manage groups.
2.  **Safety & Anti-Ban Mechanisms**:
    *   **Random Delays**: When adding multiple participants, the system waits 30-60 seconds between each request to prevent WhatsApp rate limiting (429 errors) and bans.
    *   **Duplicate Skipping**: Before adding a user, the system checks the local database (`GroupMember` table). If the user exists, the API call is skipped entirely, saving quota and time.
3.  **Database Synchronization**:
    *   **Manual Sync**: A "Sync DB" button forces a refresh of group data from WhatsApp to the local Postgres DB.
    *   **DB-First Listing**: The "List Groups" feature queries the local DB instead of the WhatsApp API to ensure instant loading and zero rate-limit risk.
4.  **Reporting**:
    *   **CSV Export**: After a bulk "Add Members" operation, a CSV report is automatically generated and downloaded, detailing the status (Success, Skipped, Failed) for each number.
    *   **Server-Side Storage**: A copy of the report is also saved to `src/reports/` on the server (synced to host via volume) with a timestamped filename (e.g., `participants_report_2025-12-22_08-47-47.csv`).

---

## Configuration & Model Switching

The project supports switching between cloud-based models (Anthropic) and local models (Hugging Face) via `.env`.

*   **Local Model**: Set `USE_LOCAL_MODEL=True`. Uses `src/services/local_model.py` (e.g., `dicta-il/dicta-lm-2.0-instruct`).
*   **Cloud Model**: Set `USE_LOCAL_MODEL=False`. Uses `pydantic-ai` default (Anthropic).

**Key File**: `src/utils/model_factory.py` handles this logic.

---

## Coding Guidelines for AI Agents

To ensure code quality and prevent errors during automated edits, follow these guidelines:

1.  **File Editing Safety**:
    *   **Verify Context**: Before editing a file, always read enough context to ensure you are targeting the correct lines.
    *   **Unique Replacements**: When using `replace_string_in_file`, ensure the `oldString` is unique and includes sufficient context (3-5 lines) to avoid ambiguous matches.
    *   **Avoid Partial Replacements**: Do not try to replace just a small part of a function if it risks breaking the syntax (e.g., leaving dangling brackets or quotes). Prefer replacing the entire function or block.
    *   **Check Syntax**: After editing, verify that the file syntax is still valid (e.g., no unclosed strings, matching parentheses).

2.  **Code Structure**:
    *   **Modular Functions**: Keep functions small and focused. Large functions are harder to edit reliably.
    *   **Type Hinting**: Use Python type hints for all function arguments and return values.
    *   **Error Handling**: Wrap external API calls in `try/except` blocks and log errors appropriately.

3.  **Testing**:
    *   **Restart Services**: After modifying core API files, restart the relevant services (e.g., `web-server`) to apply changes and check for startup errors.
