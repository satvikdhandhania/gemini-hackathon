# Production Agent Handoff Format

## Input Format

The production agent receives a JSON list of sections to process sequentially.

### Input Schema

```json
[
  {
    "format": "talking_head",
    "characterid": "uuid-string",
    "instructions": "text instructions for content generation",
    "additional_media": {}
  },
  {
    "format": "animate",
    "characterid": "uuid-string",
    "instructions": "text instructions for content generation",
    "additional_media": {}
  }
]
```

### Input Fields

- **format** (string, required): The content format type. Valid values:
  - `"talking_head"`
  - `"animate"`
  - `"dancing_clip"`
  - `"b_roll"`

- **characterid** (string, required): UUID of the character

- **instructions** (string, required): Text instructions for content generation

- **additional_media** (object, required): JSON object containing additional media
  - Structure varies by format (to be defined per format implementation)

## Output Format

The orchestrator returns a JSON list of section outputs.

### Output Schema

```json
[
  {
    "section": 0,
    "format": "talking_head",
    "output": {
      "content_path": "path/to/generated/content",
      "additional_instructions": "instructions for postproduction"
    }
  },
  {
    "section": 1,
    "format": "animate",
    "output": {
      "content_path": "path/to/generated/content",
      "additional_instructions": "instructions for postproduction"
    }
  }
]
```

### Output Fields

- **section** (integer): Zero-indexed section number
- **format** (string): The format type that was processed
- **output** (object): Output from the format's `generate_content()` function
  - **content_path** (string): Path to the generated content
  - **additional_instructions** (string/object): Additional instructions for postproduction agent

### Error Output

If a section fails, the output will include error information:

```json
{
  "section": 1,
  "format": "animate",
  "error": "Error message describing what went wrong",
  "output": null
}
```

## Processing Rules

1. **Sequential Processing**: Sections are processed in order (0, 1, 2, ...)

2. **Previous Section Context**: Each section receives:
   - `previous_section_output`: The output from the previous section (or `null` for first section)
   - `previous_section_format`: The format type of the previous section (or `null` for first section)

3. **Error Handling**:
   - Errors are logged comprehensively
   - In development: Errors are returned in output
   - In production: Retry logic will be implemented before failing
   - **NO FALLBACKS**: System fails clearly rather than using fake/placeholder data

4. **No Assumptions**: All required fields must be provided. Missing or invalid data causes clear failures.
