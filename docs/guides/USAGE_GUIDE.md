# Usage Guide: Autonomous Multi-Agent Software Development System

## 🚀 Getting Started

### Prerequisites
Before using the system, ensure you have:
- Python 3.8+ installed
- All required dependencies (see [Installation Guide](#installation))
- API credentials for LLM services
- Git repository access (if using version control features)

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd Agents
   ```

2. **Install dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Set up API keys
   export OPENAI_API_KEY="your-api-key-here"
   export ANTHROPIC_API_KEY="your-api-key-here"
   
   # Optional: Configure system settings
   export ORCHESTRATOR_MAX_WORKFLOWS=5
   export ORCHESTRATOR_CACHE_ENABLED=true
   ```

## 🎯 Basic Usage

### Starting the System

```python
from core.enhanced_orchestrator import EnhancedOrchestrator
import asyncio

async def main():
    # Initialize the orchestrator
    orchestrator = EnhancedOrchestrator()
    
    # Start a new workflow
    workflow_id = await orchestrator.start_workflow(
        request="Create a user authentication API with JWT tokens",
        workflow_type="complex_ui_feature"
    )
    
    print(f"Workflow started with ID: {workflow_id}")

# Run the system
asyncio.run(main())
```

### Running a Simple Task

```python
async def run_simple_task():
    orchestrator = EnhancedOrchestrator()
    
    # Create a task for the Product Analyst
    task_result = await orchestrator.process_agent_completion(
        task_id="TASK-001",
        agent_output="Analysis complete. Requirements documented in spec.md",
        session_id="session-123"
    )
    
    print("Task completed:", task_result)

asyncio.run(run_simple_task())
```

## 🔄 Workflow Management

### Available Workflow Types

#### 1. **Complex UI Feature** (`complex_ui_feature`)
**Best for**: Full-stack feature development

```python
workflow_id = await orchestrator.start_workflow(
    request="Build a real-time chat system with WebSocket support",
    workflow_type="complex_ui_feature"
)
```

**Typical Flow**:
1. Product Analyst → Requirements & specifications
2. Architect → System design & architecture
3. Coder → Implementation
4. Code Reviewer → Code quality review
5. QA Guardian → Testing
6. DevOps Specialist → Deployment

#### 2. **Bug Fix** (`bug_fix`)
**Best for**: Issue resolution and debugging

```python
workflow_id = await orchestrator.start_workflow(
    request="Fix authentication timeout issue in user login",
    workflow_type="bug_fix"
)
```

#### 3. **Security Update** (`security_update`)
**Best for**: Security patches and hardening

```python
workflow_id = await orchestrator.start_workflow(
    request="Implement rate limiting to prevent API abuse",
    workflow_type="security_update"
)
```

#### 4. **Performance Optimization** (`performance_optimization`)
**Best for**: System performance improvements

```python
workflow_id = await orchestrator.start_workflow(
    request="Optimize database queries for user dashboard",
    workflow_type="performance_optimization"
)
```

### Monitoring Workflow Progress

```python
# Check active workflows
active_workflows = orchestrator.active_workflows
for workflow_id, status in active_workflows.items():
    print(f"Workflow {workflow_id}: {status['status']}")

# Get detailed workflow information
workflow_info = orchestrator.get_workflow_status(workflow_id)
print(f"Current agent: {workflow_info['current_agent']}")
print(f"Phase: {workflow_info['current_phase']}")
```

## 🤖 Agent Interaction

### Available Agents

| Agent | Primary Function | When to Use |
|-------|------------------|-------------|
| **Product_Analyst** | Requirements analysis | Starting new features |
| **Architect** | System design | Architecture decisions |
| **Coder** | Implementation | Writing code |
| **Code_Reviewer** | Code quality review | Before merging code |
| **QA_Guardian** | Testing | Quality assurance |
| **DevOps_Specialist** | Deployment | CI/CD and infrastructure |
| **Technical_Writer** | Documentation | Creating docs |
| **Security_Specialist** | Security analysis | Security reviews |
| **Debugger** | Issue diagnosis | Problem solving |
| **Ask_Agent** | Information provider | Questions and guidance |

### Direct Agent Communication

```python
# Get available agents
agents = orchestrator.agent_factory.list_available_agents()
print("Available agents:", agents)

# Create a specific agent task
task_config = {
    "agent": "Coder",
    "task": "Implement user authentication middleware",
    "context": {
        "specification": "auth_spec.md",
        "existing_code": "src/middleware/"
    }
}

result = await orchestrator._create_next_task(handoff_packet, task_config)
```

## 📝 Working with Handoff Packets

### Understanding Handoff Packets

Handoff packets are structured communications between agents:

```json
{
  "completed_task_id": "TASK-123",
  "agent_name": "Product_Analyst",
  "status": "SUCCESS",
  "artifacts_produced": ["requirements.md", "user_stories.md"],
  "next_step_suggestion": "IMPLEMENTATION_NEEDED",
  "notes": "Requirements analysis complete. Ready for architecture design.",
  "timestamp": "2025-01-25T10:30:00Z",
  "dependencies_satisfied": ["SPEC-001"],
  "blocking_issues": []
}
```

### Processing Agent Completion

```python
async def handle_agent_completion(task_id, agent_output):
    result = await orchestrator.process_agent_completion(
        task_id=task_id,
        agent_output=agent_output,
        session_id="workflow-session-123"
    )
    
    if result["status"] == "human_approval_required":
        print("Human approval needed for:", result["approval_id"])
        # Handle human approval workflow
    elif result["status"] == "next_tasks_created":
        print("Next tasks created:", result["next_tasks"])
    
    return result
```

## 👥 Human Approval System

### When Human Approval is Required

The system automatically requests human approval for:
- **High-risk changes** (production deployments)
- **Security modifications** (authentication, permissions)
- **Breaking changes** (API modifications)
- **Critical bug fixes** (system-wide impacts)

### Handling Approval Requests

```python
async def handle_approval_request(approval_id, decision):
    # Decision options:
    # - "APPROVE" - Approve the change
    # - "CHANGES: [feedback]" - Request changes
    # - "REJECT: [reason]" - Reject the change
    
    result = await orchestrator.process_human_approval(
        approval_id=approval_id,
        decision=decision
    )
    
    return result

# Example usage
await handle_approval_request("APPROVAL-001", "APPROVE")
await handle_approval_request("APPROVAL-002", "CHANGES: Please add error handling")
await handle_approval_request("APPROVAL-003", "REJECT: Security concerns")
```

### Approval Workflow Example

```python
async def approval_workflow_example():
    # Start a workflow that requires approval
    workflow_id = await orchestrator.start_workflow(
        request="Deploy new payment processing system",
        workflow_type="complex_ui_feature"
    )
    
    # Monitor for approval requests
    while True:
        approval_queue = orchestrator.human_approval_queue
        
        for approval in approval_queue:
            if approval["status"] == "pending":
                print(f"Approval needed: {approval['description']}")
                print(f"Artifacts: {approval['artifacts']}")
                
                # Simulate human decision
                decision = input("Enter decision (APPROVE/CHANGES:/REJECT:): ")
                
                result = await orchestrator.process_human_approval(
                    approval_id=approval["id"],
                    decision=decision
                )
                
                print(f"Decision processed: {result}")
        
        await asyncio.sleep(5)  # Check every 5 seconds
```

## 🔧 Advanced Features

### Context Optimization

The system automatically optimizes context to reduce token usage:

```python
# Enable/disable context optimization
orchestrator.context_optimization_enabled = True

# Set maximum context tokens
orchestrator.max_context_tokens = 16000

# Get context optimization metrics
async def get_optimization_metrics():
    metrics = await orchestrator.get_context_optimization_metrics()
    print(f"Token reduction: {metrics['token_reduction_percentage']}%")
    print(f"Cache hit rate: {metrics['cache_hit_rate']}%")
```

### Caching System

```python
# Configure caching
orchestrator.caching_enabled = True

# Get cache statistics
cache_stats = orchestrator.llm_cache.get_cache_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']}")
print(f"Total cost saved: ${cache_stats['total_cost_saved']}")

# Clear cache if needed
orchestrator.llm_cache.clear_cache()
```

### Error Handling and Recovery

```python
# Configure error handling
orchestrator.config["max_retry_attempts"] = 3
orchestrator.config["auto_retry_enabled"] = True

# Check error history
error_history = orchestrator.error_history
for error in error_history:
    print(f"Error: {error['type']} - {error['message']}")
    print(f"Recovery: {error['recovery_action']}")
```

## 🔍 Monitoring and Debugging

### Logging System

```python
# Enable detailed logging
orchestrator.log_tools.set_log_level("DEBUG")

# Get recent logs
recent_logs = orchestrator.log_tools.get_recent_logs(limit=50)
for log in recent_logs:
    print(f"[{log['timestamp']}] {log['event']}: {log['data']}")

# Search logs
search_results = orchestrator.log_tools.search_logs(
    query="WORKFLOW_STARTED",
    time_range="last_hour"
)
```

### Performance Monitoring

```python
# Get system performance metrics
async def get_performance_metrics():
    metrics = await orchestrator.get_performance_metrics()
    
    print(f"Active workflows: {metrics['active_workflows']}")
    print(f"Average response time: {metrics['avg_response_time']}ms")
    print(f"Cache efficiency: {metrics['cache_efficiency']}%")
    print(f"Error rate: {metrics['error_rate']}%")
```

### Debugging Tools

```python
# Enable debug mode
orchestrator.debug_mode = True

# Get workflow state
workflow_state = orchestrator.get_workflow_state(workflow_id)
print(f"Current agent: {workflow_state['current_agent']}")
print(f"Task queue: {workflow_state['task_queue']}")
print(f"Blocking issues: {workflow_state['blocking_issues']}")

# Replay workflow from checkpoint
await orchestrator.replay_workflow_from_checkpoint(
    workflow_id=workflow_id,
    checkpoint_id="checkpoint-123"
)
```

## 📊 System Demonstrations

### Running the Demo Suite

```python
# Run the comprehensive system demonstration
from development.demos.final_demonstration import SystemDemonstration

async def run_system_demo():
    demo = SystemDemonstration()
    await demo.run_comprehensive_demonstration()

asyncio.run(run_system_demo())
```

### Available Demos

1. **Core Architecture Demo** (`development/demos/final_demonstration.py`)
2. **Context Optimization Demo** (`development/demos/context_optimization_demo.py`)
3. **LLM Cache Demo** (`development/demos/llm_cache_demo.py`)
4. **Caching System Demo** (`development/demos/caching_system_demo.py`)

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_orchestrator.py -v
pytest tests/test_agents.py -v
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=core --cov=tools --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component workflow testing
- **End-to-end Tests**: Complete workflow validation
- **Performance Tests**: System performance benchmarks

## 🚨 Troubleshooting

### Common Issues

#### 1. **Workflow Not Starting**
```python
# Check system status
if not orchestrator.is_system_healthy():
    print("System health check failed")
    health_report = orchestrator.get_health_report()
    print(health_report)
```

#### 2. **Agent Not Responding**
```python
# Check agent availability
available_agents = orchestrator.agent_factory.list_available_agents()
if "Coder" not in available_agents:
    print("Coder agent not available")
    
# Restart agent
orchestrator.agent_factory.restart_agent("Coder")
```

#### 3. **Context Optimization Issues**
```python
# Disable context optimization temporarily
orchestrator.context_optimization_enabled = False

# Check token usage
context_tokens = orchestrator._estimate_context_tokens(context)
if context_tokens > orchestrator.max_context_tokens:
    print(f"Context too large: {context_tokens} tokens")
```

### Debug Commands

```python
# Enable verbose logging
orchestrator.set_debug_mode(True)

# Get system state
system_state = orchestrator.get_system_state()
print(json.dumps(system_state, indent=2))

# Check resource usage
resource_usage = orchestrator.get_resource_usage()
print(f"Memory usage: {resource_usage['memory_mb']}MB")
print(f"CPU usage: {resource_usage['cpu_percent']}%")
```

## 📞 Support and Resources

### Documentation
- **System Overview**: `docs/SYSTEM_OVERVIEW.md`
- **Architecture Guide**: `docs/architecture/`
- **API Reference**: `docs/api/`
- **Agent Templates**: `docs/agent_templates.md`

### Community and Support
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Comprehensive guides and examples
- **Examples**: Working code samples in `development/demos/`

### Best Practices
- Always monitor active workflows
- Use human approval for critical changes
- Regularly check system health
- Keep context optimization enabled
- Monitor cache performance
- Review error logs regularly

---

*This guide provides comprehensive coverage of the Autonomous Multi-Agent Software Development System. For more detailed information, refer to the specific documentation files in the `docs/` directory.*
