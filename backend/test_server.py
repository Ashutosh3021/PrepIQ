from fastapi import FastAPI
from app.routers import auth

app = FastAPI()

# Include only the auth router for testing
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Test server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)