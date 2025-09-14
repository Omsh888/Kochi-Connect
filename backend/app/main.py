from fastapi import FastAPI
from app.database import startup_db_client
from app.routes import email_routes,document_routes
from app.auth.auth import router as auth_router

app = FastAPI()
app.include_router(email_routes.router)
app.include_router(document_routes.router, tags=["documents"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def home():
    return {"message": "Gmail + Drive + Mongo integration running ✅"}

@app.on_event("startup")
async def startup_db():
    await startup_db_client()
