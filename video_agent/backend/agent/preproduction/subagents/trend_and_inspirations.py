"""
Trend and Inspirations module

Analyzes trending videos to identify:
1. Trending audio clips and their exact duration
2. Core content concept and style
"""
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from google import genai
from google.genai import types


def _inspiration_rag(prompt: str) -> Dict[str, Any]:
    """
    Analyze trending videos to extract concepts, audio patterns, and templates

    Args:
        prompt: Text prompt describing content intent/topic

    Returns:
        Dict containing:
        - most_memeable_music: The most memeable/repeatable audio identified
        - most_repeatable_template: The most repeatable content template
        - concept: Core content concept synthesized from videos
        - analyzed_videos: Number of videos analyzed

    Raises:
        ValueError: If GEMINI_API_KEY is not set
        Exception: If video analysis fails
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Cannot perform Inspiration RAG without API key."
        )

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Get trending videos directory
    trending_videos_dir = Path("/app/resources/trending_videos")

    # Check if directory exists
    if not trending_videos_dir.exists():
        raise Exception(
            f"Trending videos directory not found: {trending_videos_dir}. "
            "Cannot perform Inspiration RAG."
        )

    # Get all video files
    video_files = list(trending_videos_dir.glob("*.mp4")) + \
                  list(trending_videos_dir.glob("*.MP4"))

    if not video_files:
        raise Exception(
            f"No video files found in {trending_videos_dir}. "
            "Cannot perform Inspiration RAG."
        )

    # Analyze videos iteratively
    video_analyses = []

    # Analysis query for individual videos
    individual_analysis_query = """
Analyze this trending video and extract:

1. AUDIO & TIMESTAMPS:
   - Is there a specific music/audio track being used?
   - If yes, describe the audio (genre, vibe, any identifying features)
   - Is this audio repeatable/memeable?
   - **IMPORTANT**: What is the EXACT START TIMESTAMP (in seconds) where the memeable/key audio section begins?
   - What is the EXACT DURATION (in seconds) of the memeable audio section?
   - Example: "Memeable audio starts at 2.5 seconds, duration 11 seconds"

2. VIDEO INFLECTION POINTS:
   - What are the key visual moments/transitions? (provide timestamps in seconds)
   - When does the hook/climax occur? (provide timestamp)
   - When are the beat drops or major transitions? (provide timestamps)

3. CONCEPT:
   - What is the core content concept?
   - What message or idea is being conveyed?

4. TEMPLATE/FORMAT:
   - What is the content structure? (talking head, b-roll, dancing, animation, etc.)
   - What editing patterns are used?
   - Is there a repeatable template/format?

**CRITICAL**: Always provide specific timestamps in seconds. Be precise.
"""

    print(f"\nAnalyzing {min(len(video_files), 10)} trending videos...")

    for video_path in video_files[:10]:  # Analyze up to 10 videos
        try:
            print(f"  - Analyzing: {video_path.name}")

            # Upload video file - open file and upload
            with open(video_path, 'rb') as video_file:
                uploaded_file = client.files.upload(
                    file=video_file,
                    config={
                        "display_name": video_path.name,
                        "mime_type": "video/mp4"
                    }
                )

            # Wait for file to become ACTIVE
            print(f"    Waiting for {video_path.name} to be processed...")
            max_wait_seconds = 120  # Maximum wait time
            wait_start = time.time()

            while time.time() - wait_start < max_wait_seconds:
                # Get file status
                file_info = client.files.get(name=uploaded_file.name)

                if hasattr(file_info, 'state'):
                    if file_info.state == "ACTIVE":
                        print(f"    {video_path.name} is ready!")
                        break
                    elif file_info.state == "FAILED":
                        raise Exception(f"File processing failed for {video_path.name}")

                time.sleep(5)  # Wait 5 seconds before checking again
            else:
                raise Exception(f"Timeout waiting for {video_path.name} to become ACTIVE")

            # Create content with video
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type="video/mp4"
                        ),
                        types.Part.from_text(text=individual_analysis_query),
                    ],
                ),
            ]

            # Generate analysis
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=contents,
            )

            video_analyses.append({
                "video": video_path.name,
                "video_path": str(video_path),
                "analysis": response.text
            })

        except Exception as e:
            print(f"  - Error analyzing {video_path.name}: {str(e)}")
            video_analyses.append({
                "video": video_path.name,
                "error": str(e)
            })

    # Synthesize findings across all videos
    print("\nSynthesizing insights from all videos...")

    successful_analyses = [v for v in video_analyses if "error" not in v]

    if not successful_analyses:
        raise Exception("No videos were successfully analyzed")

    # Create synthesis prompt
    all_analyses_text = "\n\n".join([
        f"VIDEO: {v['video']}\nANALYSIS:\n{v['analysis']}"
        for v in successful_analyses
    ])

    synthesis_query = f"""
Based on the following analyses of {len(successful_analyses)} trending videos:

{all_analyses_text}

Now, synthesize and provide:

1. MOST MEMEABLE MUSIC:
   - Which audio/music appears most frequently or has the highest meme potential?
   - What is its exact duration in seconds?
   - Describe it clearly

2. MOST REPEATABLE TEMPLATE:
   - What content format/structure appears most often?
   - What makes it repeatable?
   - Describe the template pattern

3. CORE CONCEPT:
   - What is the common concept or theme across these videos?
   - How does this relate to: "{prompt}"

Be specific and actionable. Focus on what can be replicated.
"""

    synthesis_response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=synthesis_query)],
            ),
        ],
    )

    return {
        "synthesis": synthesis_response.text,
        "analyzed_videos": len(video_analyses),
        "successful_analyses": len(successful_analyses),
        "individual_analyses": video_analyses,
        "source": "trending_videos_analysis",
        "model": "gemini-flash-latest"
    }


def get_inspirations(
    prompt: str,
    image: str,  # Currently unused
    character_id: str,  # Currently unused
    sponsor_id: Optional[str] = None  # Currently unused
) -> Dict[str, Any]:
    """
    Analyze trending videos to identify memeable music and repeatable templates

    Args:
        prompt: Text prompt describing content intent/topic
        image: Image input (currently unused)
        character_id: UUID of the character (currently unused)
        sponsor_id: Optional UUID of sponsor (currently unused)

    Returns:
        Dict containing:
        - synthesis: Synthesized insights about most memeable music and repeatable template
        - analyzed_videos: Number of videos analyzed
        - successful_analyses: Number of successful analyses
        - individual_analyses: Detailed analysis of each video

    Raises:
        ValueError: If required environment variables not set
        Exception: If video analysis fails
    """
    try:
        result = _inspiration_rag(prompt)
        return result
    except Exception as e:
        # NO FALLBACKS - fail clearly per CLAUDE.md rules
        raise Exception(f"Inspiration RAG failed: {str(e)}") from e
