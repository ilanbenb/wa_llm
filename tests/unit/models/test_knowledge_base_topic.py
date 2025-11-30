import pytest
from models.knowledge_base_topic import KBTopic


def test_kbtopic_creation():
    topic = KBTopic(
        id="topic1",
        group_jid="group@g.us",
        speakers="speaker1, speaker2",
        subject="Test Subject",
        summary="Test Summary",
        embedding=[0.1, 0.2, 0.3],
    )
    assert topic.id == "topic1"
    assert topic.embedding == [0.1, 0.2, 0.3]
