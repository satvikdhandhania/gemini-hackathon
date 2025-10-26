# Production Formats

This document describes the available video content formats and their capabilities.

## Overview

The production agent supports 3 simple video content formats:

1. **talking_head** - Character image speaks a text prompt
   - Input: character image + text to say
   - Output: talking head video with speech
   - Voice: Eleven Labs v3 (eleven_v3 model) for TTS

2. **dancing_clip** - Character image performs simple action with voiceover
   - Input: character image + action prompt + voiceover (5-15 words, no music)
   - Output: action clip with voiceover narration
   - Voice: Eleven Labs v3 (eleven_v3 model) for voiceover

3. **b_roll** - AI-generated cinematic footage with optional voiceover
   - Input: scene description + optional voiceover (5-15 words)
   - Output: AI-generated B-roll video (5 seconds, 1080p)
   - Voice: Eleven Labs v3 (eleven_v3 model) for optional voiceover

**All voiceover generation uses Eleven Labs v3 API with the `eleven_v3` model.**

Each format implements a standardized `generate_content()` function interface.

---

## Format: `talking_head`

### Description
Simple talking head video where a character image speaks a given text prompt. The character's mouth/face is animated to match the spoken text.

### Capabilities
- Takes a single character image and makes it speak
- Converts text to speech with lip-sync animation
- Simple, straightforward text-to-speech video generation

### Required Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `characterid` | `str` | Yes | UUID of the character from Firestore `email_users` collection |
| `additional_media` | `Dict[str, Any]` | Yes | JSON object containing the character image |
| `instructions` | `str` | Yes | Text prompt - what the character should say |
| `previous_section_output` | `Dict[str, Any]` | No | Output from previous section (for multi-section videos) |
| `previous_section_format` | `str` | No | Format type of previous section |

### Additional Media Structure

```python
{
    "character_image": "https://firebasestorage.googleapis.com/...image.jpg"  # Single image
}
```

### Example Usage

```python
result = talking_head.generate_content(
    characterid="alex_agentops_ai",
    additional_media={
        "character_image": "https://firebasestorage.googleapis.com/.../alex.jpg"
    },
    instructions="Hey everyone, today I want to share three productivity tips that changed my life.",
    previous_section_output=None,
    previous_section_format=None
)
```

### Output

```python
{
    "content_path": "/app/output/talking_head/video_xyz.mp4",
    "additional_instructions": "Talking head video generated"
}
```

### Implementation Status
⚠️ **PLACEHOLDER** - Implementation pending

---

## Format: `dancing_clip`

### Description
Simple action/movement clip where a character image performs a prompted action with voiceover narration. No music - just simple voiceover describing what's happening.

### Capabilities
- Takes a character image and animates a simple action/movement
- Adds simple voiceover narration (no music/audio track)
- Creates short action clips with spoken description

### Required Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `characterid` | `str` | Yes | UUID of the character from Firestore `email_users` collection |
| `additional_media` | `Dict[str, Any]` | Yes | JSON object containing the character image |
| `instructions` | `str` | Yes | Action prompt + simple voiceover (5-15 words max) |
| `previous_section_output` | `Dict[str, Any]` | No | Output from previous section (for multi-section videos) |
| `previous_section_format` | `str` | No | Format type of previous section |

### Additional Media Structure

```python
{
    "character_image": "https://firebasestorage.googleapis.com/...image.jpg",  # Single image
    "voiceover": "Watch this amazing move"  # Simple voiceover (5-15 words)
}
```

### Instructions Format

The `instructions` parameter should contain:
- **Action prompt**: What the character should do (e.g., "wave hand", "point up", "nod head")
- **Voiceover text**: Simple narration (5-15 words max)

Example:
```
Action: Point to the sky enthusiastically
Voiceover: Look at this incredible opportunity
```

### Example Usage

```python
result = dancing_clip.generate_content(
    characterid="alex_agentops_ai",
    additional_media={
        "character_image": "https://firebasestorage.googleapis.com/.../alex.jpg",
        "voiceover": "Check out this amazing productivity hack"
    },
    instructions="Action: Point forward with excitement",
    previous_section_output=None,
    previous_section_format=None
)
```

### Output

```python
{
    "content_path": "/app/output/dancing_clip/video_xyz.mp4",
    "additional_instructions": "Action clip with voiceover generated"
}
```

### Use Cases
- Quick action sequences with narration
- Character gestures/movements
- Transitional clips between sections
- Simple animated reactions

### Constraints
- **No music/audio tracks** - voiceover only
- **Simple actions only** - basic gestures and movements
- **Short voiceover** - maximum 5-15 words

### Implementation Status
⚠️ **PLACEHOLDER** - Implementation pending

---

## Format: `b_roll`

### Description
Generates AI-created cinematic B-roll video footage from text descriptions using fal.ai's WAN-25 Preview model. Can include optional voiceover narration (5-15 words max).

### Capabilities
- Text-to-video generation using AI (WAN-25 Preview)
- Creates cinematic, high-quality video clips
- Optional simple voiceover (5-15 words max)
- 1080p resolution, 16:9 aspect ratio
- 5-second duration clips
- Prompt expansion for enhanced visual quality
- Safety checking enabled

### Required Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `characterid` | `str` | No (unused) | Character ID (kept for interface consistency) |
| `additional_media` | `Dict[str, Any]` | Yes (optional voiceover) | Optional voiceover text (5-15 words max) |
| `instructions` | `str` | Yes | Detailed text description of desired video content |
| `previous_section_output` | `Dict[str, Any]` | No (unused) | Previous section output (kept for interface consistency) |
| `previous_section_format` | `str` | No (unused) | Previous section format (kept for interface consistency) |

### Additional Media Structure

```python
{
    "voiceover": "Here's how you can transform your workspace"  # Optional (5-15 words)
}
```

### Instructions Format

The `instructions` parameter should contain a detailed visual description:

```
A serene sunset over the ocean with gentle waves, cinematic lighting, golden hour
```

Best practices:
- Be specific about visuals (colors, lighting, mood)
- Include camera angles if relevant
- Mention style (cinematic, documentary, etc.)
- Specify time of day, weather, atmosphere
- Avoid text or specific people (AI limitation)

### Example Usage

**Without voiceover:**
```python
result = b_roll.generate_content(
    characterid="",
    additional_media={},
    instructions="A serene sunset over the ocean with gentle waves, cinematic lighting, golden hour",
    previous_section_output=None,
    previous_section_format=None
)
```

**With voiceover:**
```python
result = b_roll.generate_content(
    characterid="",
    additional_media={
        "voiceover": "This is where productivity happens"
    },
    instructions="Modern minimalist office workspace with natural lighting, clean desk setup",
    previous_section_output=None,
    previous_section_format=None
)
```

### Output

```python
{
    "content_path": "/app/output/b_roll/A_serene_sunset_over_the_ocean.mp4",
    "additional_instructions": "B-roll video generated successfully using WAN-25 Preview"
}
```

### Technical Specifications
- **Model**: fal.ai WAN-25 Preview
- **Resolution**: 1080p
- **Aspect Ratio**: 16:9
- **Duration**: 5 seconds
- **Format**: MP4
- **API**: fal_client library

### Environment Requirements
- `FAL_API_KEY` environment variable must be set

### Implementation Status
✅ **FULLY IMPLEMENTED** - Working and tested

---

## Voiceover Generation

All voiceover audio is generated using **Eleven Labs v3 API** with the `eleven_v3` model.

### Configuration

```python
{
    "model": "eleven_v3",  # Eleven Labs v3 model
    "voice_id": "...",  # Retrieved from character's voiceIds in Firestore
    "text": "Text to speak",  # 5-15 words for clips, longer for talking heads
    "optimize_streaming_latency": 0,
    "output_format": "mp3_44100_128"
}
```

### Environment Requirements
- `ELEVEN_LABS_API_KEY` environment variable must be set

### Voice Selection
- Voice ID is stored in the character's Firestore document under `elevenLabsVoiceId`
- For now, use any available Eleven Labs voice (no need to retrieve from character)
- Default voice ID: `taMqu5kS7VAwVTOJZFS0` (saved to alex_agentops_ai)

---

## Common Interface

All formats implement the same function signature:

```python
def generate_content(
    characterid: str,
    additional_media: Dict[str, Any],
    instructions: str,
    previous_section_output: Optional[Dict[str, Any]] = None,
    previous_section_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate content in this format

    Returns:
        Dict containing:
            - content_path: Absolute path to generated video file
            - additional_instructions: Instructions for postproduction agent

    Raises:
        ValueError: If required inputs are missing
        Exception: If content generation fails
    """
```

## Character Data from Firestore

Character data is retrieved from the `email_users` collection in Firestore:

```python
{
    "email": "alex@agentops.ai",
    "displayName": "Alex AgentOps",
    "imageIds": ["zslfqbhEbwtCdi9VR2K8", "2dQr2icFZEs2kSOSw6um"],
    "voiceIds": ["..."],
    "contentOpinion": "...",
    "speakingStyle": "...",
    "guardrails": "No racism or dicey content"
}
```

Images are stored separately in the `images` collection:

```python
{
    "downloadUrl": "https://firebasestorage.googleapis.com/...",
    "status": "processed"
}
```

## Error Handling

All formats follow these error handling principles:

1. **No Fallbacks** - Fail clearly rather than using fake/default data
2. **Validate Inputs** - Check required environment variables and parameters
3. **Clear Error Messages** - Provide actionable error information
4. **Raise Exceptions** - Don't silently fail or return partial results

Example:

```python
api_key = os.getenv('FAL_API_KEY')
if not api_key:
    raise ValueError(
        "FAL_API_KEY environment variable is not set. "
        "Cannot generate B-roll without API key."
    )
```

## Future Enhancements

### Talking Head (Placeholder - Needs Implementation)
- Integrate D-ID, Heygen, or similar TTS + lip-sync API
- Integrate Eleven Labs v3 (`eleven_v3` model) for TTS
- Retrieve voice ID from character's `voiceIds` in Firestore
- Add emotion/expression control
- Support variable video duration based on text length

### Dancing Clip (Placeholder - Needs Implementation)
- Integrate runway, kling, or similar motion/animation API
- Integrate Eleven Labs v3 (`eleven_v3` model) for voiceover
- Expand action library (gestures, movements, reactions)
- Support simple actions: wave, point, nod, etc.
- Retrieve voice ID from character's `voiceIds` in Firestore

### B-Roll (Partially Implemented)
- **TODO**: Integrate Eleven Labs v3 for voiceover overlay
- **TODO**: Combine generated video with voiceover audio
- Support longer durations (10s, 15s, 30s)
- Add style consistency across multiple B-roll clips
- Support image-to-video transformations
- Retrieve voice ID from character's `voiceIds` in Firestore
