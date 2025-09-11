from fastapi import FastAPI
from app.database import startup_db_client
from app.routes import email_routes

app = FastAPI()
app.include_router(email_routes.router)

@app.get("/")
def home():
    return {"message": "Gmail + Drive + Mongo integration running ✅"}

@app.on_event("startup")
async def startup_db():
    await startup_db_client()
