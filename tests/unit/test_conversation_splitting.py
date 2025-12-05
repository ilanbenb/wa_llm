import pytest
from datetime import datetime, timedelta
from src.load_new_kbtopics import split_messages


# Mock Message class since strictly typed object creation might be complex depending on deps
class MockMessage:
    def __init__(self, message_id, timestamp):
        self.message_id = message_id
        self.timestamp = timestamp
        # attributes needed for sorting or other logic if any


@pytest.fixture
def create_messages():
    def _create(times_offsets):
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        return [
            MockMessage(f"msg_{i}", base_time + timedelta(hours=offset))
            for i, offset in enumerate(times_offsets)
        ]

    return _create


def test_split_by_time_gap(create_messages):
    # 3 messages close together, then a 3 hour gap, then 2 messages
    # Gap is 2 hours by default
    offsets = [0, 0.1, 0.2, 3.5, 3.6]
    messages = create_messages(offsets)

    # Use min_size=1 to prevent merging of segments
    chunks = split_messages(messages, gap_hours=2.0, min_size=1)

    assert len(chunks) == 2
    assert len(chunks[0]) == 3
    assert len(chunks[1]) == 5  # 3 overlap + 2 new
    assert (
        chunks[1][0].message_id == "msg_0"
    )  # First message of overlap (which is first msg of chunk 0)
    # Wait, chunk 0 is [msg_0, msg_1, msg_2].
    # Overlap 5. Previous chunk has 3. Takes all 3.
    # So chunk 1 starts with msg_0. Correct.


def test_split_by_time_gap_no_overlap(create_messages):
    offsets = [0, 0.1, 3.5]
    messages = create_messages(offsets)
    # Set overlap to 0
    chunks = split_messages(messages, gap_hours=2.0, overlap=0, min_size=1)
    assert len(chunks) == 2
    assert len(chunks[0]) == 2
    assert len(chunks[1]) == 1


def test_merge_small_segments(create_messages):
    # 1 msg, gap, 1 msg, gap, 1 msg. All gaps > 2 hours.
    # Should result in 3 segments.
    # But min_size is 25. So they should all merge into one buffer?
    # buffer starts with segment 1. len < 25.
    # extends with segment 2. len < 25.
    # extends with segment 3. len < 25.
    # ends. adds buffer.
    # So 1 chunk total.
    offsets = [0, 3, 6]
    messages = create_messages(offsets)
    # min_size=5 ensures they merge (since 1 < 5)
    chunks = split_messages(messages, gap_hours=2.0, min_size=5)
    assert len(chunks) == 1
    assert len(chunks[0]) == 3


def test_split_max_size(create_messages):
    # 10 messages in 1 hour. No initial split.
    # max_size = 4
    offsets = [i * 0.1 for i in range(10)]
    messages = create_messages(offsets)

    chunks = split_messages(messages, gap_hours=2.0, max_size=4, overlap=0, min_size=1)

    # Total 10. Max 4.
    # Chunk 1: 4
    # Chunk 2: 4
    # Chunk 3: 2
    assert len(chunks) == 3
    assert len(chunks[0]) == 4
    assert len(chunks[1]) == 4
    assert len(chunks[2]) == 2


def test_empty_list():
    assert split_messages([]) == []
