"""
Test script for Trends & Inspirations RAG operations
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.preproduction.subagents import trend_and_inspirations

def test_trends_inspiration():
    """Test trends and inspiration gathering for alex_agentops_ai"""

    print("=" * 70)
    print("Testing Trends & Inspirations RAG for alex_agentops_ai")
    print("=" * 70)

    # Test prompt
    test_prompt = "alex_agentops_ai"

    print(f"\nPrompt: {test_prompt}")
    print("\nGathering insights... (this may take 60-120 seconds)")
    print("-" * 70)

    try:
        # Get inspirations
        result = trend_and_inspirations.get_inspirations(
            prompt=test_prompt,
            image="",  # Unused for now
            character_id="test-character-id"  # Unused for now
        )

        print("\n" + "=" * 70)
        print("✅ RAG Operations Completed!")
        print("=" * 70)

        # Display results
        print("\n" + "-" * 70)
        print("INTERNET RAG (Gemini Google Search)")
        print("-" * 70)
        internet_rag = result.get("internet_rag", {})
        print(f"Model: {internet_rag.get('model')}")
        print(f"Source: {internet_rag.get('source')}")
        print(f"\nTrends:\n{internet_rag.get('trends', 'N/A')}")

        print("\n" + "-" * 70)
        print("INSPIRATION RAG (Trending Videos Analysis)")
        print("-" * 70)
        inspiration_rag = result.get("inspiration_rag", {})
        print(f"Model: {inspiration_rag.get('model')}")
        print(f"Source: {inspiration_rag.get('source')}")
        print(f"Videos Analyzed: {inspiration_rag.get('analyzed_videos')}")
        print(f"Successful Analyses: {inspiration_rag.get('successful_analyses')}")

        print("\nInsights from videos:")
        for idx, insight in enumerate(inspiration_rag.get('insights', [])[:3], 1):
            print(f"\n  Video {idx}: {insight.get('video')}")
            if 'error' in insight:
                print(f"  Error: {insight['error']}")
            else:
                analysis = insight.get('analysis', 'N/A')
                # Truncate long analyses
                if len(analysis) > 300:
                    analysis = analysis[:300] + "..."
                print(f"  Analysis: {analysis}")

        print("\n" + "-" * 70)
        print("COMBINED INSIGHTS")
        print("-" * 70)
        combined = result.get("combined_insights", {})
        print(f"RAG Operations Completed: {combined.get('rag_operations_completed')}")
        print(f"RAG Operations Skipped: {combined.get('rag_operations_skipped')}")
        print(f"Status: {combined.get('status')}")

        # Save results to file
        output_dir = Path("/app/../resources/test")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "trends_inspiration_alex_agentops_ai.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n✅ Full results saved to: {output_file}")

        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ Test failed: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_trends_inspiration()
