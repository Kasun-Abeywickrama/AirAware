# AirAware

AirAware is a New Delhi PM2.5 decision-support web application. This repository currently contains the backend foundation only.

## Start with Docker

1. Copy `.env.example` to `.env`.
2. Run:

   ```powershell
   docker compose up --build
   ```

3. Open:
   - Health check: `http://localhost:8000/health`
   - API documentation: `http://localhost:8000/docs`

Stop the containers with `docker compose down`.

## Run the backend locally

Install dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the API:

```powershell
python -m uvicorn backend.app.main:app --reload
```

## Run tests

From the repository root:

```powershell
python -m pytest backend/tests
```
