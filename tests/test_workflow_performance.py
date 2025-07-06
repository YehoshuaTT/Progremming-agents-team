#!/usr/bin/env python3
"""
Performance Benchmark Tests for Agent Workflow System
Measures efficiency, token usage, and routing performance
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
import statistics

from agent_driven_workflow import AgentDrivenWorkflow
from smart_workflow_router import SmartWorkflowRouter, ContextAnalysis
from unittest.mock import Mock, patch

@dataclass
class BenchmarkResult:
    """Benchmark result data structure"""
    test_name: str
    execution_time: float
    memory_usage: float
    token_count: int
    agent_count: int
    iterations: int
    efficiency_score: float
    success: bool
    error_message: str = None

class WorkflowBenchmark:
    """Benchmark suite for workflow performance"""
    
    def __init__(self):
        self.workflow = AgentDrivenWorkflow()
        self.smart_router = SmartWorkflowRouter()
        self.results: List[BenchmarkResult] = []
    
    async def benchmark_simple_workflow(self) -> BenchmarkResult:
        """Benchmark simple workflow execution"""
        test_name = "Simple Workflow (Calculator)"
        start_time = time.time()
        
        try:
            with patch.object(self.workflow.orchestrator, 'execute_task_with_recovery') as mock_execute:
                mock_execute.return_value = {
                    "status": "success",
                    "result": "Calculator implemented successfully",
                    "artifacts": ["calculator.py", "test_calculator.py"],
                    "next_agent": "COMPLETE"
                }
                
                result = await self.workflow.run_agent_driven_workflow(
                    "Create a simple calculator application"
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                return BenchmarkResult(
                    test_name=test_name,
                    execution_time=execution_time,
                    memory_usage=0.0,  # Would need memory profiling
                    token_count=result.get("total_tokens", 0),
                    agent_count=len(result.get("agent_decisions", [])),
                    iterations=result.get("total_iterations", 0),
                    efficiency_score=self._calculate_efficiency_score(result),
                    success=result.get("status") == "completed"
                )
        except Exception as e:
            return BenchmarkResult(
                test_name=test_name,
                execution_time=time.time() - start_time,
                memory_usage=0.0,
                token_count=0,
                agent_count=0,
                iterations=0,
                efficiency_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def benchmark_complex_workflow(self) -> BenchmarkResult:
        """Benchmark complex workflow execution"""
        test_name = "Complex Workflow (E-commerce Platform)"
        start_time = time.time()
        
        try:
            with patch.object(self.workflow.orchestrator, 'execute_task_with_recovery') as mock_execute:
                # Simulate multiple agent executions
                mock_responses = [
                    {
                        "status": "success",
                        "result": "Requirements analyzed",
                        "artifacts": ["requirements.md"],
                        "next_agent": "Architect"
                    },
                    {
                        "status": "success",
                        "result": "Architecture designed",
                        "artifacts": ["architecture.md"],
                        "next_agent": "Security_Analyst"
                    },
                    {
                        "status": "success",
                        "result": "Security plan created",
                        "artifacts": ["security_plan.md"],
                        "next_agent": "Developer"
                    },
                    {
                        "status": "success",
                        "result": "Backend implemented",
                        "artifacts": ["backend.py"],
                        "next_agent": "UI_Designer"
                    },
                    {
                        "status": "success",
                        "result": "UI designed",
                        "artifacts": ["ui_design.html"],
                        "next_agent": "Tester"
                    },
                    {
                        "status": "success",
                        "result": "Tests implemented",
                        "artifacts": ["test_suite.py"],
                        "next_agent": "QA_Guardian"
                    },
                    {
                        "status": "success",
                        "result": "Quality assured",
                        "artifacts": ["qa_report.md"],
                        "next_agent": "COMPLETE"
                    }
                ]
                
                mock_execute.side_effect = mock_responses
                
                result = await self.workflow.run_agent_driven_workflow(
                    "Build a secure e-commerce platform with user authentication, payment processing, and admin dashboard"
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                return BenchmarkResult(
                    test_name=test_name,
                    execution_time=execution_time,
                    memory_usage=0.0,
                    token_count=result.get("total_tokens", 0),
                    agent_count=len(result.get("agent_decisions", [])),
                    iterations=result.get("total_iterations", 0),
                    efficiency_score=self._calculate_efficiency_score(result),
                    success=result.get("status") == "completed"
                )
        except Exception as e:
            return BenchmarkResult(
                test_name=test_name,
                execution_time=time.time() - start_time,
                memory_usage=0.0,
                token_count=0,
                agent_count=0,
                iterations=0,
                efficiency_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def benchmark_smart_router_performance(self) -> BenchmarkResult:
        """Benchmark smart router performance"""
        test_name = "Smart Router Performance"
        start_time = time.time()
        
        try:
            test_cases = [
                ("Create a simple calculator", {"current_artifacts": [], "execution_history": []}),
                ("Build a web application", {"current_artifacts": ["requirements.md"], "execution_history": ["Product_Analyst"]}),
                ("Implement security features", {"current_artifacts": ["app.py"], "execution_history": ["Developer"]}),
                ("Create documentation", {"current_artifacts": ["code.py", "tests.py"], "execution_history": ["Developer", "Tester"]})
            ]
            
            recommendations = []
            for user_request, context in test_cases:
                # Use the correct method signature
                analysis = self.smart_router.analyze_context(user_request, context)
                recs = self.smart_router.get_agent_recommendations(analysis, context)
                if recs:
                    recommendations.extend(recs)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Calculate efficiency based on recommendation quality
            efficiency_score = 0.0
            if recommendations:
                efficiency_score = sum(rec.confidence for rec in recommendations) / len(recommendations)
            
            return BenchmarkResult(
                test_name=test_name,
                execution_time=execution_time,
                memory_usage=0.0,
                token_count=0,  # Router doesn't use tokens directly
                agent_count=len(recommendations),
                iterations=len(test_cases),
                efficiency_score=efficiency_score,
                success=all(rec.confidence > 0.3 for rec in recommendations) if recommendations else False
            )
        except Exception as e:
            return BenchmarkResult(
                test_name=test_name,
                execution_time=time.time() - start_time,
                memory_usage=0.0,
                token_count=0,
                agent_count=0,
                iterations=0,
                efficiency_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def benchmark_loop_detection(self) -> BenchmarkResult:
        """Benchmark loop detection performance"""
        test_name = "Loop Detection Performance"
        start_time = time.time()
        
        try:
            # Create a context that would normally cause loops
            user_request = "Fix code issues"
            context = {
                "current_artifacts": ["code.py"],
                "execution_history": ["Coder", "Code_Reviewer"] * 5  # Potential loop
            }
            
            # Use the correct method signature
            analysis = self.smart_router.analyze_context(user_request, context)
            
            # Check if Coder should be skipped due to loop
            should_skip, reason = self.smart_router.should_skip_agent("Coder", analysis, context)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Loop detection is successful if it prevents the loop
            loop_detected = should_skip
            
            return BenchmarkResult(
                test_name=test_name,
                execution_time=execution_time,
                memory_usage=0.0,
                token_count=0,
                agent_count=1,
                iterations=1,
                efficiency_score=1.0 if loop_detected else 0.0,
                success=loop_detected
            )
        except Exception as e:
            return BenchmarkResult(
                test_name=test_name,
                execution_time=time.time() - start_time,
                memory_usage=0.0,
                token_count=0,
                agent_count=0,
                iterations=0,
                efficiency_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def benchmark_context_optimization(self) -> BenchmarkResult:
        """Benchmark context optimization performance"""
        test_name = "Context Optimization Performance"
        start_time = time.time()
        
        try:
            # Create a large context
            large_context = {
                "user_request": "Build a complex system",
                "project_type": "enterprise_application",
                "current_artifacts": [f"file_{i}.py" for i in range(100)],
                "execution_history": ["Agent1", "Agent2"] * 50,
                "detailed_logs": [f"Log entry {i}" for i in range(1000)]
            }
            
            # Measure optimization using the correct method
            original_size = len(str(large_context))
            optimized_context = self.smart_router.optimize_workflow_context(large_context)
            optimized_size = len(str(optimized_context))
            
            compression_ratio = (original_size - optimized_size) / original_size if original_size > 0 else 0
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            return BenchmarkResult(
                test_name=test_name,
                execution_time=execution_time,
                memory_usage=0.0,
                token_count=original_size,  # Using original size as proxy for tokens
                agent_count=1,
                iterations=1,
                efficiency_score=max(0.0, compression_ratio),
                success=compression_ratio > 0.0  # Any compression is success
            )
        except Exception as e:
            return BenchmarkResult(
                test_name=test_name,
                execution_time=time.time() - start_time,
                memory_usage=0.0,
                token_count=0,
                agent_count=0,
                iterations=0,
                efficiency_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _calculate_efficiency_score(self, workflow_result: Dict[str, Any]) -> float:
        """Calculate efficiency score based on workflow result"""
        try:
            # Factors that contribute to efficiency
            factors = []
            
            # Agent efficiency (fewer agents for simple tasks is better)
            agent_count = len(workflow_result.get("agent_decisions", []))
            if agent_count > 0:
                factors.append(min(1.0, 5.0 / agent_count))  # Optimal is 5 or fewer agents
            
            # Iteration efficiency
            iterations = workflow_result.get("total_iterations", 0)
            if iterations > 0:
                factors.append(min(1.0, 10.0 / iterations))  # Optimal is 10 or fewer iterations
            
            # Success rate
            if workflow_result.get("status") == "completed":
                factors.append(1.0)
            else:
                factors.append(0.0)
            
            # Context optimization
            if "context_optimization" in workflow_result:
                compression_ratio = workflow_result["context_optimization"].get("compression_ratio", 0)
                factors.append(min(1.0, compression_ratio))
            
            return statistics.mean(factors) if factors else 0.0
        except Exception:
            return 0.0
    
    async def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmark tests"""
        print("🔄 Starting Performance Benchmarks...")
        print("=" * 50)
        
        benchmarks = [
            self.benchmark_simple_workflow,
            self.benchmark_complex_workflow,
            self.benchmark_smart_router_performance,
            self.benchmark_loop_detection,
            self.benchmark_context_optimization
        ]
        
        results = []
        for benchmark in benchmarks:
            print(f"Running {benchmark.__name__}...")
            result = await benchmark()
            results.append(result)
            
            status = "✅ PASSED" if result.success else "❌ FAILED"
            print(f"{status} - {result.test_name}")
            print(f"  Execution Time: {result.execution_time:.3f}s")
            print(f"  Efficiency Score: {result.efficiency_score:.2f}")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            print()
        
        self.results = results
        return results
    
    def generate_benchmark_report(self) -> str:
        """Generate comprehensive benchmark report"""
        if not self.results:
            return "No benchmark results available"
        
        report = []
        report.append("# Performance Benchmark Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        report.append("## Summary")
        report.append(f"- Total Tests: {len(self.results)}")
        report.append(f"- Successful: {len(successful_tests)}")
        report.append(f"- Failed: {len(failed_tests)}")
        report.append(f"- Success Rate: {len(successful_tests)/len(self.results)*100:.1f}%")
        report.append("")
        
        if successful_tests:
            avg_execution_time = statistics.mean([r.execution_time for r in successful_tests])
            avg_efficiency = statistics.mean([r.efficiency_score for r in successful_tests])
            
            report.append("## Performance Metrics")
            report.append(f"- Average Execution Time: {avg_execution_time:.3f}s")
            report.append(f"- Average Efficiency Score: {avg_efficiency:.2f}")
            report.append("")
        
        # Detailed results
        report.append("## Detailed Results")
        for result in self.results:
            report.append(f"### {result.test_name}")
            report.append(f"- Status: {'✅ PASSED' if result.success else '❌ FAILED'}")
            report.append(f"- Execution Time: {result.execution_time:.3f}s")
            report.append(f"- Efficiency Score: {result.efficiency_score:.2f}")
            report.append(f"- Agent Count: {result.agent_count}")
            report.append(f"- Iterations: {result.iterations}")
            if result.error_message:
                report.append(f"- Error: {result.error_message}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        if failed_tests:
            report.append("- Address failing tests:")
            for test in failed_tests:
                report.append(f"  - {test.test_name}: {test.error_message}")
        
        if successful_tests:
            slow_tests = [r for r in successful_tests if r.execution_time > 1.0]
            if slow_tests:
                report.append("- Optimize slow tests:")
                for test in slow_tests:
                    report.append(f"  - {test.test_name}: {test.execution_time:.3f}s")
        
        return "\n".join(report)
    
    def save_benchmark_report(self, filename: str = None) -> str:
        """Save benchmark report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_report_{timestamp}.md"
        
        report = self.generate_benchmark_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename


async def main():
    """Run benchmark suite"""
    benchmark = WorkflowBenchmark()
    
    # Run all benchmarks
    results = await benchmark.run_all_benchmarks()
    
    # Generate and save report
    report_file = benchmark.save_benchmark_report()
    
    print("🎉 Benchmark Suite Completed!")
    print(f"📊 Report saved to: {report_file}")
    print("=" * 50)
    
    # Print summary
    successful = sum(1 for r in results if r.success)
    total = len(results)
    
    print(f"Results: {successful}/{total} tests passed")
    
    if successful == total:
        print("✅ All benchmarks passed!")
        return True
    else:
        print("❌ Some benchmarks failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
