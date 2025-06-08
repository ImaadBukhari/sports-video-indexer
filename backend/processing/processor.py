import sys
import os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

# Import the main functions from the current directory
from .yolo_main import main as yolo_main

def create_embeddings(yolo_data, model_name_512, model_name_1024):
    """
    Create embeddings for the YOLO captions using sentence transformers.
    
    Args:
        yolo_data: List of metadata entries from YOLO
        model_name_512: Name of the model for 512-dimensional embeddings
        model_name_1024: Name of the model for 1024-dimensional embeddings
    
    Returns:
        Tuple of (embeddings_512, embeddings_1024, frame_mapping)
    """
    # Initialize models
    model_512 = SentenceTransformer(model_name_512)
    model_1024 = SentenceTransformer(model_name_1024)
    
    embeddings_512 = {}
    embeddings_1024 = {}
    captions_dict = {}
    
    for entry in yolo_data:
        frame_num = entry['frame_num']
        caption = entry['caption']
        
        # Store caption
        captions_dict[frame_num] = [caption]
        
        # Create embeddings
        embedding_512 = model_512.encode([caption])[0].astype(np.float32)
        embedding_1024 = model_1024.encode([caption])[0].astype(np.float32)
        
        # Normalize embeddings
        embedding_512 = normalize([embedding_512])[0]
        embedding_1024 = normalize([embedding_1024])[0]
        
        embeddings_512[frame_num] = embedding_512
        embeddings_1024[frame_num] = embedding_1024
        
        print(f"Frame {frame_num}: '{caption}' -> Embeddings created")
    
    return embeddings_512, embeddings_1024, captions_dict

def save_embeddings(embeddings_512, embeddings_1024, captions_dict, file_path):
    """
    Save embeddings and metadata to files.
    
    Args:
        embeddings_512: Dictionary of 512-dimensional embeddings
        embeddings_1024: Dictionary of 1024-dimensional embeddings
        captions_dict: Dictionary of YOLO captions
        file_path: Original video file path for naming
    """
    # Create output directory
    os.makedirs('embeddings', exist_ok=True)
    
    # Generate base filename from video path
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Save 512-dimensional embeddings
    embedding_data_512 = {
        'embeddings': embeddings_512,
        'captions': captions_dict,
        'dimension': 512,
        'video_file': file_path
    }
    
    with open(f'embeddings/{base_name}_embeddings_512.pkl', 'wb') as f:
        pickle.dump(embedding_data_512, f)
    
    # Save 1024-dimensional embeddings
    embedding_data_1024 = {
        'embeddings': embeddings_1024,
        'captions': captions_dict,
        'dimension': 1024,
        'video_file': file_path
    }
    
    with open(f'embeddings/{base_name}_embeddings_1024.pkl', 'wb') as f:
        pickle.dump(embedding_data_1024, f)
    
    print(f"Embeddings saved:")
    print(f"  - {base_name}_embeddings_512.pkl ({len(embeddings_512)} frames)")
    print(f"  - {base_name}_embeddings_1024.pkl ({len(embeddings_1024)} frames)")

def process_videos():
    """
    Main processing function that runs YOLO on video files and creates embeddings.
    """
    # File paths to process
    file_paths = ['input_videos/08fd33_4.mp4']
    
    # Sentence transformer models for different embedding dimensions
    model_512 = 'all-MiniLM-L6-v2'  # 384 dimensions (closest to 512)
    model_1024 = 'all-mpnet-base-v2'  # 768 dimensions (closest to 1024)
    
    for file_path in file_paths:
        print(f"\n{'='*60}")
        print(f"Processing: {file_path}")
        print(f"{'='*60}")
        
        # Run YOLO analysis
        print("\n🎯 Running YOLO analysis...")
        try:
            yolo_data = yolo_main(file_path)
            print(f"YOLO detected {len(yolo_data)} events")
        except Exception as e:
            print(f"Error running YOLO: {e}")
            continue
        
        # Create embeddings directly from YOLO data
        print("\n🧠 Creating embeddings...")
        try:
            embeddings_512, embeddings_1024, captions_dict = create_embeddings(
                yolo_data, model_512, model_1024
            )
            print(f"Created embeddings for {len(embeddings_512)} frames")
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            continue
        
        # Save embeddings
        print("\n💾 Saving embeddings...")
        try:
            save_embeddings(embeddings_512, embeddings_1024, captions_dict, file_path)
        except Exception as e:
            print(f"Error saving embeddings: {e}")
            continue
        
        print(f"\n✅ Successfully processed {file_path}")

def load_embeddings(file_path, dimension=512):
    """
    Utility function to load saved embeddings.
    
    Args:
        file_path: Path to the original video file
        dimension: Embedding dimension (512 or 1024)
    
    Returns:
        Dictionary containing embeddings and metadata
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    embedding_file = f'embeddings/{base_name}_embeddings_{dimension}.pkl'
    
    try:
        with open(embedding_file, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print(f"Embedding file not found: {embedding_file}")
        return None

if __name__ == '__main__':
    # Install required packages if not already installed
    try:
        import sentence_transformers
        import sklearn
    except ImportError:
        print("Installing required packages...")
        os.system("pip install sentence-transformers scikit-learn")
        import sentence_transformers
        import sklearn
    
    # Run the processing
    process_videos()
    
    # Example of how to load and use the embeddings
    print("\n" + "="*60)
    print("Example: Loading embeddings")
    print("="*60)
    
    embeddings_512 = load_embeddings('input_videos/08fd33_4.mp4', 512)
    if embeddings_512:
        print(f"Loaded 512D embeddings for {len(embeddings_512['embeddings'])} frames")
        
        # Show first embedding
        first_frame = list(embeddings_512['embeddings'].keys())[0]
        first_embedding = embeddings_512['embeddings'][first_frame]
        print(f"First embedding (Frame {first_frame}): shape {first_embedding.shape}")
        print(f"Captions: {embeddings_512['captions'][first_frame]}")