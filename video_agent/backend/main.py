from fastapi import FastAPI

app = FastAPI(title="TikTok Genie API")


@app.get("/")
async def root():
    return {"message": "Welcome to TikTok Genie API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
