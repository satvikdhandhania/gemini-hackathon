"""
Postproduction Agent Orchestrator

Takes individual video clips from production and stitches them into a final 9:16 vertical video.
Uses ffmpeg to normalize all clips to 1080x1920 (9:16) with black strips as needed.
Analyzes the final video with Gemini to add OST (On-Screen Text/Captions) for hook moments.
"""
import subprocess
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
import os
from google import genai
from google.genai import types


# Configure logger
logger = logging.getLogger(__name__)


def normalize_to_9_16(input_path: str, output_path: str) -> None:
    """
    Normalize a video to 9:16 aspect ratio (1080x1920) using black strips.

    Args:
        input_path: Path to input video
        output_path: Path to save normalized video

    Raises:
        Exception: If ffmpeg processing fails
    """
    try:
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "copy",
            "-y",  # Overwrite output
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Normalized video to 9:16: {output_path}")

    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to normalize video to 9:16: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg not found. Install ffmpeg to process videos.")


def stitch_videos(video_paths: List[str], output_path: str) -> None:
    """
    Stitch multiple videos together into a single video using ffmpeg concat.

    Args:
        video_paths: List of paths to normalized video files
        output_path: Path to save final stitched video

    Raises:
        Exception: If ffmpeg concatenation fails
    """
    try:
        # Create a temporary concat file for ffmpeg
        concat_file = Path(output_path).parent / "concat_list.txt"

        with open(concat_file, "w") as f:
            for video_path in video_paths:
                # ffmpeg concat requires format: file 'path'
                f.write(f"file '{video_path}'\n")

        # Concatenate videos
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Stitched {len(video_paths)} videos into: {output_path}")

        # Clean up concat file
        concat_file.unlink()

    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to stitch videos: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg not found. Install ffmpeg to stitch videos.")


def analyze_video_for_captions(video_path: str) -> List[Dict[str, Any]]:
    """
    Analyze the final video with Gemini to generate on-screen text/captions.

    Uses Gemini Flash to:
    1. Upload and analyze the video
    2. Identify hook moments and key points
    3. Generate caption text with timestamps
    4. Transcribe any speech for captions

    Args:
        video_path: Path to the stitched video to analyze

    Returns:
        List of caption dictionaries:
        [
            {
                "timestamp": 1.5,  # Time in seconds
                "duration": 2.0,   # Duration in seconds
                "text": "Hook text here",
                "position": "top" | "center" | "bottom",
                "style": "emphasis" | "normal"
            },
            ...
        ]

    Raises:
        ValueError: If GEMINI_API_KEY not set
        Exception: If video analysis fails
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Cannot analyze video without API key."
        )

    logger.info(f"Analyzing video for captions: {video_path}")

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    try:
        # Upload video to Gemini
        logger.info("Uploading video to Gemini for analysis...")
        video_file = client.files.upload(path=video_path)

        # Wait for video to be processed
        import time
        while video_file.state == "PROCESSING":
            logger.info("Waiting for video to be processed...")
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)

        if video_file.state == "FAILED":
            raise Exception("Video processing failed in Gemini")

        logger.info(f"Video uploaded and processed: {video_file.name}")

        # Create analysis prompt
        caption_prompt = """
Analyze this short-form vertical video and generate on-screen text (OST) captions to maximize engagement.

YOUR TASK:
1. Identify hook moments (attention-grabbing points)
2. Detect key message points that need emphasis
3. Transcribe any speech/voiceover for accessibility
4. Generate engaging caption text for each moment

OUTPUT FORMAT (JSON):
{
    "captions": [
        {
            "timestamp": 0.0,
            "duration": 2.5,
            "text": "HOOK TEXT HERE",
            "position": "top" | "center" | "bottom",
            "style": "emphasis" | "normal"
        },
        ...
    ]
}

CAPTION RULES:
- Keep text SHORT and PUNCHY (max 3-5 words per caption for emphasis)
- Full sentences allowed for speech transcription
- Position "top" for emphasis text, "bottom" for speech transcription
- Style "emphasis" for hook moments (bold/larger), "normal" for transcription
- Timestamps in seconds (decimal precision)
- Duration: how long the caption should display (typically 1.5-3 seconds)
- Place captions at beat drops, hook moments, and key message points
- Ensure captions enhance the video, don't distract

Respond ONLY with valid JSON.
"""

        # Analyze video with Gemini
        logger.info("Analyzing video content with Gemini Flash...")
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=video_file.uri,
                            mime_type=video_file.mime_type
                        ),
                        types.Part.from_text(text=caption_prompt)
                    ],
                ),
            ],
        )

        # Parse JSON response
        import json
        caption_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))

        captions = caption_data.get("captions", [])
        logger.info(f"Generated {len(captions)} captions")

        return captions

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Gemini caption response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Video caption analysis failed: {str(e)}")


def add_captions_to_video(video_path: str, captions: List[Dict[str, Any]], output_path: str) -> None:
    """
    Overlay captions onto the video using ffmpeg drawtext filter.

    Args:
        video_path: Path to input video
        captions: List of caption dictionaries from analyze_video_for_captions()
        output_path: Path to save video with captions

    Raises:
        Exception: If ffmpeg processing fails
    """
    if not captions:
        logger.info("No captions to add, copying video as-is")
        import shutil
        shutil.copy(video_path, output_path)
        return

    logger.info(f"Adding {len(captions)} captions to video...")

    try:
        # Build ffmpeg drawtext filter for each caption
        filters = []

        for idx, caption in enumerate(captions):
            text = caption["text"].replace("'", "\\'").replace(":", "\\:")
            timestamp = caption["timestamp"]
            duration = caption["duration"]
            position = caption.get("position", "top")
            style = caption.get("style", "normal")

            # Position mapping
            if position == "top":
                y_pos = "h*0.15"  # 15% from top
            elif position == "bottom":
                y_pos = "h*0.85"  # 85% from top (near bottom)
            else:  # center
                y_pos = "h*0.5"

            # Style settings
            if style == "emphasis":
                fontsize = 80
                fontcolor = "white"
                borderw = 4
            else:  # normal
                fontsize = 60
                fontcolor = "white"
                borderw = 3

            # Build drawtext filter with enable time range
            filter_str = (
                f"drawtext=text='{text}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize={fontsize}:"
                f"fontcolor={fontcolor}:"
                f"borderw={borderw}:"
                f"bordercolor=black:"
                f"x=(w-text_w)/2:"  # Center horizontally
                f"y={y_pos}:"
                f"enable='between(t,{timestamp},{timestamp + duration})'"
            )
            filters.append(filter_str)

        # Combine all filters
        vf_filter = ",".join(filters)

        # Run ffmpeg with all captions
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", vf_filter,
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Captions added successfully: {output_path}")

    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to add captions to video: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg not found. Install ffmpeg to add captions.")


def process_final_video(production_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process production results into a final 9:16 vertical video with captions.

    Steps:
    1. Extract video paths from successful production sections
    2. Normalize each video to 9:16 (1080x1920) with black strips
    3. Stitch all normalized videos together
    4. Analyze stitched video with Gemini to generate captions
    5. Add captions to final video
    6. Return final video path with captions

    Args:
        production_results: List of section results from production orchestrator
                          Each result has: section, format, output (with content_path)

    Returns:
        Dict containing:
            - final_video_path: Path to the final stitched 9:16 video
            - sections_processed: Number of sections included
            - sections_failed: Number of sections that failed

    Example input:
        [
            {
                "section": 0,
                "format": "talking_head",
                "output": {"content_path": "/app/output/talking_head/video1.mp4"}
            },
            {
                "section": 1,
                "format": "b_roll",
                "output": {"content_path": "/app/output/b_roll/video2.mp4"}
            }
        ]

    Example output:
        {
            "final_video_path": "/app/output/final_videos/final_1234567890.mp4",
            "sections_processed": 2,
            "sections_failed": 0
        }

    Raises:
        Exception: If no valid sections or video processing fails
    """
    logger.info(f"Starting postproduction: {len(production_results)} sections")

    # Create output directories
    output_dir = Path("/app/output/final_videos")
    normalized_dir = output_dir / "normalized"
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    # Extract valid video paths
    video_paths = []
    sections_failed = 0

    for result in production_results:
        if result.get("error"):
            logger.warning(f"Section {result['section']} failed: {result['error']}")
            sections_failed += 1
            continue

        output = result.get("output")
        if not output:
            logger.warning(f"Section {result['section']} has no output")
            sections_failed += 1
            continue

        content_path = output.get("content_path")
        if not content_path or not Path(content_path).exists():
            logger.warning(f"Section {result['section']} has invalid content_path: {content_path}")
            sections_failed += 1
            continue

        video_paths.append(content_path)

    if not video_paths:
        raise Exception("No valid video sections to process")

    logger.info(f"Processing {len(video_paths)} valid sections")

    # Normalize each video to 9:16
    normalized_paths = []

    for idx, video_path in enumerate(video_paths):
        try:
            normalized_path = str(normalized_dir / f"normalized_section_{idx}.mp4")

            logger.info(f"Normalizing section {idx} to 9:16...")
            normalize_to_9_16(video_path, normalized_path)

            normalized_paths.append(normalized_path)

        except Exception as e:
            logger.error(f"Failed to normalize section {idx}: {str(e)}")
            sections_failed += 1

    if not normalized_paths:
        raise Exception("Failed to normalize any video sections")

    # Stitch normalized videos together
    timestamp = int(time.time())
    stitched_video_path = str(output_dir / f"stitched_{timestamp}.mp4")

    logger.info(f"Stitching {len(normalized_paths)} normalized videos...")
    stitch_videos(normalized_paths, stitched_video_path)

    # Clean up normalized videos
    for normalized_path in normalized_paths:
        try:
            Path(normalized_path).unlink()
        except Exception as e:
            logger.warning(f"Failed to clean up {normalized_path}: {str(e)}")

    logger.info(f"Stitched video created: {stitched_video_path}")

    # Analyze video for captions
    logger.info("Analyzing video with Gemini for captions...")
    try:
        captions = analyze_video_for_captions(stitched_video_path)
        logger.info(f"Generated {len(captions)} captions")
    except Exception as e:
        logger.warning(f"Caption analysis failed: {str(e)}")
        logger.warning("Continuing without captions...")
        captions = []

    # Add captions to video
    final_video_path = str(output_dir / f"final_{timestamp}.mp4")

    logger.info("Adding captions to final video...")
    try:
        add_captions_to_video(stitched_video_path, captions, final_video_path)
        logger.info(f"Final video with captions created: {final_video_path}")

        # Clean up stitched video (without captions)
        try:
            Path(stitched_video_path).unlink()
        except Exception as e:
            logger.warning(f"Failed to clean up {stitched_video_path}: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to add captions: {str(e)}")
        logger.info("Using stitched video without captions as final video")
        final_video_path = stitched_video_path

    return {
        "final_video_path": final_video_path,
        "sections_processed": len(normalized_paths),
        "sections_failed": sections_failed,
        "captions_added": len(captions)
    }
