from fastapi import FastAPI

APP_NAME = "HomeNet Guardian"

app = FastAPI(title=APP_NAME)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "name": APP_NAME}
