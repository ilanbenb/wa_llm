# WhatsApp Group Assistant Bot

A WhatsApp bot that can participate in group conversations, powered by AI. The bot monitors group messages and responds when mentioned.

## Features

- Automated group chat responses when mentioned
- Message history tracking and summarization
- Knowledge base integration for informed responses
- Support for various message types (text, media, links, etc.)
- Group management capabilities

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- PostgreSQL with pgvector extension
- Voyage AI API key
- WhatsApp account for the bot

## Setup

1. Clone the repository

2. Create a `.env` file in the src directory with the following variables:

```env
WHATSAPP_HOST=http://localhost:3000
WHATSAPP_BASIC_AUTH_USER=admin
WHATSAPP_BASIC_AUTH_PASSWORD=admin
VOYAGE_API_KEY=your_voyage_api_key
DB_URI=postgresql+asyncpg://user:password@localhost:5432/webhook_db
LOG_LEVEL=INFO
ANTHROPIC_API_KEY=your-key-here # You need to have a real anthropic key here, starts with sk-....
LOGFIRE_TOKEN=your-key-here # You need to have a real logfire key here
```

3. Start the services:
```bash
docker-compose up -d
```

4. Initialize the WhatsApp connection by scanning the QR code through the WhatsApp web interface.

## Developing

* install uv tools `uv sync --all-extras --active`
* run ruff (Python linter and code formatter) `ruff check` and `ruff format`
* check for types usage 

## Architecture

The project consists of several key components:

- FastAPI backend for webhook handling
- WhatsApp Web API client for message interaction
- PostgreSQL database with vector storage for knowledge base
- AI-powered message processing and response generation

## Key Files

- Main application: `app/main.py`
- WhatsApp client: `src/whatsapp/client.py`
- Message handler: `src/handler/__init__.py`
- Database models: `src/models/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[LICENCE](CODE_OF_CONDUCT.md)
