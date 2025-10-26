"""
Scriptwriting module

Generates scripts and section lists for the production agent with image and audio extraction.

CAPABILITIES:
- Script generation using Gemini Flash
- Image generation/editing using gemini-2.5-flash-image
- Audio extraction from trending videos (specific sections)
- Can create custom character poses and imaginary settings from inspiration videos

CRITICAL REMINDERS:
- NO hardcoded script templates
- NO fake if/else logic pretending to be AI
- Use REAL LLM APIs (Gemini) for intelligent script generation
- Fail with clear errors if service unavailable
"""
import os
import base64
import mimetypes
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from google import genai
from google.genai import types


def extract_audio_segment(
    video_path: str,
    start_time: float,
    duration: float,
    output_filename: Optional[str] = None
) -> str:
    """
    Extract a specific audio segment from a video file using ffmpeg

    Args:
        video_path: Path to the source video file
        start_time: Start time in seconds
        duration: Duration of audio segment in seconds
        output_filename: Optional filename (without extension) for output

    Returns:
        str: Path to the extracted audio file (.mp3)

    Raises:
        Exception: If audio extraction fails

    Example:
        # Extract 11 seconds of audio starting at 3 seconds
        audio_path = extract_audio_segment(
            video_path="/app/resources/trending_videos/video.mp4",
            start_time=3.0,
            duration=11.0,
            output_filename="memeable_music_clip"
        )
    """
    # Create output directory
    output_dir = Path("/app/output/extracted_audio")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    if not output_filename:
        video_name = Path(video_path).stem
        output_filename = f"{video_name}_{int(start_time)}s_{int(duration)}s"

    output_path = output_dir / f"{output_filename}.mp3"

    # Use ffmpeg to extract audio segment
    try:
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-q:a", "0",  # Best quality
            "-map", "a",  # Extract audio only
            "-y",  # Overwrite output file
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"Audio extracted: {output_path}")
        return str(output_path)

    except subprocess.CalledProcessError as e:
        raise Exception(f"Audio extraction failed: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg not found. Install ffmpeg to extract audio.")


def generate_image(
    prompt: str,
    character_image_url: Optional[str] = None,
    output_filename: Optional[str] = None
) -> str:
    """
    Generate or edit images using gemini-2.5-flash-image

    Can be used to:
    - Create custom character poses from existing character image
    - Generate imaginary settings/backgrounds from inspiration videos
    - Create scene compositions for video sections

    Args:
        prompt: Text description of the image to generate
        character_image_url: Optional URL to character image for reference/editing
        output_filename: Optional filename (without extension) for saved image

    Returns:
        str: Path to the generated image file

    Raises:
        ValueError: If GEMINI_API_KEY is not set
        Exception: If image generation fails

    Example:
        # Generate a new character pose
        image_path = generate_image(
            prompt="Alex pointing forward enthusiastically with a big smile",
            character_image_url="https://firebase.../alex.jpg",
            output_filename="alex_pointing"
        )

        # Generate a setting from inspiration
        image_path = generate_image(
            prompt="Modern minimalist office workspace with natural lighting, clean desk",
            output_filename="office_scene"
        )
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Cannot generate images without API key."
        )

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Build content parts
    parts = []

    # Add character image if provided
    if character_image_url:
        try:
            # Fetch the character image from URL
            import requests
            response = requests.get(character_image_url)
            response.raise_for_status()

            # Encode image data
            image_data = response.content

            # Add image part and prompt
            parts.append(types.Part.from_bytes(
                data=image_data,
                mime_type=response.headers.get('content-type', 'image/jpeg')
            ))
            parts.append(types.Part.from_text(
                text=f"Using this character image as reference. Generate: {prompt}"
            ))
        except Exception as e:
            print(f"[Image Generation] Warning: Could not fetch character image: {str(e)}")
            print(f"[Image Generation] Falling back to text-only generation")
            parts.append(types.Part.from_text(text=prompt))
    else:
        parts.append(types.Part.from_text(text=prompt))

    # Create content
    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]

    # Configure for image generation
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

    # Create output directory
    output_dir = Path("/app/output/generated_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Generate image
        file_index = 0
        generated_path = None

        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            # Check for image data
            if (chunk.candidates[0].content.parts[0].inline_data and
                chunk.candidates[0].content.parts[0].inline_data.data):

                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"

                # Use provided filename or generate one
                if output_filename:
                    file_name = f"{output_filename}_{file_index}" if file_index > 0 else output_filename
                else:
                    file_name = f"generated_image_{file_index}"

                file_path = output_dir / f"{file_name}{file_extension}"

                # Save image
                with open(file_path, "wb") as f:
                    f.write(data_buffer)

                print(f"Image saved to: {file_path}")
                generated_path = str(file_path)
                file_index += 1
            else:
                # Print any text responses
                if chunk.text:
                    print(f"[Image Generation] {chunk.text}")

        if not generated_path:
            raise Exception("No image was generated by gemini-2.5-flash-image")

        return generated_path

    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")


def generate_script(
    trend_output: Dict[str, Any],
    character_id: str,
    character_images: List[str]
) -> List[Dict[str, Any]]:
    """
    Generate script and production sections list (3-5 sections)

    Uses Gemini Flash to:
    1. Analyze trend insights (memeable music, templates, concepts)
    2. Create themed 3-5 section video script
    3. Generate custom images based on character images and theme
    4. Structure sections with appropriate formats

    Args:
        trend_output: Output from trend_and_inspirations.get_inspirations()
                     Contains: synthesis, analyzed_videos, individual_analyses
        character_id: UUID of the character (e.g., "alex_agentops_ai")
        character_images: List of character image URLs from Firestore

    Returns:
        List of 3-5 section dictionaries:
        [
            {
                "format": "talking_head" | "dancing_clip" | "b_roll",
                "characterid": "uuid-string",
                "instructions": "detailed instructions for this section",
                "additional_media": {
                    "character_image": "path or URL",
                    "voiceover": "text (5-15 words for clips)"
                }
            },
            ...
        ]

    Raises:
        ValueError: If GEMINI_API_KEY not set or invalid inputs
        Exception: If script generation fails

    Example Output:
        [
            {
                "format": "talking_head",
                "characterid": "alex_agentops_ai",
                "instructions": "Hey everyone! Today I'm sharing my top 3 productivity hacks...",
                "additional_media": {
                    "character_image": "/app/output/generated_images/alex_intro.png"
                }
            },
            {
                "format": "b_roll",
                "characterid": "",
                "instructions": "Modern minimalist workspace, morning sunlight, clean desk",
                "additional_media": {
                    "voiceover": "First, optimize your workspace"
                }
            },
            ...
        ]
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Cannot generate script without API key."
        )

    if not trend_output:
        raise ValueError("trend_output cannot be empty")

    if not character_images:
        raise ValueError("character_images list cannot be empty")

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Extract key insights from trend output
    synthesis = trend_output.get("synthesis", "")
    individual_analyses = trend_output.get("individual_analyses", [])

    # Get trending videos with paths
    trending_videos = [
        {"name": v["video"], "path": v.get("video_path", ""), "analysis": v.get("analysis", "")}
        for v in individual_analyses
        if "error" not in v and "video_path" in v
    ]

    print(f"\n[Scriptwriting] Found {len(trending_videos)} trending videos with analysis")

    # Create script generation prompt
    script_prompt = f"""
Based on the following trend analysis, create a viral short-form video script with 3-5 sections.

TREND INSIGHTS:
{synthesis}

TRENDING VIDEOS ANALYZED: {len(trending_videos)} videos
(Audio can be extracted from these videos if needed)

CHARACTER ID: {character_id}
CHARACTER IMAGES AVAILABLE: {len(character_images)} images

YOUR TASK:
1. Create a cohesive 3-5 section video script that leverages the trend insights
2. Each section should use one of these formats: talking_head, dancing_clip, or b_roll
3. Use the memeable music and repeatable template patterns identified
4. If memeable music was identified, specify which video to extract audio from
5. Ensure visceral intensity and peak moments
6. Generate custom images for sections using gemini-2.5-flash-image when needed

OUTPUT FORMAT (JSON):
{{
    "theme": "overall video theme based on trends",
    "audio_extraction": {{
        "needed": true/false,
        "video_index": 0-{len(trending_videos)-1} (index of video to extract from),
        "start_time": 0.0,
        "duration": 6.5 (duration in seconds, typically 3-10s for dancing clips)
    }},
    "sections": [
        {{
            "format": "talking_head" | "dancing_clip" | "b_roll",
            "characterid": "{character_id}" or "" (empty for b_roll),
            "instructions": "detailed instructions for this section",
            "voiceover": "5-15 words for clips, or full script for talking_head",
            "image_generation_prompt": "optional: describe custom image/scene to generate with gemini-2.5-flash-image"
        }},
        ...
    ]
}}

FORMAT SPECIFICATIONS AND RESTRICTIONS:

1. **talking_head**:
   - Input: character image + text to say
   - Output: Character speaking with lip-sync animation
   - Voice: Eleven Labs v3 (eleven_v3 model) generates audio from text
   - Text length: No strict limit (can be full sentences/paragraphs)
   - Uses fal-ai/infinitalk with image + audio
   - Can generate custom character pose using gemini-2.5-flash-image

2. **dancing_clip**:
   - Input: character image + action description + EXTRACTED AUDIO from trending videos
   - Output: Character performing rhythmic movement synchronized to music
   - Duration: 3-10 seconds (based on extracted audio length)
   - Audio: MUST use extracted memeable music from trending videos (audio drives the movement)
   - Optional voiceover: 5-15 words maximum (spoken over the music)
   - Voice: Eleven Labs v3 (eleven_v3 model) for optional voiceover only
   - Uses fal-ai/wan-25-preview with image + audio_url for rhythmic movement
   - Can generate custom character pose using gemini-2.5-flash-image
   - **IMPORTANT**: If using dancing_clip, audio_extraction MUST be needed=true

3. **b_roll**:
   - Input: scene description + optional voiceover
   - Output: AI-generated cinematic B-roll footage
   - Duration: 5 seconds, 1080p
   - Optional voiceover: 5-15 words maximum
   - Voice: Eleven Labs v3 (eleven_v3 model) for optional voiceover
   - Uses fal-ai WAN-25 Preview for video generation
   - Can generate custom scene/background using gemini-2.5-flash-image
   - No character needed (characterid should be empty string)

CRITICAL RULES:
- 3-5 sections total
- ALL voiceovers use Eleven Labs v3 (eleven_v3 model) exclusively
- dancing_clip REQUIRES extracted music from trending videos (audio drives rhythmic movement)
- Voiceovers for clips: 5-15 words MAXIMUM (dancing_clip, b_roll)
- talking_head: full text allowed (will be converted to speech)
- Focus on the peak moment (climax) per trend analysis
- Use audio-first approach if memeable music identified
- If memeable music exists, extract it from trending videos for dancing_clip
- Custom images can be generated for any format using gemini-2.5-flash-image
- Image generation prompts should reference character style and theme

Respond ONLY with valid JSON.
"""

    try:
        # Generate script using Gemini Flash
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=script_prompt)],
                ),
            ],
        )

        # Parse JSON response
        import json
        script_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))

        theme = script_data.get("theme", "")
        sections_data = script_data.get("sections", [])
        audio_extraction = script_data.get("audio_extraction", {})

        print(f"\n[Scriptwriting] Theme: {theme}")

        # Extract audio if needed
        extracted_audio_path = None
        if audio_extraction.get("needed") and trending_videos:
            video_index = audio_extraction.get("video_index", 0)
            start_time = audio_extraction.get("start_time", 0.0)
            duration = audio_extraction.get("duration", 11.0)

            if 0 <= video_index < len(trending_videos):
                video_path = trending_videos[video_index]["path"]
                print(f"[Scriptwriting] Extracting audio from video {video_index}: {trending_videos[video_index]['name']}")
                print(f"  Start: {start_time}s, Duration: {duration}s")

                extracted_audio_path = extract_audio_segment(
                    video_path=video_path,
                    start_time=start_time,
                    duration=duration,
                    output_filename=f"trending_audio_{theme.replace(' ', '_')}"
                )
                print(f"  ✓ Audio extracted: {extracted_audio_path}")

        print(f"[Scriptwriting] Generating {len(sections_data)} sections...")

        # Build section list with image generation
        sections = []
        for idx, section_data in enumerate(sections_data):
            section = {
                "format": section_data["format"],
                "characterid": section_data.get("characterid", ""),
                "instructions": section_data["instructions"],
                "additional_media": {}
            }

            # Add voiceover if specified
            if "voiceover" in section_data and section_data["voiceover"]:
                section["additional_media"]["voiceover"] = section_data["voiceover"]

            # Add extracted audio for dancing_clip (required for rhythmic movement)
            if section_data["format"] == "dancing_clip" and extracted_audio_path:
                section["additional_media"]["audio_path"] = extracted_audio_path
                print(f"  Section {idx+1}: Added extracted audio for rhythmic movement")

            # Generate custom image if prompt provided (for formats that need images)
            if "image_generation_prompt" in section_data and section_data["image_generation_prompt"]:
                print(f"  Section {idx+1}: Generating custom image...")

                # Use first character image as reference for character-based formats
                character_image_ref = character_images[0] if character_images and section_data["format"] in ["talking_head", "dancing_clip"] else None

                generated_image_path = generate_image(
                    prompt=section_data["image_generation_prompt"],
                    character_image_url=character_image_ref,
                    output_filename=f"section_{idx+1}_{section_data['format']}"
                )

                # Only add character_image for talking_head and dancing_clip
                if section_data["format"] in ["talking_head", "dancing_clip"]:
                    section["additional_media"]["character_image"] = generated_image_path
            elif section_data["format"] in ["talking_head", "dancing_clip"]:
                # Use original character image if no custom generation
                section["additional_media"]["character_image"] = character_images[0]

            sections.append(section)
            print(f"  ✓ Section {idx+1}: {section['format']}")

        print(f"\n[Scriptwriting] Generated {len(sections)} sections successfully")
        return sections

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Gemini script response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Script generation failed: {str(e)}")
