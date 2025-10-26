"""
B-roll content generator module

Uses fal.ai WAN-25 Preview model to create B-roll footage based on text instructions.
"""
import os
import pathlib
from typing import Dict, Any, Optional
import fal_client
import requests


def generate_content(
    characterid: str,
    additional_media: Dict[str, Any],
    instructions: str,
    previous_section_output: Optional[Dict[str, Any]] = None,
    previous_section_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate B-roll content using fal.ai WAN-25 Preview model

    Args:
        characterid: UUID of the character (currently unused)
        additional_media: Additional media data (currently unused)
        instructions: Text instructions for content generation
        previous_section_output: Output from previous section (currently unused)
        previous_section_format: Format of previous section (currently unused)

    Returns:
        Dict containing:
            - content_path: Path to generated video file
            - additional_instructions: Instructions for postproduction

    Raises:
        ValueError: If FAL_API_KEY is not set
        Exception: If video generation or download fails
    """
    # Validate API key
    api_key = os.getenv('FAL_API_KEY')
    if not api_key:
        raise ValueError(
            "FAL_API_KEY environment variable is not set. "
            "Cannot generate B-roll without API key."
        )

    # Set API key for fal_client
    os.environ['FAL_KEY'] = api_key

    # Create output directory
    output_dir = pathlib.Path("/app/output/b_roll")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Queue update callback for logging
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(f"[B-roll Generation] {log['message']}")

    try:
        # Generate video using fal.ai WAN-25 Preview
        result = fal_client.subscribe(
            "fal-ai/wan-25-preview/text-to-video",
            arguments={
                "prompt": instructions,
                "aspect_ratio": "16:9",
                "resolution": "1080p",
                "duration": "5",
                "negative_prompt": "low resolution, error, worst quality, low quality, defects",
                "enable_prompt_expansion": True,
                "enable_safety_checker": True
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        # Extract video URL from result
        if not result or 'video' not in result:
            raise Exception("fal.ai API response missing 'video' field")

        video_data = result['video']
        video_url = video_data['url'] if isinstance(video_data, dict) else video_data

        # Download video
        video_response = requests.get(video_url)
        if video_response.status_code != 200:
            raise Exception(
                f"Failed to download video from {video_url} with status {video_response.status_code}"
            )

        # Create sanitized filename from instructions
        sanitized_filename = "".join(
            c for c in instructions[:30]
            if c.isalnum() or c in (' ', '-', '_')
        ).strip().replace(' ', '_')

        output_path = output_dir / f"{sanitized_filename}.mp4"

        # Save video file
        output_path.write_bytes(video_response.content)

        return {
            "content_path": str(output_path),
            "additional_instructions": "B-roll video generated successfully using WAN-25 Preview"
        }

    except Exception as e:
        raise Exception(f"B-roll generation failed: {str(e)}")
