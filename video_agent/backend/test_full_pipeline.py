"""
Complete end-to-end test of the video generation pipeline

Tests the full flow:
1. Preproduction: Analyze trends → Generate script with images and audio
2. Production: Generate videos for each section (talking_head, dancing_clip, b_roll)
3. Postproduction: Stitch videos → Add captions → Final 9:16 video
"""
from agent.preproduction.subagents import trend_and_inspirations, scriptwriting
from agent.production import orchestrator as production_orchestrator
from agent.postproduction import orchestrator as postproduction_orchestrator
from google.cloud import firestore


def main():
    print("=" * 80)
    print("COMPLETE VIDEO GENERATION PIPELINE TEST")
    print("=" * 80)
    print()

    # Get character data
    db = firestore.Client()
    doc_ref = db.collection('email_users').document('alex_agentops_ai')
    doc = doc_ref.get()
    character_data = doc.to_dict()

    # Get character images
    image_ids = character_data.get('imageIds', [])
    character_images = []
    for image_id in image_ids:
        img_doc = db.collection('images').document(image_id).get()
        if img_doc.exists:
            download_url = img_doc.to_dict().get('downloadUrl')
            if download_url:
                character_images.append(download_url)

    print(f"Character: alex_agentops_ai")
    print(f"Images found: {len(character_images)}")
    print()

    # =========================================================================
    # PHASE 1: PREPRODUCTION
    # =========================================================================
    print("-" * 80)
    print("PHASE 1: PREPRODUCTION - Analyzing Trends & Generating Script")
    print("-" * 80)
    print()

    # Analyze trends
    print("Step 1: Analyzing trending videos...")
    trend_output = trend_and_inspirations.get_inspirations(
        prompt='Create a viral TikTok about productivity',
        image=character_images[0] if character_images else '',
        character_id='alex_agentops_ai'
    )

    print(f"✓ Analyzed {len(trend_output.get('individual_analyses', []))} trending videos")
    print()

    # Generate script
    print("Step 2: Generating script with custom images and audio extraction...")
    sections = scriptwriting.generate_script(
        trend_output=trend_output,
        character_id='alex_agentops_ai',
        character_images=character_images
    )

    print(f"✓ Generated {len(sections)} sections")
    print()

    for idx, section in enumerate(sections, 1):
        print(f"Section {idx}:")
        print(f"  Format: {section['format']}")
        print(f"  Character: {section.get('characterid', 'N/A')}")
        print(f"  Instructions: {section['instructions'][:60]}...")
        print(f"  Media: {list(section.get('additional_media', {}).keys())}")
    print()

    # =========================================================================
    # PHASE 2: PRODUCTION
    # =========================================================================
    print("-" * 80)
    print("PHASE 2: PRODUCTION - Generating Video Clips")
    print("-" * 80)
    print()

    print(f"Generating {len(sections)} video sections...")
    print("NOTE: This may take several minutes as videos are generated with fal.ai")
    print()

    production_results = production_orchestrator.process_sections(sections)

    print()
    print(f"✓ Production complete: {len(production_results)} sections processed")
    print()

    for result in production_results:
        if result.get('error'):
            print(f"  Section {result['section']} ({result['format']}): FAILED - {result['error']}")
        else:
            print(f"  Section {result['section']} ({result['format']}): SUCCESS")
            print(f"    → {result['output'].get('content_path', 'N/A')}")
    print()

    # =========================================================================
    # PHASE 3: POSTPRODUCTION
    # =========================================================================
    print("-" * 80)
    print("PHASE 3: POSTPRODUCTION - Stitching & Adding Captions")
    print("-" * 80)
    print()

    print("Step 1: Normalizing videos to 9:16...")
    print("Step 2: Stitching sections together...")
    print("Step 3: Analyzing video with Gemini for captions...")
    print("Step 4: Adding on-screen text captions...")
    print()

    final_result = postproduction_orchestrator.process_final_video(production_results)

    print()
    print("=" * 80)
    print("✓ PIPELINE COMPLETE!")
    print("=" * 80)
    print()
    print(f"Final video: {final_result['final_video_path']}")
    print(f"Sections processed: {final_result['sections_processed']}")
    print(f"Sections failed: {final_result['sections_failed']}")
    print(f"Captions added: {final_result['captions_added']}")
    print()
    print("=" * 80)

    return final_result


if __name__ == "__main__":
    main()
