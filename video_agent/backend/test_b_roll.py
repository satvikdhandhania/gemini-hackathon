"""
Test script for B-roll generation with WAN-25 Preview
"""
import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.production.formats import b_roll

def test_b_roll_generation():
    """Test B-roll generation and save to resources/test"""

    print("=" * 60)
    print("Testing B-roll Generation with WAN-25 Preview")
    print("=" * 60)

    # Test prompt
    test_prompt = "A serene sunset over the ocean with gentle waves, cinematic lighting, golden hour"

    print(f"\nPrompt: {test_prompt}")
    print("\nGenerating video... (this may take 30-60 seconds)")
    print("-" * 60)

    try:
        # Generate b-roll content
        result = b_roll.generate_content(
            characterid="test-character-id",
            additional_media={},
            instructions=test_prompt,
            previous_section_output=None,
            previous_section_format=None
        )

        print("-" * 60)
        print("\n✅ Video generated successfully!")
        print(f"Original path: {result['content_path']}")
        print(f"Message: {result['additional_instructions']}")

        # Create resources/test directory
        test_dir = Path("/app/../resources/test")
        test_dir.mkdir(parents=True, exist_ok=True)

        # Copy video to resources/test
        source_path = Path(result['content_path'])
        if source_path.exists():
            destination_path = test_dir / "sample_b_roll_wan25.mp4"
            shutil.copy(source_path, destination_path)
            print(f"\n✅ Video copied to: {destination_path}")

            # Get file size
            file_size = destination_path.stat().st_size / (1024 * 1024)  # MB
            print(f"File size: {file_size:.2f} MB")
        else:
            print(f"\n⚠️  Warning: Generated video not found at {source_path}")

        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {str(e)}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    test_b_roll_generation()
