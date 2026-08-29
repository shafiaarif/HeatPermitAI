
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import events

load_dotenv()

REQUIRED_ENV_VARS = ["DATABASE_URL", "FORTYGUARD_API_KEY", "GOOGLE_API_KEY"]
missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}. "
        f"Check your .env file."
    )

app = FastAPI(title="HeatPermit AI Backend API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000",
#                    "https://heatpermit-git-main-shafia1.vercel.app"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


app = FastAPI(title="HeatPermit AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://heatpermit-git-main-shafia1.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "HeatPermit AI Backend"}

app.include_router(events.router)







































# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from app.routers import events

# load_dotenv()
# app = FastAPI(title="HeatPermit AI Backend")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/health")
# def health_check():
#     return {"status": "ok", "service": "HeatPermit AI Backend"}


# app.include_router(events.router)
