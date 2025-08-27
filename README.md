# 📱 WhatsApp Group Summary Bot

AI-powered WhatsApp bot that **joins any group, tracks conversations, and generates intelligent summaries**.  

---

## Features
- 🤖 Automated group chat responses (when mentioned)
- 📝 Smart **LLM-based conversation summaries**
- 📚 Knowledge base integration for context-aware answers
- 📂 Persistent message history with PostgreSQL + `pgvector`
- 🔗 Support for multiple message types (text, media, links)
- 👥 Group management & customizable settings
- ⚡ REST API with Swagger docs (`localhost:8000/docs`)

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

Create a `.env` file in the src directory with the following variables:

```env
WHATSAPP_HOST=http://localhost:3000
WHATSAPP_BASIC_AUTH_USER=admin
WHATSAPP_BASIC_AUTH_PASSWORD=admin
VOYAGE_API_KEY=your_voyage_api_key
DB_URI=postgresql+asyncpg://user:password@localhost:5432/postgres
LOG_LEVEL=INFO
ANTHROPIC_API_KEY=your-key-here  
LOGFIRE_TOKEN=your-key-here 
```

#### Environment Variables

| Variable                       | Description                          | Default                                                      |
| ------------------------------ | ------------------------------------ | ------------------------------------------------------------ |
| `WHATSAPP_HOST`                | WhatsApp Web API URL                 | `http://localhost:3000`                                      |
| `WHATSAPP_BASIC_AUTH_USER`     | WhatsApp API user                    | `admin`                                                      |
| `WHATSAPP_BASIC_AUTH_PASSWORD` | WhatsApp API password                | `admin`                                                      |
| `VOYAGE_API_KEY`               | Voyage AI key                        | –                                                            |
| `DB_URI`                       | PostgreSQL URI                       | `postgresql+asyncpg://user:password@localhost:5432/postgres` |
| `LOG_LEVEL`                    | Log level (`DEBUG`, `INFO`, `ERROR`) | `INFO`                                                       |
| `ANTHROPIC_API_KEY`            | Anthropic API key. You need to have a real anthropic key here, starts with sk-....                    | –                                                            |
| `LOGFIRE_TOKEN`                | Logfire monitoring key, You need to have a real logfire key here               | –                                                            |


### 3. starting the services
```docker compose up -d```

### 4. Connect your device
1. Open http://localhost:3000
2. Scan the QR code with your WhatsApp mobile app.
3. Invite the bot device to any target groups you want to summarize. 
4. Restart service: `docker compose restart wa_llm-web-server`

### 5. Activating the Bot for a Group
1. open pgAdmin or any other posgreSQL admin tool
2. connect using 
    | Parameter | Value     |
    | --------- | --------- |
    | Host      | localhost |
    | Port      | 5432      |
    | Database  | postgres  |
    | Username  | user      |
    | Password  | password  |

3. run the following update statement:  

    ```
        UPDATE public."group"
        SET managed = true
        WHERE group_name = 'Your Group Name';
    ```

4. Restart the service: `docker compose restart wa_llm-web-server`

### 6. API usage 
Swagger docs available at: `http://localhost:8000/docs`

#### Key Endpoints
* <b>/load_new_kbtopic (POST)</b> Loads a new knowledge base topic, prepares content for summarization.
* <b>/trigger_summarize_and_send_to_groups (POST)</b> Generates & dispatches summaries, Sends summaries to all managed groups

---
## Developing
* install uv tools `uv sync --all-extras --active`
* run ruff (Python linter and code formatter) `ruff check` and `ruff format`
* check for types usage `pyright`

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