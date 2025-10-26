"""
Preproduction Agent Orchestrator

Orchestrates the preproduction workflow:
1. trend_and_inspirations: Analyze trends and get content inspirations
2. scriptwriting: Generate script and production sections

TODO: IMPLEMENTATION REQUIRED - Define exact input parameters
"""
import logging
from typing import Dict, Any, List, Optional

from .subagents import trend_and_inspirations, scriptwriting


# Configure logger
logger = logging.getLogger(__name__)


def run_preproduction(
    prompt: str,
    image: str,  # TODO: Clarify exact type - file path? bytes? URL?
    character_id: str,
    sponsor_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the complete preproduction workflow

    Executes two sequential steps:
    1. Get trends and inspirations
    2. Generate script and production sections

    TODO: FINALIZE INPUT PARAMETERS
    - Confirm exact image format (path? bytes? URL? base64?)
    - Add any additional parameters needed
    - Document exact input requirements

    Args:
        prompt: Text prompt describing content intent/topic
        image: Image input (TODO: clarify exact format)
        character_id: UUID of the character
        sponsor_id: Optional UUID of sponsor (if sponsored content)

    Returns:
        List of production sections in format expected by production agent:
        [
            {
                "format": "talking_head" | "animate" | "dancing_clip" | "b_roll",
                "characterid": "uuid-string",
                "instructions": "detailed instructions",
                "additional_media": {}
            },
            ...
        ]

    Raises:
        Exception: If any step fails (logged comprehensively)

    IMPORTANT:
    - Steps run sequentially: trends → scriptwriting
    - Errors are logged comprehensively
    - NO FALLBACKS - fail clearly if APIs unavailable
    - All AI/intelligence must use REAL APIs
    """
    try:
        logger.info(
            f"Starting preproduction workflow: character_id={character_id}, "
            f"sponsor_id={sponsor_id}, prompt_length={len(prompt)}"
        )

        # Step 1: Get trends and inspirations
        logger.info("Step 1/2: Getting trends and inspirations")
        trend_output = trend_and_inspirations.get_inspirations(
            prompt=prompt,
            image=image,
            character_id=character_id,
            sponsor_id=sponsor_id
        )
        logger.info("Step 1/2: Trends and inspirations completed")

        # Step 2: Generate script and sections
        logger.info("Step 2/2: Generating script and production sections")
        sections = scriptwriting.generate_script(
            trend_output=trend_output,
            character_id=character_id
        )
        logger.info(f"Step 2/2: Script generation completed - {len(sections)} sections created")

        # Validate output format
        if not isinstance(sections, list):
            raise ValueError(f"scriptwriting.generate_script must return a list, got {type(sections)}")

        for idx, section in enumerate(sections):
            if not isinstance(section, dict):
                raise ValueError(f"Section {idx} must be a dict, got {type(section)}")

            required_fields = ["format", "characterid", "instructions", "additional_media"]
            for field in required_fields:
                if field not in section:
                    raise ValueError(f"Section {idx} missing required field: {field}")

            valid_formats = ["talking_head", "animate", "dancing_clip", "b_roll"]
            if section["format"] not in valid_formats:
                raise ValueError(
                    f"Section {idx} has invalid format '{section['format']}'. "
                    f"Valid formats: {valid_formats}"
                )

        logger.info(f"Preproduction workflow completed successfully: {len(sections)} sections ready")
        return sections

    except Exception as e:
        logger.error(
            "Preproduction workflow failed",
            exc_info=True,
            extra={
                "character_id": character_id,
                "sponsor_id": sponsor_id,
                "prompt": prompt,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        )
        raise
