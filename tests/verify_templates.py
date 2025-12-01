import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.prompt_manager import prompt_manager


def test_conversation_splitter_template():
    print("Testing conversation_splitter.j2...")
    try:
        rendered = prompt_manager.render("conversation_splitter.j2")
        assert "Attached is a snapshot from a group chat conversation" in rendered
        assert "Break the conversation into a list of topics" in rendered
        print("✅ conversation_splitter.j2 rendered successfully")
    except Exception as e:
        print(f"❌ Failed to render conversation_splitter.j2: {e}")
        sys.exit(1)


def test_quick_summary_template():
    print("\nTesting quick_summary.j2...")
    try:
        group_name = "Test Group"
        rendered = prompt_manager.render("quick_summary.j2", group_name=group_name)
        assert f'what happened in "{group_name}" group recently' in rendered
        assert "Write a quick summary of what happened" in rendered
        print("✅ quick_summary.j2 rendered successfully")
    except Exception as e:
        print(f"❌ Failed to render quick_summary.j2: {e}")
        sys.exit(1)


def test_link_spam_detector_template():
    print("\nTesting link_spam_detector.j2...")
    try:
        rendered = prompt_manager.render("link_spam_detector.j2")
        assert "whatsapp link spam detector" in rendered
        assert "score of 1-5" in rendered
        print("✅ link_spam_detector.j2 rendered successfully")
    except Exception as e:
        print(f"❌ Failed to render link_spam_detector.j2: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_conversation_splitter_template()
    test_quick_summary_template()
    test_link_spam_detector_template()
