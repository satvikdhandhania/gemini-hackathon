"""
Talking head content generation module using fal-ai/infinitalk

This format takes a character image and text prompt, generates audio using
Eleven Labs v3, then creates a talking head video where the character speaks.
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


def generate_audio_with_elevenlabs(text: str, voice_id: str) -> str:
    """
    Generate audio using Eleven Labs v3 API

    Args:
        text: Text to convert to speech
        voice_id: Eleven Labs voice ID

    Returns:
        Path to generated audio file
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_v3",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Eleven Labs API error: {response.status_code} - {response.text}")

    # Save audio to file
    output_dir = Path("/app/output/audio")
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / f"tts_{voice_id}_{hash(text)}.mp3"

    with open(audio_path, "wb") as f:
        f.write(response.content)

    print(f"Audio generated: {audio_path}")
    return str(audio_path)


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
    Generate talking head content using fal-ai/infinitalk

    Flow:
    1. Get character image and voice ID from Firestore
    2. Generate audio from instructions using Eleven Labs v3
    3. Use fal-ai/infinitalk to create talking head video with image + audio

    Args:
        characterid: UUID of the character
        additional_media: JSON object containing:
            - character_image (optional): URL to character image
        instructions: Text that the character will say
        previous_section_output: JSON output from previous section (if any)
        previous_section_format: Format of previous section (if any)

    Returns:
        Dict containing:
            - content_path: Path to generated talking head video
            - additional_instructions: Additional instructions for postproduction
    """
    print(f"\n[Talking Head] Starting generation for character: {characterid}")
    print(f"[Talking Head] Instructions: {instructions[:100]}...")

    # Get character data
    character_data = get_character_data(characterid)
    voice_id = character_data.get('elevenLabsVoiceId')

    if not voice_id:
        raise ValueError(f"Character {characterid} missing elevenLabsVoiceId")

    # Get character image
    character_image_url = additional_media.get('character_image')
    if not character_image_url and 'imageUrl' in character_data:
        character_image_url = character_data['imageUrl']

    if not character_image_url:
        raise ValueError(f"No character image found for {characterid}")

    # If character_image is a local file path, upload it to fal.ai
    if character_image_url.startswith('/app/'):
        print(f"[Talking Head] Uploading character image to fal.ai...")
        character_image_url = fal_client.upload_file(character_image_url)
        print(f"[Talking Head] Character image uploaded: {character_image_url}")

    print(f"[Talking Head] Character image: {character_image_url}")
    print(f"[Talking Head] Voice ID: {voice_id}")

    # Generate audio using Eleven Labs v3
    print(f"[Talking Head] Generating audio with Eleven Labs v3...")
    audio_path = generate_audio_with_elevenlabs(instructions, voice_id)

    # Upload audio to fal.ai for public access
    print(f"[Talking Head] Uploading audio to fal.ai...")
    audio_url = fal_client.upload_file(audio_path)
    print(f"[Talking Head] Audio uploaded: {audio_url}")

    print(f"[Talking Head] Generating video with fal-ai/infinitalk...")

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(f"[Talking Head] {log['message']}")

    # Generate talking head video
    result = fal_client.subscribe(
        "fal-ai/infinitalk",
        arguments={
            "image_url": character_image_url,
            "audio_url": audio_url,
            "prompt": f"A person speaking: {instructions[:100]}",
            "resolution": "480p",
            "acceleration": "regular"
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    # Download the generated video
    video_url = result['video']['url']

    output_dir = Path("/app/output/talking_head")
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = output_dir / f"talking_head_{characterid}_{hash(instructions)}.mp4"

    print(f"[Talking Head] Downloading video from: {video_url}")
    video_response = requests.get(video_url)

    if video_response.status_code != 200:
        raise Exception(f"Failed to download video: {video_response.status_code}")

    with open(video_path, "wb") as f:
        f.write(video_response.content)

    print(f"[Talking Head] Video saved to: {video_path}")

    return {
        "content_path": str(video_path),
        "additional_instructions": "Talking head video generated successfully"
    }
