#!/usr/bin/env python3
"""
Performance & Load Test Suite
בדיקת ביצועים ועומס של המערכת
"""

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from enhanced_orchestrator import EnhancedOrchestrator

async def measure_initialization_time():
    """מדידת זמן אתחול המערכת"""
    print("🔄 Measuring system initialization time...")
    
    start_time = time.time()
    orchestrator = EnhancedOrchestrator()
    init_time = time.time() - start_time
    
    start_knowledge = time.time()
    await orchestrator.initialize_knowledge_systems()
    knowledge_time = time.time() - start_knowledge
    
    print(f"✅ Orchestrator initialization: {init_time:.3f}s")
    print(f"✅ Knowledge systems initialization: {knowledge_time:.3f}s")
    print(f"📊 Total initialization time: {init_time + knowledge_time:.3f}s")
    
    return orchestrator, init_time + knowledge_time

async def measure_workflow_creation_time(orchestrator):
    """מדידת זמן יצירת workflows"""
    print("\n🔄 Measuring workflow creation time...")
    
    times = []
    for i in range(5):
        start_time = time.time()
        workflow_id = await orchestrator.start_workflow(
            f"Create feature {i+1}: User management system",
            "complex_ui_feature"
        )
        end_time = time.time()
        times.append(end_time - start_time)
        print(f"   Workflow {i+1}: {times[-1]:.3f}s")
    
    avg_time = statistics.mean(times)
    print(f"✅ Average workflow creation time: {avg_time:.3f}s")
    return avg_time

async def measure_context_optimization_performance(orchestrator):
    """מדידת ביצועי אופטימיזציית קונטקסט"""
    print("\n🔄 Measuring context optimization performance...")
    
    # יצירת קונטקסט גדול לבדיקה
    large_context = {
        "user_request": "Complex system request",
        "previous_artifacts": [f"large_file_{i}.md" for i in range(100)],
        "artifact_content": "Very large content block " * 2000,
        "metadata": {
            "large_data": list(range(5000)),
            "complex_structure": {f"key_{i}": f"value_{i}" * 100 for i in range(50)}
        },
        "history": [f"Historical entry {i}" for i in range(1000)]
    }
    
    original_size = len(str(large_context))
    
    # בדיקת זמני אופטימיזציה
    times = []
    optimized_sizes = []
    
    for agent in ["Product_Analyst", "Coder", "Code_Reviewer", "Architect", "Tester"]:
        start_time = time.time()
        optimized = orchestrator._optimize_context_for_agent(large_context, agent)
        end_time = time.time()
        
        times.append(end_time - start_time)
        optimized_sizes.append(len(str(optimized)))
        
        reduction = ((original_size - optimized_sizes[-1]) / original_size) * 100
        print(f"   {agent}: {times[-1]:.3f}s, {reduction:.1f}% reduction")
    
    avg_time = statistics.mean(times)
    avg_reduction = statistics.mean([((original_size - size) / original_size) * 100 for size in optimized_sizes])
    
    print(f"✅ Average optimization time: {avg_time:.3f}s")
    print(f"✅ Average size reduction: {avg_reduction:.1f}%")
    
    return avg_time, avg_reduction

async def measure_concurrent_workflows(orchestrator, num_workflows=10):
    """מדידת ביצועים עם workflows מקבילים"""
    print(f"\n🔄 Measuring performance with {num_workflows} concurrent workflows...")
    
    start_time = time.time()
    
    # יצירת workflows מקבילים
    tasks = []
    for i in range(num_workflows):
        task = orchestrator.start_workflow(
            f"Concurrent feature {i+1}: Authentication module",
            "simple_linear_feature"
        )
        tasks.append(task)
    
    workflow_ids = await asyncio.gather(*tasks)
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_per_workflow = total_time / num_workflows
    
    print(f"✅ {num_workflows} workflows created in {total_time:.3f}s")
    print(f"📊 Average time per workflow: {avg_per_workflow:.3f}s")
    print(f"📊 Workflows per second: {num_workflows / total_time:.2f}")
    
    return workflow_ids, total_time

async def measure_memory_usage():
    """מדידת שימוש בזיכרון"""
    print("\n🔄 Measuring memory usage...")
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # יצירת מספר orchestrators לבדיקת זיכרון
    orchestrators = []
    for i in range(5):
        orch = EnhancedOrchestrator()
        await orch.initialize_knowledge_systems()
        orchestrators.append(orch)
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_per_orchestrator = (memory_after - memory_before) / 5
    
    print(f"📊 Memory before: {memory_before:.1f} MB")
    print(f"📊 Memory after: {memory_after:.1f} MB")
    print(f"✅ Memory per orchestrator: {memory_per_orchestrator:.1f} MB")
    
    return memory_per_orchestrator

async def measure_cache_performance(orchestrator):
    """מדידת ביצועי cache"""
    print("\n🔄 Measuring cache performance...")
    
    # ביצוע מספר קריאות LLM זהות
    prompt = "Create a comprehensive test plan for authentication system"
    context = {"type": "testing", "complexity": "high"}
    
    # קריאה ראשונה (cache miss)
    start_time = time.time()
    response1 = await orchestrator.execute_llm_call_with_cache("Tester", prompt, context)
    first_call_time = time.time() - start_time
    
    # קריאות נוספות (cache hits)
    cache_times = []
    for i in range(5):
        start_time = time.time()
        response = await orchestrator.execute_llm_call_with_cache("Tester", prompt, context)
        cache_times.append(time.time() - start_time)
    
    avg_cache_time = statistics.mean(cache_times)
    speedup = first_call_time / avg_cache_time if avg_cache_time > 0 else 0
    
    print(f"📊 First call (miss): {first_call_time:.3f}s")
    print(f"📊 Cache hits average: {avg_cache_time:.3f}s")
    print(f"✅ Cache speedup: {speedup:.1f}x")
    
    # בדיקת סטטיסטיקות cache
    cache_stats = orchestrator.get_cache_performance_stats()
    print(f"📊 Cache hit rate: {cache_stats['performance_summary']['hit_rate']:.1f}%")
    print(f"📊 Cache efficiency: {cache_stats['performance_summary']['cache_efficiency']:.1f}%")
    
    return speedup, cache_stats

async def run_performance_tests():
    """ריצת כל בדיקות הביצועים"""
    print("🚀 Starting Performance & Load Tests...")
    print("=" * 60)
    
    results = {}
    
    # בדיקת זמן אתחול
    orchestrator, init_time = await measure_initialization_time()
    results['initialization_time'] = init_time
    
    # בדיקת יצירת workflows
    workflow_time = await measure_workflow_creation_time(orchestrator)
    results['workflow_creation_time'] = workflow_time
    
    # בדיקת אופטימיזציית קונטקסט
    opt_time, opt_reduction = await measure_context_optimization_performance(orchestrator)
    results['context_optimization_time'] = opt_time
    results['context_reduction_percent'] = opt_reduction
    
    # בדיקת workflows מקבילים
    workflow_ids, concurrent_time = await measure_concurrent_workflows(orchestrator, 10)
    results['concurrent_workflows_time'] = concurrent_time
    
    # בדיקת זיכרון
    memory_usage = await measure_memory_usage()
    results['memory_per_orchestrator_mb'] = memory_usage
    
    # בדיקת ביצועי cache
    cache_speedup, cache_stats = await measure_cache_performance(orchestrator)
    results['cache_speedup'] = cache_speedup
    results['cache_hit_rate'] = cache_stats['performance_summary']['hit_rate']
    
    # סיכום
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    print(f"⚡ System initialization: {results['initialization_time']:.3f}s")
    print(f"⚡ Workflow creation: {results['workflow_creation_time']:.3f}s")
    print(f"⚡ Context optimization: {results['context_optimization_time']:.3f}s")
    print(f"⚡ 10 concurrent workflows: {results['concurrent_workflows_time']:.3f}s")
    print(f"💾 Memory per instance: {results['memory_per_orchestrator_mb']:.1f} MB")
    print(f"🚀 Cache speedup: {results['cache_speedup']:.1f}x")
    print(f"📈 Context size reduction: {results['context_reduction_percent']:.1f}%")
    print(f"🎯 Cache hit rate: {results['cache_hit_rate']:.1f}%")
    
    # הערכת ביצועים
    print("\n📋 PERFORMANCE EVALUATION:")
    if results['initialization_time'] < 2.0:
        print("✅ Initialization time: EXCELLENT")
    elif results['initialization_time'] < 5.0:
        print("🟡 Initialization time: GOOD")
    else:
        print("🔴 Initialization time: NEEDS IMPROVEMENT")
    
    if results['workflow_creation_time'] < 1.0:
        print("✅ Workflow creation: EXCELLENT")
    elif results['workflow_creation_time'] < 3.0:
        print("🟡 Workflow creation: GOOD")
    else:
        print("🔴 Workflow creation: NEEDS IMPROVEMENT")
    
    if results['context_reduction_percent'] > 70:
        print("✅ Context optimization: EXCELLENT")
    elif results['context_reduction_percent'] > 50:
        print("🟡 Context optimization: GOOD")
    else:
        print("🔴 Context optimization: NEEDS IMPROVEMENT")
    
    if results['memory_per_orchestrator_mb'] < 50:
        print("✅ Memory usage: EXCELLENT")
    elif results['memory_per_orchestrator_mb'] < 100:
        print("🟡 Memory usage: GOOD")
    else:
        print("🔴 Memory usage: NEEDS IMPROVEMENT")
    
    print("\n🎉 Performance tests completed successfully!")
    return results

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
