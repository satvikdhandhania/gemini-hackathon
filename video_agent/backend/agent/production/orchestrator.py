"""
Production Agent Orchestrator

Processes sections sequentially through format-specific content generators.
"""
import logging
from typing import List, Dict, Any, Optional

from .formats import talking_head, dancing_clip, b_roll


# Configure logger
logger = logging.getLogger(__name__)


# Map format names to their modules
FORMAT_MODULES = {
    "talking_head": talking_head,
    "dancing_clip": dancing_clip,
    "b_roll": b_roll,
}


def process_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process sections sequentially through their respective format generators.

    Args:
        sections: List of section definitions with format, characterid, instructions, and additional_media

    Returns:
        List of section outputs with section number, format, and output/error

    Example input:
        [
            {
                "format": "talking_head",
                "characterid": "uuid-string",
                "instructions": "text instructions",
                "additional_media": {}
            }
        ]

    Example output:
        [
            {
                "section": 0,
                "format": "talking_head",
                "output": {
                    "content_path": "path/to/content",
                    "additional_instructions": "..."
                }
            }
        ]
    """
    results = []
    previous_section_output: Optional[Dict[str, Any]] = None
    previous_section_format: Optional[str] = None

    for index, section in enumerate(sections):
        section_result = {
            "section": index,
            "format": section.get("format"),
            "output": None,
        }

        try:
            # Validate required fields
            format_type = section.get("format")
            if not format_type:
                raise ValueError("Missing required field: 'format'")

            if format_type not in FORMAT_MODULES:
                raise ValueError(
                    f"Invalid format '{format_type}'. Valid formats: {list(FORMAT_MODULES.keys())}"
                )

            characterid = section.get("characterid", "")

            # Only talking_head and dancing_clip require characterid
            if format_type in ["talking_head", "dancing_clip"] and not characterid:
                raise ValueError(f"Format '{format_type}' requires 'characterid'")

            instructions = section.get("instructions")
            if instructions is None:
                raise ValueError("Missing required field: 'instructions'")

            additional_media = section.get("additional_media")
            if additional_media is None:
                raise ValueError("Missing required field: 'additional_media'")

            # Get the format module and call generate_content
            format_module = FORMAT_MODULES[format_type]

            logger.info(
                f"Processing section {index}: format={format_type}, "
                f"characterid={characterid}, "
                f"has_previous={previous_section_output is not None}"
            )

            # Call the format's generate_content function
            output = format_module.generate_content(
                characterid=characterid,
                additional_media=additional_media,
                instructions=instructions,
                previous_section_output=previous_section_output,
                previous_section_format=previous_section_format,
            )

            section_result["output"] = output

            # Update previous section info for next iteration
            previous_section_output = output
            previous_section_format = format_type

            logger.info(f"Successfully processed section {index}")

        except Exception as e:
            # Log comprehensive error information
            logger.error(
                f"Failed to process section {index}",
                exc_info=True,
                extra={
                    "section_index": index,
                    "section_data": section,
                    "previous_section_format": previous_section_format,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )

            # Include error in result
            section_result["error"] = str(e)
            section_result["output"] = None

        results.append(section_result)

    logger.info(f"Completed processing {len(sections)} sections")
    return results
