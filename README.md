# NeuroSpark Core

An autonomous agentic learning platform—a "school" of specialised Agents that continuously scout trusted sources, vectorise fresh knowledge, teach humans (or downstream AIs), and never contaminate themselves with hallucinations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-required-blue.svg)](https://www.docker.com/)
[![Test-Driven Development](https://img.shields.io/badge/TDD-required-red.svg)](https://en.wikipedia.org/wiki/Test-driven_development)

## Project Overview

NeuroSpark Core is a distributed system of specialized agents that work together to:
1. Discover and collect knowledge from trusted sources
2. Process and vectorize this knowledge
3. Create lessons and answers with proper citations
4. Validate content for factual accuracy
5. Deliver knowledge to users through conversational interfaces
6. Monitor system performance and quality

The platform is designed to be:
- **Factual**: All content is grounded in trusted sources with citations
- **Autonomous**: Agents work together with minimal human intervention
- **Scalable**: Modular architecture allows for horizontal scaling
- **Extensible**: Easy to add new agents, data sources, and capabilities

## Architecture

The system consists of the following agents:

| Agent | Core Responsibility | Consumes | Emits |
|-------|--------------------|----------|-------|
| **Curator** | Discover docs (OpenAlex, NewsAPI, SerpAPI) | keywords, RSS | raw docs |
| **Vectoriser** | Clean ➜ chunk ➜ embed | raw docs | vectors (Qdrant) |
| **Professor** | Draft lessons / answers with citations | vectors | markdown drafts |
| **Reviewer** | Validates each draft's citations via RAG similarity & factuality | drafts | `approve` / `regenerate` |
| **Tutor** | Converse with users, track mastery | approved lessons | chat msgs |
| **Auditor** | Spot‑check global metrics: relevance, cost, latency | any outputs | audit reports |
| **Custodian** | De‑dupe vectors, prune stale/low‑score chunks, rebuild indexes | Qdrant metadata | pruned IDs |
| **Governor** | Enforce MCP rate‑limits, per‑Agent budgets | cost events | throttle cmds |

## Tech Stack

| Layer | Choice | Why / Escape Hatch |
|-------|--------|--------------------|
| **API Surface** | FastAPI + gRPC (`grpclib`) | Python ecosystem, language‑agnostic micro‑services |
| **Vector Search** | **Llama‑Index router** → Qdrant (ANN) *+* ElasticLite (BM25) | Hybrid recall; swap ElasticLite for OpenSearch if needed |
| **Metadata DB** | Postgres 16 | ACID, easy local dev |
| **Blob Store** | MinIO (S3‑compat) | Single‑binary, Docker‑friendly |
| **Message Bus** | Redis Streams → migrate to NATS when clustered | Zero config on day 0 |
| **Scraping** | trafilatura (HTML) • pdfminer‑s (PDF) | Stable, Unicode‑safe |
| **LLM Provider** | OpenAI `gpt‑4o` (env `OPENAI_API_KEY`) | Can switch to local Llama‑3‑GGUF |
| **Paper / Web APIs** | OpenAlex (scholarly) • NewsAPI • SerpAPI | All have Python SDKs |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Make](https://www.gnu.org/software/make/)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd neurospark-core

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Copy example environment file and add your API keys
cp .env.example .env

# Edit the .env file to add your API keys
# Required: OPENAI_API_KEY for LLM functionality
# Optional: OPENALEX_API_KEY, NEWSAPI_API_KEY, SERPAPI_API_KEY for external data sources
```

### Running the Platform

```bash
# Start all services with Docker Compose
make dev

# Check the status of all services
docker-compose ps

# View logs for a specific service
make logs-api  # Replace 'api' with any service name

# Run tests to verify setup
make test

# Stop all services
make down
```

### API Documentation

Once the services are running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Monitoring

- Grafana Dashboard: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Development

This project follows Test-Driven Development principles. All new features must include tests.

### Project Structure

```
neurospark-core/
├── src/
│   ├── api/                # FastAPI and gRPC API definitions
│   ├── agents/             # Agent implementations
│   │   ├── curator/        # Discovers documents from trusted sources
│   │   ├── vectoriser/     # Processes and embeds documents
│   │   ├── professor/      # Creates draft lessons and answers
│   │   ├── reviewer/       # Validates content for factuality
│   │   ├── tutor/          # Interfaces with users
│   │   ├── auditor/        # Monitors system metrics
│   │   ├── custodian/      # Maintains vector database
│   │   └── governor/       # Enforces resource limits
│   ├── database/           # Database models and connections
│   ├── vector_store/       # Vector database interface
│   ├── search/             # Search functionality
│   ├── storage/            # Blob storage interface
│   ├── message_bus/        # Message bus for inter-agent communication
│   └── common/             # Shared utilities and models
├── tests/                  # Test suite
├── docker/                 # Docker configuration
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── .env.example            # Example environment variables
├── docker-compose.yml      # Service orchestration
├── Makefile                # Common commands
└── README.md               # This file
```

## Testing

We use pytest for testing. All tests are located in the `tests/` directory.

```bash
# Run all tests
make test

# Run a specific test
make test-api  # Runs tests/test_api.py

# Run tests with coverage report
pytest --cov=src tests/
```

## Common Issues and Troubleshooting

### Docker Services Not Starting

If you encounter issues with Docker services not starting:

```bash
# Check service logs
docker-compose logs <service-name>

# Rebuild a specific service
docker-compose build --no-cache <service-name>

# Reset all containers and volumes (WARNING: This will delete all data)
docker-compose down -v
make dev
```

### API Key Issues

If you encounter issues with API keys:

1. Ensure your `.env` file contains the required API keys
2. Check that the API keys are valid and have the necessary permissions
3. For OpenAI, verify your account has sufficient credits

### Database Connection Issues

If you encounter database connection issues:

1. Ensure the Postgres service is running: `docker-compose ps postgres`
2. Check Postgres logs: `docker-compose logs postgres`
3. Verify database credentials in `.env` match those in `docker-compose.yml`

## Contributing

We welcome contributions to NeuroSpark Core! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

Please ensure your code follows our coding standards and includes tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
