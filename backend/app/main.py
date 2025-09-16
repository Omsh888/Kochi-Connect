from fastapi import FastAPI
from app.database import startup_db_client
from app.routes import email_routes
from app.routes import summary_routes
from app.routes import employee_routes
from app.routes import document_routes

app = FastAPI()
app.include_router(email_routes.router)
app.include_router(summary_routes.router)
app.include_router(employee_routes.router)
app.include_router(document_routes.router)

@app.get("/")
def home():
    return {"message": "Gmail + Drive + Mongo integration running ✅"}

@app.on_event("startup")
async def startup_db():
    await startup_db_client()
