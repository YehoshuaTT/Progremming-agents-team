# Quick Reference Guide
## Autonomous Multi-Agent Software Development System

### 🚀 Essential Commands

#### Start the System
```python
from core.enhanced_orchestrator import EnhancedOrchestrator
import asyncio

orchestrator = EnhancedOrchestrator()
```

#### Launch a Workflow
```python
# Complex feature development
workflow_id = await orchestrator.start_workflow(
    request="Create user authentication with JWT",
    workflow_type="complex_ui_feature"
)

# Bug fix workflow
workflow_id = await orchestrator.start_workflow(
    request="Fix login timeout issue",
    workflow_type="bug_fix"
)

# Security update
workflow_id = await orchestrator.start_workflow(
    request="Add rate limiting to API endpoints",
    workflow_type="security_update"
)
```

#### Monitor Progress
```python
# Check status
status = orchestrator.get_workflow_status(workflow_id)
print(f"Status: {status['status']}")
print(f"Current agent: {status['current_agent']}")

# Get performance metrics
metrics = await orchestrator.get_performance_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']}")
```

#### Handle Human Approval
```python
# Process approval
result = await orchestrator.process_human_approval(
    approval_id="APPROVAL-001",
    decision="APPROVE"  # or "CHANGES: feedback" or "REJECT: reason"
)
```

### 🤖 Agent Quick Reference

| Agent Name | Command | Best For |
|------------|---------|----------|
| **Product_Analyst** | `"Product_Analyst"` | Requirements, specs |
| **Architect** | `"Architect"` | System design |
| **Coder** | `"Coder"` | Implementation |
| **Code_Reviewer** | `"Code_Reviewer"` | Code quality |
| **QA_Guardian** | `"QA_Guardian"` | Testing |
| **DevOps_Specialist** | `"DevOps_Specialist"` | Deployment |
| **Security_Specialist** | `"Security_Specialist"` | Security |
| **Debugger** | `"Debugger"` | Issue resolution |

### 📊 Common Workflow Patterns

#### 1. **New Feature Development**
```python
# 1. Start workflow
workflow_id = await orchestrator.start_workflow(
    request="Build shopping cart functionality",
    workflow_type="complex_ui_feature"
)

# 2. Monitor and handle approvals
while True:
    status = orchestrator.get_workflow_status(workflow_id)
    if status['status'] == 'awaiting_approval':
        # Handle approval
        break
    elif status['status'] in ['completed', 'failed']:
        break
    await asyncio.sleep(5)
```

#### 2. **Quick Bug Fix**
```python
# Direct bug fix workflow
workflow_id = await orchestrator.start_workflow(
    request="Fix null pointer exception in user profile",
    workflow_type="bug_fix"
)
```

#### 3. **Security Enhancement**
```python
# Security-focused workflow
workflow_id = await orchestrator.start_workflow(
    request="Add input validation to prevent SQL injection",
    workflow_type="security_update"
)
```

### 🔧 Configuration Quick Setup

#### Environment Variables
```bash
# Required
export OPENAI_API_KEY="your-api-key"

# Optional
export ORCHESTRATOR_CACHE_ENABLED=true
export ORCHESTRATOR_MAX_WORKFLOWS=5
export ORCHESTRATOR_DEBUG_MODE=false
```

#### System Settings
```python
# Enable features
orchestrator.caching_enabled = True
orchestrator.context_optimization_enabled = True
orchestrator.debug_mode = False

# Configure limits
orchestrator.max_context_tokens = 16000
orchestrator.config["max_concurrent_workflows"] = 5
```

### 🧪 Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_orchestrator.py -v
pytest tests/test_integration.py -v

# Run demos
python development/demos/final_demonstration.py
python development/demos/context_optimization_demo.py
```

### 📝 Common Task Types

#### Request Formats
```python
# Feature requests
"Create a REST API for [functionality]"
"Build a [component] with [requirements]"
"Implement [feature] using [technology]"

# Bug fixes
"Fix [issue] in [component]"
"Resolve [error] when [condition]"
"Debug [problem] occurring in [context]"

# Security tasks
"Add [security measure] to [component]"
"Implement [protection] against [threat]"
"Secure [endpoint] with [method]"
```

### 🔄 Handoff Packet Structure

```json
{
  "completed_task_id": "TASK-001",
  "agent_name": "Coder",
  "status": "SUCCESS",
  "artifacts_produced": ["auth.py", "tests.py"],
  "next_step_suggestion": "CODE_REVIEW",
  "notes": "Implementation complete with unit tests",
  "timestamp": "2025-01-25T10:30:00Z"
}
```

### 🎯 Next Step Suggestions

| Suggestion | Meaning | Next Agent |
|------------|---------|------------|
| `CODE_REVIEW` | Code ready for review | Code_Reviewer |
| `TESTING_NEEDED` | Tests required | QA_Guardian |
| `IMPLEMENTATION_NEEDED` | Ready for coding | Coder |
| `HUMAN_APPROVAL_NEEDED` | Human decision required | Human |
| `DEPLOY_TO_STAGING` | Ready for staging | DevOps_Specialist |
| `SECURITY_SCAN_NEEDED` | Security review required | Security_Specialist |
| `DOCUMENTATION_NEEDED` | Documentation required | Technical_Writer |

### 🚨 Troubleshooting Quick Fixes

#### Common Issues
```python
# System not starting
if not orchestrator.is_system_healthy():
    health_report = orchestrator.get_health_report()
    print(health_report)

# Agent not responding
available_agents = orchestrator.agent_factory.list_available_agents()
if "Coder" not in available_agents:
    orchestrator.agent_factory.restart_agent("Coder")

# Cache issues
if cache_issues:
    orchestrator.llm_cache.clear_cache()
    orchestrator.caching_enabled = False
```

#### Debug Mode
```python
# Enable debug logging
orchestrator.set_debug_mode(True)

# Get detailed logs
logs = orchestrator.log_tools.get_recent_logs(limit=100)
for log in logs:
    print(f"[{log['timestamp']}] {log['event']}")
```

### 💡 Best Practices

#### 1. **Workflow Design**
- Use descriptive requests
- Choose appropriate workflow types
- Monitor progress regularly
- Handle approvals promptly

#### 2. **Performance Optimization**
- Enable caching for repeated operations
- Use context optimization
- Monitor token usage
- Set appropriate limits

#### 3. **Error Handling**
- Enable debug mode for troubleshooting
- Check system health regularly
- Review error logs
- Use retry mechanisms

#### 4. **Security**
- Use human approval for sensitive operations
- Monitor security-related workflows
- Review artifacts before deployment
- Follow security best practices

### 📚 Documentation Links

- **[Complete System Overview](docs/SYSTEM_OVERVIEW.md)**
- **[Detailed Usage Guide](docs/guides/USAGE_GUIDE.md)**
- **[KILOCODE Integration](docs/guides/KILOCODE_INTEGRATION.md)**
- **[Adding New Agents](docs/guides/ADDING_NEW_AGENTS.md)**
- **[API Reference](docs/api/API_REFERENCE.md)**

### 🎓 Learning Path

1. **Start Here**: Run `python development/demos/final_demonstration.py`
2. **Basic Usage**: Follow the [Usage Guide](docs/guides/USAGE_GUIDE.md)
3. **Advanced Features**: Explore context optimization and caching
4. **Integration**: Set up KILOCODE integration
5. **Customization**: Create custom agents and workflows
6. **Production**: Deploy and monitor in production environment

---

*Keep this reference handy for quick access to the most common commands and patterns in the Autonomous Multi-Agent Software Development System.*
