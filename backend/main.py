from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

app = FastAPI()

# Enable CORS for Vue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process(query: str = Form(...), file: UploadFile = File(None), use_demo: bool = Form(False)):
    # For now, we're ignoring the actual file and just returning mock data
    # Later you can integrate real processing here
    
    # Mock data to return
    result = {
        "thumbnails": ["thumbnail1.jpg", "thumbnail2.jpg"],
        "previews": ["preview1.mov", "preview2.mov"],
        "videos": ["video1.mov", "video2.mov"]
    }
    
    # If a file was uploaded, store it for later use
    if not use_demo and file:
        os.makedirs("uploads", exist_ok=True)
        input_path = f"uploads/{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())
    
    return JSONResponse(content=result)