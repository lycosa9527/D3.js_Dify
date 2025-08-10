#!/usr/bin/env python3
"""
Example usage of the new simplified concept map generation approach.

This shows how to replace the old unreliable unified approach with the new
reliable two-stage approach.
"""

from concept_map_agent import ConceptMapAgent
from llm_clients import get_llm_client

def example_old_way():
    """Example of the old unreliable way (NOT RECOMMENDED)."""
    print("OLD WAY (Unreliable):")
    print("=" * 50)
    
    agent = ConceptMapAgent()
    llm_client = get_llm_client()
    
    # This often fails due to parsing issues
    try:
        result = agent.generate_concept_map("Climate Change", llm_client)
        if result.get("success"):
            print("✓ Success (rare with old approach)")
        else:
            print(f"✗ Failed: {result.get('error')}")
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
    
    print()

def example_new_way():
    """Example of the new reliable way (RECOMMENDED)."""
    print("NEW WAY (Reliable):")
    print("=" * 50)
    
    agent = ConceptMapAgent()
    llm_client = get_llm_client()
    
    # This is much more reliable
    try:
        result = agent.generate_simplified_two_stage("Climate Change", llm_client)
        if result.get("success"):
            print("✓ Success!")
            print(f"  Topic: {result.get('topic')}")
            print(f"  Concepts: {len(result.get('concepts', []))}")
            print(f"  Relationships: {len(result.get('relationships', []))}")
            
            # Show some sample concepts
            concepts = result.get('concepts', [])
            if concepts:
                print("\n  Sample concepts:")
                for i, concept in enumerate(concepts[:3], 1):
                    print(f"    {i}. {concept}")
                if len(concepts) > 3:
                    print(f"    ... and {len(concepts) - 3} more")
            
            # Show some sample relationships
            relationships = result.get('relationships', [])
            if relationships:
                print("\n  Sample relationships:")
                for i, rel in enumerate(relationships[:3], 1):
                    print(f"    {i}. {rel.get('from')} --[{rel.get('label')}]--> {rel.get('to')}")
                if len(relationships) > 3:
                    print(f"    ... and {len(relationships) - 3} more")
            
        else:
            print(f"✗ Failed: {result.get('error')}")
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
    
    print()

def example_with_different_topics():
    """Example with different topics to show versatility."""
    print("EXAMPLES WITH DIFFERENT TOPICS:")
    print("=" * 50)
    
    topics = [
        "Machine Learning",
        "Renewable Energy",
        "Digital Marketing"
    ]
    
    agent = ConceptMapAgent()
    llm_client = get_llm_client()
    
    for topic in topics:
        print(f"\nGenerating concept map for: {topic}")
        try:
            result = agent.generate_simplified_two_stage(topic, llm_client)
            if result.get("success"):
                print(f"  ✓ Success: {len(result.get('concepts', []))} concepts, {len(result.get('relationships', []))} relationships")
            else:
                print(f"  ✗ Failed: {result.get('error')}")
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
    
    print()

def example_network_first():
    """Example of using the network-first approach (Option 3)."""
    print("NETWORK-FIRST APPROACH (Option 3):")
    print("=" * 50)
    print("This approach focuses on comprehensive concepts and rich relationships.")
    
    agent = ConceptMapAgent()
    llm_client = get_llm_client()
    
    try:
        # Generate concept map using the network-first approach
        result = agent.generate_network_first("Artificial Intelligence", llm_client)
        
        if result and "topic" in result:
            print("✓ Success!")
            print(f"  Topic: {result.get('topic', 'N/A')}")
            print(f"  Concepts: {len(result.get('concepts', []))}")
            print(f"  Relationships: {len(result.get('relationships', []))}")
            
            # Show some sample relationships
            if result.get('relationships'):
                print("\n  Sample relationships:")
                for i, rel in enumerate(result['relationships'][:3], 1):
                    print(f"    {i}. {rel.get('from')} --[{rel.get('label')}]--> {rel.get('to')}")
                if len(result['relationships']) > 3:
                    print(f"    ... and {len(result['relationships']) - 3} more")
        else:
            print("✗ Failed: Could not generate network-first concept map")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
    
    print()

def example_configuration():
    """Show how to configure different approaches."""
    print("CONFIGURATION OPTIONS:")
    print("=" * 50)
    
    print("To use different approaches, edit concept_map_config.py:")
    print()
    
    approaches = {
        "simplified_two_stage": "RECOMMENDED - Simple, reliable, two LLM calls",
        "hierarchical_three_stage": "Structured, three LLM calls, good for complex topics",
        "network_first": "IMPLEMENTED - Focus on connections, two LLM calls",
        "template_based": "Consistent structure, two LLM calls",
        "unified": "NOT RECOMMENDED - Original unreliable approach"
    }
    
    for approach, description in approaches.items():
        if approach == "simplified_two_stage":
            marker = "⭐"
        elif approach == "network_first":
            marker = "✅"
        else:
            marker = "  "
        print(f"{marker} {approach}: {description}")
    
    print()
    print("Example configuration:")
    print("CONCEPT_MAP_APPROACH = 'simplified_two_stage'  # RECOMMENDED")
    print("CONCEPT_MAP_LANGUAGE = 'en'  # or 'zh'")

def main():
    """Run all examples."""
    print("CONCEPT MAP GENERATION EXAMPLES")
    print("=" * 60)
    print("This shows the difference between old and new approaches")
    print()
    
    # Show old vs new
    example_old_way()
    example_new_way()
    
    # Show the network-first approach (Option 3)
    example_network_first()
    
    # Show with different topics
    example_with_different_topics()
    
    # Show configuration options
    example_configuration()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    print("Both new approaches are much more reliable than the old unified approach:")
    print("1. Simplified Two-Stage: Most reliable, good for production")
    print("2. Network-First: Good for relationship-focused topics")
    print("3. Both avoid the parsing issues of the old approach")
    print()
    print("To get started:")
    print("1. Edit concept_map_config.py: CONCEPT_MAP_APPROACH = 'simplified_two_stage' or 'network_first'")
    print("2. Use: agent.generate_simplified_two_stage(topic, llm_client) or agent.generate_network_first(topic, llm_client)")
    print("3. Test with: python test_simplified_concept_maps.py")

if __name__ == "__main__":
    main()
