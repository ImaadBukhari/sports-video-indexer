import sys
import os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

# Import the main functions from the current directory
from yolo_main import main as yolo_main
from blip_main import main as blip_main


def sync_captions(yolo_data, blip_data, frame_tolerance=5):
    """
    Sync captions from YOLO and BLIP based on frame proximity.
    
    Args:
        yolo_data: List of metadata entries from YOLO
        blip_data: List of metadata entries from BLIP
        frame_tolerance: Number of frames within which to consider captions as synced
    
    Returns:
        Dictionary with frame numbers as keys and lists of synced captions as values
    """
    synced_captions = {}
    used_blip_indices = set()
    
    # Process YOLO data and find matching BLIP captions
    for yolo_entry in yolo_data:
        yolo_frame = yolo_entry['frame_num']
        yolo_caption = yolo_entry['caption']
        
        # Initialize the sublist with YOLO caption
        caption_list = [yolo_caption]
        
        # Find BLIP captions within frame tolerance
        for i, blip_entry in enumerate(blip_data):
            if i in used_blip_indices:
                continue
                
            blip_frame = blip_entry['frame_num']
            blip_caption = blip_entry['caption']
            
            # Check if BLIP frame is within tolerance of YOLO frame
            if abs(blip_frame - yolo_frame) <= frame_tolerance:
                caption_list.append(blip_caption)
                used_blip_indices.add(i)
        
        synced_captions[yolo_frame] = caption_list
    
    # Add any remaining BLIP captions that weren't synced
    for i, blip_entry in enumerate(blip_data):
        if i not in used_blip_indices:
            blip_frame = blip_entry['frame_num']
            blip_caption = blip_entry['caption']
            
            # Add as a separate entry
            if blip_frame not in synced_captions:
                synced_captions[blip_frame] = [blip_caption]
            else:
                synced_captions[blip_frame].append(blip_caption)
    
    return synced_captions

def create_embeddings(synced_captions, model_name_512, model_name_1024):
    """
    Create embeddings for the synced captions using sentence transformers.
    
    Args:
        synced_captions: Dictionary of frame numbers and caption lists
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
    
    for frame_num, caption_list in synced_captions.items():
        if not caption_list:
            continue
            
        # Combine captions into a single text
        combined_caption = " | ".join(caption_list)
        
        # If multiple captions, we'll average the individual embeddings
        if len(caption_list) > 1:
            # Get embeddings for each caption
            embeddings_512_list = model_512.encode(caption_list)
            embeddings_1024_list = model_1024.encode(caption_list)
            
            # Average the embeddings
            avg_embedding_512 = np.mean(embeddings_512_list, axis=0)
            avg_embedding_1024 = np.mean(embeddings_1024_list, axis=0)
            
            # Normalize the averaged embeddings
            avg_embedding_512 = normalize([avg_embedding_512])[0].astype(np.float32)
            avg_embedding_1024 = normalize([avg_embedding_1024])[0].astype(np.float32)

            
            embeddings_512[frame_num] = avg_embedding_512
            embeddings_1024[frame_num] = avg_embedding_1024
        else:
            # Single caption - encode directly
            embedding_512 = model_512.encode([caption_list[0]])[0].astype(np.float32)
            embedding_1024 = model_1024.encode([caption_list[0]])[0].astype(np.float32)

            
            embeddings_512[frame_num] = embedding_512
            embeddings_1024[frame_num] = embedding_1024
        
        print(f"Frame {frame_num}: '{combined_caption}' -> Embeddings created")
    
    return embeddings_512, embeddings_1024

def save_embeddings(embeddings_512, embeddings_1024, synced_captions, file_path):
    """
    Save embeddings and metadata to files.
    
    Args:
        embeddings_512: Dictionary of 512-dimensional embeddings
        embeddings_1024: Dictionary of 1024-dimensional embeddings
        synced_captions: Dictionary of synced captions
        file_path: Original video file path for naming
    """
    # Create output directory
    os.makedirs('embeddings', exist_ok=True)
    
    # Generate base filename from video path
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Save 512-dimensional embeddings
    embedding_data_512 = {
        'embeddings': embeddings_512,
        'captions': synced_captions,
        'dimension': 512,
        'video_file': file_path
    }
    
    with open(f'embeddings/{base_name}_embeddings_512.pkl', 'wb') as f:
        pickle.dump(embedding_data_512, f)
    
    # Save 1024-dimensional embeddings
    embedding_data_1024 = {
        'embeddings': embeddings_1024,
        'captions': synced_captions,
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
    Main processing function that runs YOLO and BLIP on video files and creates embeddings.
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
        
        # Run BLIP analysis
        print("\n🖼️  Running BLIP analysis...")
        try:
            blip_data = blip_main(file_path)
            print(f"BLIP generated {len(blip_data)} captions")
        except Exception as e:
            print(f"Error running BLIP: {e}")
            continue
        
        # Sync captions
        print("\n🔄 Syncing captions...")
        synced_captions = sync_captions(yolo_data, blip_data)
        print(f"Synced captions for {len(synced_captions)} frames")
        
        # Print some examples
        print("\nExample synced captions:")
        for i, (frame_num, captions) in enumerate(list(synced_captions.items())[:3]):
            print(f"  Frame {frame_num}: {captions}")
        
        # Create embeddings
        print("\n🧠 Creating embeddings...")
        try:
            embeddings_512, embeddings_1024 = create_embeddings(
                synced_captions, model_512, model_1024
            )
            print(f"Created embeddings for {len(embeddings_512)} frames")
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            continue
        
        # Save embeddings
        print("\n💾 Saving embeddings...")
        try:
            save_embeddings(embeddings_512, embeddings_1024, synced_captions, file_path)
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