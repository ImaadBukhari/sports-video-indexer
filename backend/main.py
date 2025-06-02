from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from moviepy.video.io.VideoFileClip import VideoFileClip
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
    input_path = "demo.mp4" if use_demo else f"uploads/{file.filename}"
    if not use_demo and file:
        os.makedirs("uploads", exist_ok=True)
        with open(input_path, "wb") as f:
            f.write(await file.read())

    # Replace with your ML inference
    start, end = 10, 20  # mock result
    clip = VideoFileClip(input_path).subclip(start, end)
    output_path = "result.mp4"
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return FileResponse(output_path, media_type="video/mp4")