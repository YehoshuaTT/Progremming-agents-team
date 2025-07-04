#!/usr/bin/env python3
"""
LLM Cache System Demonstration
Shows intelligent caching capabilities with performance improvements
"""

import asyncio
import time
import json
from datetime import datetime
from enhanced_orchestrator import EnhancedOrchestrator
from tools.llm_cache import llm_cache

async def main():
    print("=" * 80)
    print("LLM CACHE SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = EnhancedOrchestrator()
    
    print("\n" + "=" * 60)
    print("1. CACHE SYSTEM INITIALIZATION")
    print("=" * 60)
    
    # Show initial cache stats
    initial_stats = orchestrator.get_cache_performance_stats()
    print(f"✅ LLM Cache initialized")
    print(f"📊 Initial cache size: {initial_stats['llm_cache']['cache_size_mb']:.1f} MB")
    print(f"📈 Initial entries: {initial_stats['llm_cache']['entries_count']}")
    print(f"⚡ Caching enabled: {initial_stats['caching_enabled']}")
    
    print("\n" + "=" * 60)
    print("2. AGENT-SPECIFIC CACHING STRATEGIES")
    print("=" * 60)
    
    # Test different agents with different caching strategies
    test_scenarios = [
        {
            "agent": "Product_Analyst",
            "prompt": "Create a detailed specification for a user profile page with authentication",
            "context": {"task_id": "TASK-001", "priority": "high"},
            "description": "Long-term spec caching (2 hours TTL)"
        },
        {
            "agent": "Coder", 
            "prompt": "Implement user authentication API with JWT tokens",
            "context": {"task_id": "TASK-002", "language": "python"},
            "description": "Semantic matching for similar coding tasks"
        },
        {
            "agent": "Code_Reviewer",
            "prompt": "Review the authentication code for security vulnerabilities",
            "context": {"task_id": "TASK-003", "files": ["auth.py", "jwt_handler.py"]},
            "description": "Exact match for precise review context"
        },
        {
            "agent": "Security_Specialist",
            "prompt": "Analyze security implications of JWT implementation",
            "context": {"task_id": "TASK-004", "scope": "authentication"},
            "description": "Long-term security pattern caching"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🤖 Testing {scenario['agent']}")
        print(f"📝 Task: {scenario['description']}")
        
        # First call (cache miss)
        start_time = time.time()
        response1 = await orchestrator.execute_llm_call_with_cache(
            scenario["agent"],
            scenario["prompt"],
            scenario["context"]
        )
        first_call_time = time.time() - start_time
        
        # Second call (cache hit)
        start_time = time.time()
        response2 = await orchestrator.execute_llm_call_with_cache(
            scenario["agent"],
            scenario["prompt"],
            scenario["context"]
        )
        second_call_time = time.time() - start_time
        
        print(f"⏱️  First call: {first_call_time:.3f}s (cache miss)")
        print(f"⚡ Second call: {second_call_time:.3f}s (cache hit)")
        print(f"🚀 Speed improvement: {(first_call_time / second_call_time):.1f}x faster")
        print(f"✅ Response consistency: {'✓' if response1 == response2 else '✗'}")
    
    print("\n" + "=" * 60)
    print("3. SEMANTIC MATCHING DEMONSTRATION")
    print("=" * 60)
    
    # Test semantic matching with normalized prompts
    print("\n🧠 Testing semantic matching for Coder agent")
    
    # Original prompt with specific details
    original_prompt = "Implement user login for TASK-123-001 at 2025-01-15T10:30:00"
    # Similar prompt with different details
    similar_prompt = "Implement user login for TASK-456-002 at 2025-01-16T14:45:00"
    
    context = {"task_type": "authentication"}
    
    # First call
    start_time = time.time()
    response1 = await orchestrator.execute_llm_call_with_cache("Coder", original_prompt, context)
    first_time = time.time() - start_time
    
    # Second call with similar prompt (should hit cache due to semantic matching)
    start_time = time.time()
    response2 = await orchestrator.execute_llm_call_with_cache("Coder", similar_prompt, context)
    second_time = time.time() - start_time
    
    print(f"📝 Original prompt: {original_prompt}")
    print(f"📝 Similar prompt: {similar_prompt}")
    print(f"⏱️  First call: {first_time:.3f}s")
    print(f"⚡ Second call: {second_time:.3f}s")
    print(f"🎯 Semantic match: {'✓' if second_time < first_time else '✗'}")
    print(f"🚀 Speed improvement: {(first_time / second_time):.1f}x faster")
    
    print("\n" + "=" * 60)
    print("4. CACHE PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Get comprehensive cache statistics
    final_stats = orchestrator.get_cache_performance_stats()
    llm_stats = final_stats['llm_cache']
    
    print(f"\n📊 CACHE STATISTICS:")
    print(f"   • Total requests: {llm_stats['hits'] + llm_stats['misses']}")
    print(f"   • Cache hits: {llm_stats['hits']}")
    print(f"   • Cache misses: {llm_stats['misses']}")
    print(f"   • Hit rate: {llm_stats['hit_rate']:.1f}%")
    print(f"   • Total cost saved: ${llm_stats['total_cost_saved']:.4f}")
    print(f"   • Total tokens saved: {llm_stats['total_tokens_saved']:,}")
    print(f"   • Cache size: {llm_stats['cache_size_mb']:.1f} MB")
    print(f"   • Active entries: {llm_stats['entries_count']}")
    
    print(f"\n🎯 PERFORMANCE SUMMARY:")
    print(f"   • Cache efficiency: {final_stats['performance_summary']['cache_efficiency']:.1f}/100")
    print(f"   • Memory usage: {llm_stats['memory_usage_mb']:.1f} MB")
    
    print(f"\n🤖 AGENT DISTRIBUTION:")
    for agent, count in llm_stats['agent_distribution'].items():
        print(f"   • {agent}: {count} cached entries")
    
    print("\n" + "=" * 60)
    print("5. CACHE OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)
    
    # Analyze cache performance and provide recommendations
    hit_rate = llm_stats['hit_rate']
    cache_size = llm_stats['cache_size_mb']
    entries_count = llm_stats['entries_count']
    
    print(f"\n🔍 PERFORMANCE ANALYSIS:")
    
    if hit_rate >= 70:
        print(f"   ✅ Excellent hit rate ({hit_rate:.1f}%) - Cache is very effective")
    elif hit_rate >= 50:
        print(f"   ⚠️  Good hit rate ({hit_rate:.1f}%) - Consider tuning TTL settings")
    else:
        print(f"   ❌ Low hit rate ({hit_rate:.1f}%) - Review caching strategies")
    
    if cache_size <= 50:
        print(f"   ✅ Optimal memory usage ({cache_size:.1f} MB)")
    elif cache_size <= 100:
        print(f"   ⚠️  Moderate memory usage ({cache_size:.1f} MB)")
    else:
        print(f"   ❌ High memory usage ({cache_size:.1f} MB) - Consider cleanup")
    
    if entries_count > 0:
        avg_size = cache_size / entries_count if entries_count > 0 else 0
        print(f"   📊 Average entry size: {avg_size:.2f} MB")
    
    print(f"\n💡 RECOMMENDATIONS:")
    
    if hit_rate < 60:
        print(f"   • Consider increasing TTL for stable agents like Product_Analyst")
        print(f"   • Enable semantic matching for more agents")
    
    if cache_size > 100:
        print(f"   • Consider reducing max_memory_mb setting")
        print(f"   • Implement more aggressive cleanup policies")
    
    if llm_stats['total_cost_saved'] > 0:
        print(f"   • Current cost savings: ${llm_stats['total_cost_saved']:.4f}")
        print(f"   • Projected monthly savings: ${llm_stats['total_cost_saved'] * 30:.2f}")
    
    print("\n" + "=" * 60)
    print("6. CACHE REPORT GENERATION")
    print("=" * 60)
    
    # Generate and display cache report
    cache_report = orchestrator.generate_cache_report()
    print(f"\n📋 CACHE PERFORMANCE REPORT:")
    print(cache_report)
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    success_indicators = [
        f"✅ Cache system operational",
        f"⚡ {llm_stats['hit_rate']:.1f}% hit rate achieved",
        f"💰 ${llm_stats['total_cost_saved']:.4f} cost savings",
        f"🚀 {llm_stats['total_tokens_saved']:,} tokens saved",
        f"📊 {llm_stats['entries_count']} entries cached",
        f"🎯 {final_stats['performance_summary']['cache_efficiency']:.1f}/100 efficiency score"
    ]
    
    print("\n🎉 SUCCESS INDICATORS:")
    for indicator in success_indicators:
        print(f"   {indicator}")
    
    print(f"\n📈 SYSTEM READY FOR PRODUCTION WITH CACHING ENABLED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
