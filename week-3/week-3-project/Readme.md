# GulzarSoft Backend Setup

## 1) Environment Variables

Copy `.env.example` to `.env` and adjust values if needed.

Required PostgreSQL keys:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`
- `APP_DATABASE_URL`
- `CHECKPOINT_DATABASE_URL`

## 2) Start PostgreSQL

Use Docker Compose from project root:

```bash
docker compose up -d postgres
```

## 3) Why the previous error happened

The Postgres container refuses first-time initialization when `POSTGRES_PASSWORD` is missing. This project now includes that variable in `.env` and uses it in `docker-compose.yml`.
