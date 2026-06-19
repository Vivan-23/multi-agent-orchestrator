from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.Routers.scan import router as scan_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("[START] Agentic AI Recon Interface is running!")
    print("[LINK] Click here to open: http://localhost:8000")
    print("="*50 + "\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    # Serve the frontend index.html on the root path
    return FileResponse("frontend/index.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("frontend/favicon.png")

# Include scan router
app.include_router(scan_router)

# Mount the entire frontend directory for css, js, etc. MUST BE AT THE BOTTOM!
app.mount("/", StaticFiles(directory="frontend"), name="frontend")