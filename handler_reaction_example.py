#!/usr/bin/env python3
"""
Example demonstrating the updated BaseHandler with reaction support

This shows how the BaseHandler now handles both messages and reactions
from WhatsApp webhook payloads.
"""


async def example_handler_usage():
    """
    Example showing how the updated BaseHandler processes webhooks.

    Note: This is a conceptual example - in practice you'd have real
    database session, WhatsApp client, and embedding client instances.
    """
    print("🚀 BaseHandler Reaction Support Example")
    print("=" * 50)

    # In real usage, you'd have actual instances:
    # handler = BaseHandler(session, whatsapp_client, embedding_client)

    # Example 1: Processing a message webhook
    print("\n📱 Processing message webhook:")
    print("   From: 1234567890@s.whatsapp.net in 987654321@g.us")
    print("   Message: Hello everyone! 👋")
    print("   Timestamp: 2024-01-16T10:30:00Z")

    # In real usage:
    # stored_message = await handler.store_message(message_payload)
    # print(f"   Stored message ID: {stored_message.message_id}")

    # Example 2: Processing a reaction webhook
    print("\n💖 Processing reaction webhook:")
    print("   From: 0987654321@s.whatsapp.net in 987654321@g.us")
    print("   Reacting to message: msg_123456789")
    print("   Reaction emoji: ❤️")
    print("   Timestamp: 2024-01-16T10:35:00Z")

    # In real usage:
    # result = await handler.store_message(reaction_payload)
    # print(f"   Result: {result}")  # Would be None for reactions

    # Example 3: What happens inside the handler
    print("\n🔧 What happens inside the handler:")
    print("   1. Handler receives webhook payload")
    print("   2. Checks if payload contains reaction or message")
    print("   3. For reactions:")
    print("      - Calls store_reaction() method")
    print("      - Ensures sender exists in database")
    print("      - Checks if message being reacted to exists")
    print("      - Updates existing reaction or creates new one")
    print("      - Returns None (no message to return)")
    print("   4. For messages:")
    print("      - Calls existing message storage logic")
    print("      - Returns stored Message object")

    # Example 4: Reaction management
    print("\n🗑️ Reaction management:")
    print("   - Remove reaction: handler.remove_reaction(message_id, sender_jid)")
    print("   - Update reaction: Automatically handled by store_reaction()")
    print("   - Query reactions: Access via message.reactions relationship")


def demonstrate_reaction_scenarios():
    """Show different reaction scenarios."""
    print("\n🎭 Reaction Scenarios:")
    print("=" * 30)

    scenarios = [
        {
            "name": "New Reaction",
            "description": "User reacts to a message for the first time",
            "action": "Creates new reaction in database",
        },
        {
            "name": "Update Reaction",
            "description": "User changes their reaction on a message",
            "action": "Updates existing reaction with new emoji",
        },
        {
            "name": "Remove Reaction",
            "description": "User removes their reaction",
            "action": "Deletes reaction from database",
        },
        {
            "name": "Orphaned Reaction",
            "description": "Reaction to a message we don't have",
            "action": "Logs warning but still stores reaction",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}:")
        print(f"   Scenario: {scenario['description']}")
        print(f"   Action: {scenario['action']}")


if __name__ == "__main__":
    print("BaseHandler Reaction Support - Examples and Usage")
    print("=" * 60)

    # Run examples
    import asyncio

    asyncio.run(example_handler_usage())

    demonstrate_reaction_scenarios()

    print("\n✅ Integration Guide:")
    print("1. Update your webhook endpoint to use the enhanced store_message()")
    print("2. The method automatically detects message vs reaction payloads")
    print("3. Messages are stored normally, reactions are handled separately")
    print("4. Use message.reactions to access reactions for a message")
    print("5. Use sender.reactions to access all reactions by a sender")
    print("6. Database constraints prevent duplicate reactions")
    print("7. Reaction updates are handled automatically")

    print("\n🔍 Database Queries:")
    print("- Get message reactions: SELECT * FROM reaction WHERE message_id = ?")
    print("- Get user reactions: SELECT * FROM reaction WHERE sender_jid = ?")
    print("- Popular reactions: SELECT emoji, COUNT(*) FROM reaction GROUP BY emoji")
    print("- Recent reactions: SELECT * FROM reaction ORDER BY timestamp DESC")
