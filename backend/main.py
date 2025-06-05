from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import cv2
from pathlib import Path
import glob

app = FastAPI()

# Enable CORS for Vue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for loaded models and embeddings
embedding_model = None
faiss_index = None
frame_mapping = None
video_mapping = None  # Maps frame indices to their source videos

def find_video_embedding_pairs():
    """Find all video and embedding file pairs"""
    embedding_dir = 'processing/embeddings'
    video_dir = 'processing/input_videos'
    
    pairs = []
    
    # Find all embedding files
    embedding_files = glob.glob(os.path.join(embedding_dir, '*_embeddings_512.pkl'))
    
    for embedding_file in embedding_files:
        # Extract base name from embedding file
        basename = os.path.basename(embedding_file)
        video_name = basename.replace('_embeddings_512.pkl', '.mp4')
        video_path = os.path.join(video_dir, video_name)
        
        # Check if corresponding video exists
        if os.path.exists(video_path):
            pairs.append({
                'embedding_file': embedding_file,
                'video_file': video_path,
                'video_name': video_name.replace('.mp4', '')
            })
            print(f"Found pair: {video_name} -> {basename}")
        else:
            print(f"Warning: Video not found for {basename}")
    
    return pairs

def load_embeddings():
    """Load embeddings from multiple files and initialize FAISS index"""
    global embedding_model, faiss_index, frame_mapping, video_mapping
    
    # Load the embedding model
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Find all video-embedding pairs
    video_pairs = find_video_embedding_pairs()
    
    if not video_pairs:
        print("No video-embedding pairs found!")
        return False
    
    try:
        all_embeddings = []
        frame_mapping = {}  # Maps FAISS index -> (video_name, frame_number)
        video_mapping = {}  # Maps video_name -> video_file_path
        
        current_index = 0
        
        for pair in video_pairs:
            print(f"Loading embeddings from {pair['embedding_file']}...")
            
            with open(pair['embedding_file'], 'rb') as f:
                embedding_data = pickle.load(f)
            
            embeddings = embedding_data['embeddings']
            video_name = pair['video_name']
            video_mapping[video_name] = pair['video_file']
            
            # Add embeddings to the collection
            for frame_num, embedding_vector in embeddings.items():
                all_embeddings.append(embedding_vector)
                frame_mapping[current_index] = {
                    'video_name': video_name,
                    'frame_number': frame_num,
                    'video_path': pair['video_file']
                }
                current_index += 1
        
        if not all_embeddings:
            print("No embeddings found in any file!")
            return False
        
        # Convert to numpy array with explicit dtype and contiguity
        embedding_vectors = np.array(all_embeddings, dtype=np.float32)
        embedding_vectors = np.ascontiguousarray(embedding_vectors)

        # Check for invalid values
        if np.isnan(embedding_vectors).any() or np.isinf(embedding_vectors).any():
            print("Warning: Found NaN or Inf values in embeddings")
            embedding_vectors = np.nan_to_num(embedding_vectors, nan=0.0, posinf=1.0, neginf=-1.0)

        # Create FAISS index
        dimension = embedding_vectors.shape[1]
        faiss_index = faiss.IndexFlatIP(dimension)

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embedding_vectors)
        faiss_index.add(embedding_vectors)
        
        print(f"✅ Loaded {len(all_embeddings)} embeddings from {len(video_pairs)} videos into FAISS index")
        
        # Print summary
        video_counts = {}
        for mapping in frame_mapping.values():
            video_name = mapping['video_name']
            video_counts[video_name] = video_counts.get(video_name, 0) + 1
        
        for video_name, count in video_counts.items():
            print(f"  - {video_name}: {count} frames")
        
        return True
        
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return False

def search_similar_frames(query: str, top_k: int = 3):
    """Search for frames similar to the query using FAISS across all videos"""
    global embedding_model, faiss_index, frame_mapping
    
    if faiss_index is None:
        raise ValueError("FAISS index not loaded")
    
    # Encode the query
    query_embedding = embedding_model.encode([query])
    query_embedding = query_embedding.astype('float32')
    
    # Normalize for cosine similarity
    faiss.normalize_L2(query_embedding)
    
    # Search in FAISS index
    similarities, indices = faiss_index.search(query_embedding, top_k)
    
    # Convert indices to frame numbers and video info
    results = []
    for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
        frame_info = frame_mapping[idx]
        results.append({
            'frame_number': int(frame_info['frame_number']),
            'video_name': frame_info['video_name'],
            'video_path': frame_info['video_path'],
            'similarity': float(similarity),
            'rank': i + 1
        })
    
    return results

def extract_frame_as_thumbnail(video_path: str, frame_number: int, output_path: str):
    """Extract a single frame as thumbnail"""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(output_path, frame)
    
    cap.release()
    return ret

def extract_video_segment(video_path: str, center_frame: int, duration_seconds: int, output_path: str, fps: int = 30):
    """Extract a video segment around a center frame with web-compatible codec"""
    start_frame = max(0, center_frame - duration_seconds * fps)
    end_frame = center_frame + duration_seconds * fps
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    end_frame = min(end_frame, total_frames - 1)
    
    # Use H.264 codec for better web compatibility
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Use original FPS or 30 if not available
    output_fps = original_fps if original_fps > 0 else 30
    
    out = cv2.VideoWriter(output_path, fourcc, output_fps, (frame_width, frame_height))
    
    if not out.isOpened():
        print(f"Warning: Could not open video writer for {output_path}, trying alternative codec")
        # Fallback to mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, output_fps, (frame_width, frame_height))
    
    # Extract frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frames_written = 0
    for frame_idx in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frames_written += 1
    
    cap.release()
    out.release()
    
    print(f"Wrote {frames_written} frames to {output_path}")
    
    # Verify the output file exists and has content
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True
    else:
        print(f"Warning: Output video {output_path} is empty or doesn't exist")
        return False

def generate_video_assets(search_results):
    """Generate thumbnails, previews, and videos based on search results"""
    thumbnails = []
    previews = []
    videos = []
    
    # Create output directories
    os.makedirs('static/thumbnails', exist_ok=True)
    os.makedirs('static/previews', exist_ok=True)
    os.makedirs('static/videos', exist_ok=True)
    
    for i, result in enumerate(search_results):
        frame_num = result['frame_number']
        video_path = result['video_path']
        video_name = result['video_name']
        
        # Generate filenames with video name to avoid conflicts
        thumbnail_filename = f"{video_name}_thumbnail_{i+1}.jpg"
        preview_filename = f"{video_name}_preview_{i+1}.mp4"
        video_filename = f"{video_name}_video_{i+1}.mp4"
        
        thumbnail_path = f"static/thumbnails/{thumbnail_filename}"
        preview_path = f"static/previews/{preview_filename}"
        video_path_out = f"static/videos/{video_filename}"
        
        try:
            # Extract thumbnail (single frame)
            if extract_frame_as_thumbnail(video_path, frame_num, thumbnail_path):
                thumbnails.append(thumbnail_filename)
                print(f"Generated thumbnail: {thumbnail_filename}")
            else:
                print(f"Failed to generate thumbnail for {video_name}")
                continue
            
            # Extract preview (2 seconds before and after = 4 seconds total)
            if extract_video_segment(video_path, frame_num, 2, preview_path):
                previews.append(preview_filename)
                print(f"Generated preview: {preview_filename}")
            else:
                print(f"Failed to generate preview for {video_name}")
                previews.append("")  # Empty placeholder
            
            # Extract full video (5 seconds before and after = 10 seconds total)
            if extract_video_segment(video_path, frame_num, 5, video_path_out):
                videos.append(video_filename)
                print(f"Generated video: {video_filename}")
            else:
                print(f"Failed to generate video segment for {video_name}")
                videos.append("")  # Empty placeholder
            
        except Exception as e:
            print(f"Error generating assets for frame {frame_num} from {video_name}: {e}")
            # Use empty placeholders if generation fails
            thumbnails.append("")
            previews.append("")
            videos.append("")
    
    return thumbnails, previews, videos

@app.post("/process")
async def process(query: str = Form(...), file: UploadFile = File(None), use_demo: bool = Form(False)):
    try:
        # Search for similar frames across all videos
        search_results = search_similar_frames(query, top_k=3)
        
        print(f"Search results for query '{query}':")
        for result in search_results:
            print(f"  {result['video_name']} Frame {result['frame_number']}: similarity {result['similarity']:.4f}")
        
        # Generate video assets
        thumbnails, previews, videos = generate_video_assets(search_results)
        
        result = {
            "thumbnails": thumbnails,
            "previews": previews, 
            "videos": videos,
            "search_results": search_results  # Include search metadata with video info
        }
        
        # If a file was uploaded, store it for later use
        if not use_demo and file:
            os.makedirs("uploads", exist_ok=True)
            input_path = f"uploads/{file.filename}"
            with open(input_path, "wb") as f:
                f.write(await file.read())
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to mock data
        result = {
            "thumbnails": ["thumbnail1.jpg", "thumbnail2.jpg", "thumbnail3.jpg"],
            "previews": ["preview1.mp4", "preview2.mp4", "preview3.mp4"],
            "videos": ["video1.mp4", "video2.mp4", "video3.mp4"],
            "error": str(e)
        }
        return JSONResponse(content=result)

@app.get("/videos")
async def list_videos():
    """Get list of available videos"""
    try:
        video_pairs = find_video_embedding_pairs()
        videos = [pair['video_name'] for pair in video_pairs]
        return JSONResponse(content={"videos": videos})
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.get("/test-static")
async def test_static():
    """Test endpoint to check static file serving"""
    static_dirs = ['thumbnails', 'previews', 'videos']
    file_counts = {}
    
    for dir_name in static_dirs:
        dir_path = f"static/{dir_name}"
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            file_counts[dir_name] = {
                "count": len(files),
                "files": files[:5]  # Show first 5 files
            }
        else:
            file_counts[dir_name] = {"count": 0, "files": []}
    
    return JSONResponse(content=file_counts)

@app.on_event("startup")
async def startup_event():
    """Load embeddings on startup"""
    print("Loading embeddings from multiple videos...")
    if load_embeddings():
        print("✅ All embeddings loaded successfully")
    else:
        print("❌ Failed to load embeddings - using fallback mode")

# Serve static files for thumbnails, previews, and videos
from fastapi.staticfiles import StaticFiles

# Add headers for proper video serving
class VideoStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith('.mp4'):
            response.headers["Accept-Ranges"] = "bytes"
            response.headers["Content-Type"] = "video/mp4"
        return response

app.mount("/static", VideoStaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)