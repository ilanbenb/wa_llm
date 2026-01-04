# 📱 WhatsApp Group Summary Bot

![release version](https://img.shields.io/github/v/release/ilanbenb/wa_llm)
![Build Image](https://github.com/ilanbenb/wa_llm/actions/workflows/docker.yml/badge.svg)
![Release](https://github.com/ilanbenb/wa_llm/actions/workflows/release.yml/badge.svg)

AI-powered WhatsApp bot that **joins any group, tracks conversations, and generates intelligent summaries**.

---

## Features

- 🤖 Automated group chat responses (when mentioned)
- 📝 Smart **LLM-based conversation summaries**
- 📚 Knowledge base integration for context-aware answers
- 📂 Persistent message history with PostgreSQL + `pgvector`
- 🔗 Support for multiple message types (text, media, links)
- 👥 Group management & customizable settings
- 🔕 **Opt-out feature**: Users can opt-out of being tagged in summaries/answers via DM.
- 🖥️ **Group Management UI**: Web interface to manage groups, participants, and settings (`localhost:8000/group/ui`).
- ⚡ REST API with Swagger docs (`localhost:8000/docs`)

---

## 🐳 Docker Compose Configurations

This project includes multiple Docker Compose files for different environments:

| File                           | Purpose                                                                        | Usage                                                  |
| ------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------ |
| `docker-compose.yml`           | **Default/Development**. Builds the application from source code.              | `docker compose up -d`                                 |
| `docker-compose.prod.yml`      | **Production**. Uses pre-built images from GHCR. Recommended for deployment.   | `docker compose -f docker-compose.prod.yml up -d`      |
| `docker-compose.local-run.yml` | **Local Execution**. For running the app on host while services run in Docker. | `docker compose -f docker-compose.local-run.yml up -d` |
| `docker-compose.base.yml`      | **Base Configuration**. Contains shared service definitions.                   | ❌ **Do not use directly**                             |

---

## 📋 Prerequisites

- 🐳 Docker and Docker Compose
- 🐍 Python 3.12+
- 🗄️ PostgreSQL with `pgvector` extension
- 🔑 Voyage AI API key
- 📲 WhatsApp account for the bot

## Quick Start

### 1. Clone & Configure

`git clone https://github.com/YOUR_USER/wa_llm.git
cd wa_llm`

### 2. Create .env file

- Copy `.env.example` to `.env` and fill in required values.

```
cp .env.example .env
```

#### Environment Variables

<div style="font-size: 10px;">

| Variable                       | Description                                                                        | Default                                                      |
| ------------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `WHATSAPP_HOST`                | WhatsApp Web API URL                                                               | `http://localhost:3000`                                      |
| `WHATSAPP_BASIC_AUTH_USER`     | WhatsApp API user                                                                  | `admin`                                                      |
| `WHATSAPP_BASIC_AUTH_PASSWORD` | WhatsApp API password                                                              | `admin`                                                      |
| `VOYAGE_API_KEY`               | Voyage AI key                                                                      | –                                                            |
| `DB_URI`                       | PostgreSQL URI                                                                     | `postgresql+asyncpg://user:password@localhost:5432/postgres` |
| `LOG_LEVEL`                    | Log level (`DEBUG`, `INFO`, `ERROR`)                                               | `INFO`                                                       |
| `ANTHROPIC_API_KEY`            | Anthropic API key. You need to have a real anthropic key here, starts with sk-.... | –                                                            |
| `LOGFIRE_TOKEN`                | Logfire monitoring key, You need to have a real logfire key here                   | –                                                            |
| `DM_AUTOREPLY_ENABLED`         | Enable static auto-reply for DMs. If `False`, bot uses AI to respond.              | `False`                                                      |
| `DM_AUTOREPLY_MESSAGE`         | Message to send as auto-reply                                                      | `Hello, I am not designed to answer to personal messages.`   |
| `RATE_LIMIT_USER_MESSAGES`       | Max messages per user in window                                                    | `5`                                                          |
| `RATE_LIMIT_USER_WINDOW_SECONDS` | Time window for user rate limit (seconds)                                          | `60`                                                         |
| `RATE_LIMIT_GROUP_MESSAGES`      | Max messages per group in window                                                   | `20`                                                         |
| `RATE_LIMIT_GROUP_WINDOW_SECONDS`| Time window for group rate limit (seconds)                                         | `60`                                                         |

</div>

### 3. Starting the Services

**Option A: Development (Build from source)**

```bash
docker compose up -d
```

**Option B: Production (Use pre-built images)**

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Connect your device

1. Open http://localhost:3000
2. Scan the QR code with your WhatsApp mobile app.
3. Invite the bot device to any target groups you want to summarize.
4. Restart service: `docker compose restart wa_llm-web-server`

### 5. Activating the Bot for a Group

You can manage groups and activate the bot using the **Group Management UI**:

1. Open **http://localhost:8000/group/ui** in your browser.
2. Go to the **List Groups** tab.
3. Click **Refresh List** to see your groups.
4. Click **Settings** for the group you want to manage.
5. Set an **Auto Summary Threshold** (e.g., 50 messages) to enable auto-summaries.
6. Toggle **Enable Web Search** to allow the bot to search the web for answers.
7. Click **Save Settings**.

Alternatively, you can use SQL directly:

1. open pgAdmin or any other posgreSQL admin tool
2. connect using
   | Parameter | Value |
   | --------- | --------- |
   | Host | localhost |
   | Port | 5432 |
   | Database | postgres |
   | Username | user |
   | Password | password |

3. run the following update statement:

   ```sql
       UPDATE public."group"
       SET managed = true, enable_web_search = true
       WHERE group_name = 'Your Group Name';
   ```

4. Restart the service: `docker compose restart wa_llm-web-server`

### 6. API usage

Swagger docs available at: `http://localhost:8000/docs`

#### Key Endpoints

- <b>/load_new_kbtopic (POST)</b> Loads a new knowledge base topic, prepares content for summarization.
- <b>/trigger_summarize_and_send_to_groups (POST)</b> Generates & dispatches summaries, Sends summaries to all managed groups

### 7. Opt-Out Feature

Users can control whether they are tagged in bot-generated messages (summaries, answers) by sending Direct Messages (DMs) to the bot:

| Command   | Description                                                                        |
| :-------- | :--------------------------------------------------------------------------------- |
| `opt-out` | Opt-out of being tagged. Your name will be displayed as text instead of a mention. |
| `opt-in`  | Opt-in to being tagged (default).                                                  |
| `status`  | Check your current opt-out status.                                                 |

> **Note:** This only affects messages generated by the bot. It does not prevent other users from tagging you manually.

### Rate Limiting

To prevent abuse and spam, the bot includes a built-in rate limiter:
- **User Limit**: Limits how many messages a single user can send to the bot (DMs or mentions) within a specific time window.
- **Group Limit**: Limits how many times the bot can be triggered in a specific group within a time window.

These limits can be configured using the environment variables listed above.

---

## 🚀 Production Deployment

To deploy in a production environment using the optimized configuration:

1. **Create Production Environment File**:
   Copy `.env.example` to `.env.prod` and configure your production secrets.

   ```bash
   cp .env.example .env.prod
   ```

2. **Start Services**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

This configuration includes:

- Automatic restart policies (`restart: always`)

---

## Developing

### Setup

Install dependencies using `uv`:

```bash
uv sync --all-extras --dev
```

### Development Commands

The project uses **Poe the Poet** for task automation with parallel execution:

```bash
# Run all checks (format, then parallel lint/typecheck/test)
uv run poe check

# Individual tasks
uv run poe format     # Format code with ruff
uv run poe lint       # Lint code with ruff
uv run poe typecheck  # Type check with pyright
uv run poe test       # Run tests with pytest

# List all available tasks
uv run poe
```

The `check` command runs formatting first, then executes linting, type checking, and testing **in parallel** for faster execution.

### Key Files

- Main application: `app/main.py`
- WhatsApp client: `src/whatsapp/client.py`
- Message handler: `src/handler/__init__.py`
- Database models: `src/models/`

---

## Architecture

The project consists of several key components:

- FastAPI backend for webhook handling
- WhatsApp Web API client for message interaction
- PostgreSQL database with vector storage for knowledge base
- AI-powered message processing and response generation

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License

[LICENCE](CODE_OF_CONDUCT.md)
