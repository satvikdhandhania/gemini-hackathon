"""
Dancing clip content generation module using fal-ai/wan-25-preview

This format takes a character image and audio (extracted from trending videos),
then creates a video with rhythmic movement based on the audio (3s to 10s clips).
"""
from typing import Dict, Any, Optional
import fal_client
import os
import requests
from pathlib import Path
from google.cloud import firestore

# Configure fal_client to use FAL_API_KEY
if not os.getenv("FAL_KEY") and os.getenv("FAL_API_KEY"):
    os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY")


def get_character_data(character_id: str) -> Dict[str, Any]:
    """Get character data from Firestore email_users collection with images"""
    db = firestore.Client()
    doc_ref = db.collection('email_users').document(character_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Character {character_id} not found in Firestore email_users collection")

    data = doc.to_dict()

    # Fetch image URLs from images collection
    image_ids = data.get('imageIds', [])
    image_urls = []

    for image_id in image_ids:
        img_doc = db.collection('images').document(image_id).get()
        if img_doc.exists:
            img_data = img_doc.to_dict()
            download_url = img_data.get('downloadUrl')
            if download_url:
                image_urls.append(download_url)

    data['imageUrls'] = image_urls
    if image_urls:
        data['imageUrl'] = image_urls[0]  # Primary image

    return data


def generate_content(
    characterid: str,
    additional_media: Dict[str, Any],
    instructions: str,
    previous_section_output: Optional[Dict[str, Any]] = None,
    previous_section_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate dancing clip content using fal-ai/wan-25-preview

    Flow:
    1. Get character image from Firestore or additional_media
    2. Get audio file path from additional_media (extracted from trending videos)
    3. Use fal-ai/wan-25-preview to create rhythmic movement video (3-10s)

    Args:
        characterid: UUID of the character
        additional_media: JSON object containing:
            - character_image (optional): URL to character image
            - audio_path (required): Path or URL to audio file for rhythmic movement
        instructions: Text describing the movement/action to perform
        previous_section_output: JSON output from previous section (if any)
        previous_section_format: Format of previous section (if any)

    Returns:
        Dict containing:
            - content_path: Path to generated dancing clip video
            - additional_instructions: Additional instructions for postproduction
    """
    print(f"\n[Dancing Clip] Starting generation for character: {characterid}")
    print(f"[Dancing Clip] Movement instructions: {instructions[:100]}...")

    # Get character data
    character_data = get_character_data(characterid)

    # Get character image
    character_image_url = additional_media.get('character_image')
    if not character_image_url and 'imageUrl' in character_data:
        character_image_url = character_data['imageUrl']

    if not character_image_url:
        raise ValueError(f"No character image found for {characterid}")

    # If character_image is a local file path, upload it to fal.ai
    if character_image_url.startswith('/app/'):
        print(f"[Dancing Clip] Uploading character image to fal.ai...")
        character_image_url = fal_client.upload_file(character_image_url)
        print(f"[Dancing Clip] Character image uploaded: {character_image_url}")

    # Get audio file (required for rhythmic movement)
    audio_path = additional_media.get('audio_path')
    if not audio_path:
        raise ValueError("Dancing clip requires audio_path in additional_media for rhythmic movement")

    print(f"[Dancing Clip] Character image: {character_image_url}")
    print(f"[Dancing Clip] Audio path: {audio_path}")

    # Upload audio to fal.ai for public access
    print(f"[Dancing Clip] Uploading audio to fal.ai...")
    audio_url = fal_client.upload_file(audio_path)
    print(f"[Dancing Clip] Audio uploaded: {audio_url}")

    # Calculate duration based on audio (WAN-25 supports 3-10 seconds)
    # For now, default to 5 seconds - can be made dynamic based on audio length
    duration = "5"

    print(f"[Dancing Clip] Generating video with fal-ai/wan-25-preview...")
    print(f"[Dancing Clip] Duration: {duration}s (WAN-25 supports 3-10s)")

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(f"[Dancing Clip] {log['message']}")

    # Generate dancing clip with rhythmic movement
    result = fal_client.subscribe(
        "fal-ai/wan-25-preview/image-to-video",
        arguments={
            "prompt": instructions,
            "image_url": character_image_url,
            "audio_url": audio_url,  # Audio drives the rhythmic movement
            "resolution": "1080p",
            "duration": duration,
            "negative_prompt": "low resolution, error, worst quality, low quality, defects, static, no movement",
            "enable_prompt_expansion": True,
            "enable_safety_checker": True
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    # Download the generated video
    video_url = result['video']['url']

    output_dir = Path("/app/output/dancing_clip")
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = output_dir / f"dancing_clip_{characterid}_{hash(instructions)}.mp4"

    print(f"[Dancing Clip] Downloading video from: {video_url}")
    video_response = requests.get(video_url)

    if video_response.status_code != 200:
        raise Exception(f"Failed to download video: {video_response.status_code}")

    with open(video_path, "wb") as f:
        f.write(video_response.content)

    print(f"[Dancing Clip] Video saved to: {video_path}")

    return {
        "content_path": str(video_path),
        "audio_path": audio_path,  # Pass audio path for post-production
        "additional_instructions": "Dancing clip with rhythmic movement generated successfully"
    }
