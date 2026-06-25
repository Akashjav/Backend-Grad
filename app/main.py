from fastapi import FastAPI
from app.api.V1.auth import router as auth_router
from app.api.V1.users import router as users_router
from app.api.V1.alumni import router as alumni_router
from app.api.V1.communities import router as communities_router
from app.api.V1.events import router as events_router


app = FastAPI()
    
app.include_router(auth_router)
app.include_router(users_router)

@app.get("/")
def home():
    return {"message":"Alumni Platform API"}

@app.get("/health")
def health():
    return {"status":"healthy"}    

app.include_router(alumni_router)
app.include_router(communities_router)
app.include_router(events_router)
