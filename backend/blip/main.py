from utils import read_video
import random
import numpy as np

def generate_football_caption():
    """Generate a random football-related caption"""
    captions = [
        "Player passes the ball to teammate",
        "Player tackles opponent to win possession", 
        "Player dribbles past defender",
        "Player shoots towards goal",
        "Goalkeeper makes a save",
        "Player crosses the ball into the box",
        "Player intercepts the pass",
        "Player commits a foul",
        "Player runs with the ball",
        "Player heads the ball away"
    ]
    return random.choice(captions)

def main():
    # Read Video
    video_frames = read_video('input_videos/08fd33_4.mp4')
    
    print(f"Processing video with {len(video_frames)} frames...")
    
    # Generate captions every 5 frames
    indexed_data = []
    caption_frames = range(0, len(video_frames), 5)  # Every 5th frame
    
    for frame_num in caption_frames:
        # Generate random caption
        caption = generate_football_caption()
        
        # Create metadata entry
        metadata_entry = {
            "frame_num": frame_num,
            "timestamp": frame_num / 30.0,  # Assuming 30fps
            "caption": caption,
            "confidence": round(random.uniform(0.7, 0.95), 2),  # Random confidence score
            "source": "BLIP_simulation"
        }
        
        indexed_data.append(metadata_entry)
        print(f"Frame {frame_num} ({metadata_entry['timestamp']:.2f}s): {caption}")
    
    print(f"\nGenerated {len(indexed_data)} captions for video analysis")
    return indexed_data

if __name__ == '__main__':
    result = main()
    
    # Print summary
    print("\nSample metadata entries:")
    for i, entry in enumerate(result[:3]):  # Show first 3 entries
        print(f"{i+1}. Frame {entry['frame_num']}: '{entry['caption']}'")