# Core-System

A consumer system for structured, approved legal data (laws/regulations and Q&A), prepared for RAG (Retrieval-Augmented Generation).

## Overview

The Core-System accepts structured data published by an external Admin-Ingest system, stores authoritative documents and Q&A in a normalized schema suitable for retrieval, and provides basic endpoints for health monitoring, statistics, and internal data synchronization.

## Features

- **Data Storage**: PostgreSQL database with normalized schema for legal documents and Q&A
- **Object Storage**: MinIO S3-compatible storage for document files
- **API Endpoints**: Health check, statistics, and internal sync API
- **Database Management**: Alembic migrations and Adminer web interface
- **Containerized**: Full Docker Compose setup for Windows 11 + WSL2

## Architecture

### Services

- **core_db**: PostgreSQL 15 database
- **minio**: MinIO S3-compatible object storage
- **core_adminer**: Adminer database management interface
- **core_api**: FastAPI application

### Data Models

1. **OfficialDocument**: Authoritative legal documents (laws, regulations, etc.)
2. **LegalUnit**: Document structure units (articles, paragraphs, etc.)
3. **QAEntry**: Non-authoritative Q&A content
4. **SyncWatermark**: Synchronization tracking
5. **User**: Reserved for future use

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Windows 11 with WSL2 (or Linux)

### Setup

1. **Create Docker Network**:
   ```bash
   docker network create advisor_net
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. **Start Services**:
   ```bash
   docker compose -f docker-compose.core.yml up -d --build
   ```

4. **Verify Setup**:
   - API Health: http://localhost:8000/health
   - API Docs: http://localhost:8000/docs
   - Database Admin: http://localhost:8082
   - MinIO Console: http://localhost:9001

## API Endpoints

### Health Check
```http
GET /health
```
Returns system status including database and MinIO connectivity.

### Statistics
```http
GET /stats
```
Returns counts of official documents and Q&A entries with breakdowns by status and type.

### Sync Import (Internal)
```http
POST /sync/import
Header: X-Bridge-Token: <token>
```
Internal endpoint for importing data from Bridge service. Secured by bridge token.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Project identifier | `advisor-core` |
| `ENV` | Environment (dev/prod) | `dev` |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_DB` | Database name | `coredb` |
| `CORE_DB_EXTERNAL_PORT` | External DB port | `5433` |
| `S3_ENDPOINT` | MinIO endpoint | `http://minio:9000` |
| `S3_BUCKET` | Storage bucket | `advisor-docs` |
| `BRIDGE_TOKEN` | Sync API security token | `secure_bridge_token_change_me` |

## Database Schema

### OfficialDocument
- Stores authoritative legal documents
- Supports laws, regulations, circulars, guidelines
- Includes metadata like jurisdiction, authority, dates
- Links to S3 storage for file content

### LegalUnit
- Represents document structure (articles, paragraphs, etc.)
- Hierarchical organization with order indexing
- Persian/Farsi label support

### QAEntry
- Non-authoritative Q&A content
- Topic tagging and quality scoring
- PII and moderation status tracking

## Development

### Database Migrations

```bash
# Generate new migration
docker exec -it core_api alembic revision --autogenerate -m "description"

# Apply migrations
docker exec -it core_api alembic upgrade head

# Migration history
docker exec -it core_api alembic history
```

### Running Tests

```bash
# Run all tests
docker exec -it core_api pytest

# Run specific test file
docker exec -it core_api pytest tests/test_health.py

# Run with coverage
docker exec -it core_api pytest --cov=app tests/
```

### Logs

```bash
# View all logs
docker compose -f docker-compose.core.yml logs -f

# View specific service logs
docker compose -f docker-compose.core.yml logs -f core_api
```

## Configuration Files

### `config/policy.yaml`
Defines disclaimer policies, quality thresholds, sensitive topics, and content moderation rules.

### `config/schema.yaml`
Defines legal domains, document types, unit types, citation rules, and relationship types.

## Security

- **Bridge Token**: Internal sync API secured with `X-Bridge-Token` header
- **CORS**: Configurable allowed origins
- **Database**: Internal network isolation
- **Environment**: Sensitive data in environment variables

## Monitoring

### Health Checks
- Database connectivity
- MinIO availability
- Service status reporting

### Statistics
- Document counts by type and status
- Q&A entry metrics
- System utilization data

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify PostgreSQL container is running
   - Check database credentials in `.env`
   - Ensure network connectivity

2. **MinIO Connection Failed**
   - Verify MinIO container is running
   - Check S3 credentials and endpoint
   - Verify bucket creation permissions

3. **Migration Errors**
   - Check database schema compatibility
   - Verify Alembic configuration
   - Review migration files for conflicts

### Useful Commands

```bash
# Reset database
docker compose -f docker-compose.core.yml down -v
docker compose -f docker-compose.core.yml up -d --build

# View container status
docker compose -f docker-compose.core.yml ps

# Access database directly
docker exec -it core_db psql -U postgres -d coredb

# Access MinIO CLI
docker exec -it minio mc --help
```

## Integration

This Core-System is designed to work with:
- **Admin-Ingest System**: Provides structured legal data
- **Bridge Service**: Handles data synchronization
- **RAG System**: Consumes stored data for retrieval

The system uses the `advisor_net` Docker network for inter-service communication.

## License

This project is part of the Legal Advisory System architecture.
