"""
Example: Running Oscar Chatbot (R1 Agent)

Demonstrates customer service chatbot with evidence-backed responses.
"""

import sys
sys.path.append('..')
from dotenv import load_dotenv

load_dotenv()
import os

from src.agents.oscar_chatbot import OscarChatbot


def main():
    """Run Oscar chatbot example"""

    print("=" * 80)
    print("Air NZ Oscar Chatbot - R1 (Customer Service)")
    print("Evidence-backed customer service with verifiable citations")
    llm_real = bool(os.getenv("OPENAI_API_KEY"))
    print(f"LLM API mode: {'REAL (OPENAI_API_KEY detected)' if llm_real else 'MOCK (no OPENAI_API_KEY)'}")
    print("=" * 80)
    print()

    # Initialize Oscar chatbot
    chatbot = OscarChatbot()

    # Example queries
    queries = [
        "What is the checked baggage allowance for economy class?",
        "Can I change my flight booking?",
        "What are the cancellation fees?",
    ]

    session_id = "demo_session_001"

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Query {i}: {query}")
        print(f"{'=' * 80}\n")

        # Process query
        response = chatbot.process_query(
            query=query,
            user_id="demo_user_cs_agent",
            session_id=session_id
        )

        # Display response
        if response["success"]:
            print("✓ Response generated successfully\n")
            print(f"Answer:\n{response['answer']}\n")
            print(f"Citations:")
            for citation in response['citations']:
                print(f"  - {citation}")
            print(f"\nMetadata:")
            print(f"  Risk Tier: {response['metadata']['risk_tier']}")
            print(f"  Confidence: {response['metadata']['confidence']:.2%}")
            print(f"  Strategy: {response['metadata']['retrieval_strategy']}")
            print(f"  Trace ID: {response['metadata']['trace_id']}")
        elif response.get("escalated"):
            print("⚠ Query escalated to human agent\n")
            print(f"Reason: {response['reason']}")
            print(f"Message: {response['message']}")
        else:
            print("✗ Error occurred\n")
            print(f"Error: {response.get('error')}")
            print(f"Details: {response.get('details')}")

    print(f"\n{'=' * 80}")
    print("Demo completed")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
