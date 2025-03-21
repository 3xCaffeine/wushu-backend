## Backend for Project Wushu

> Backend codebase for for Wushu Tournament Management Platform

## Prerequisities

- Python `3.11+`
- `uv` Python package manager
- Postgres Database (NeonDB, RDS, Docker)
- AWS S3 bucket preconfigured
- Docker

### Setup

1. Clone the repository and change to project directory.
```bash
git clone https://github.com/3xCaffeine/wushu-backend
cd wushu-backend
```

2. Create a `.env` file with secrets.

#### With `uv`

3. Install dependencies, activate virtual environment and run the application with `fastapi-cli`
```bash
uv sync
fastapi run main.py
```

#### With `Docker`

```bash
docker build -t wushu-backend:latest .
docker run -p 8000:5000 --env-file=.env -d wushu-backend:latest
```

## Usage

Visit [localhost:5000](http://localhost:8000/docs) to inspect the API docs. Send requests to the endpoints with `curl` or `Postman` or any API testing platform.