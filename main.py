from fastapi import FastAPI
from route.routes import router
from fastapi.middleware.cors import CORSMiddleware

print("Demarrage du serveur !")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # frontend local
    ],# Ou "*" pour tout autoriser (pas recommand�)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
