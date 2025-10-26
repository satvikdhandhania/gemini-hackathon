from agent.production.formats.b_roll import generate_content
import uuid

def test_video_generation():
    try:
        # Test prompt with detailed scene description
        test_prompt = """A serene sunset scene in San Jose downtown, 
        showing the city skyline with modern buildings silhouetted against 
        the warm orange sky. Palm trees sway gently in the foreground, 
        creating a perfect California ambiance. The scene is cinematic and 
        professionally composed."""
        
        print("Starting video generation...")
        print("This may take a few minutes. Progress will be shown below:\n")
        
        result = generate_content(
            characterid=str(uuid.uuid4()),
            additional_media={},
            instructions=test_prompt
        )
        
        print("\n✓ Video generated successfully!")
        print(f"Output saved to: {result['content_path']}")
        print(f"Additional info: {result['additional_instructions']}")
        
    except Exception as e:
        print(f"\n✗ Error during video generation: {str(e)}")

if __name__ == "__main__":
    test_video_generation()
