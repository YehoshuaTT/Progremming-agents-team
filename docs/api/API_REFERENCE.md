# API Reference Guide
## Autonomous Multi-Agent Software Development System

### 📋 Table of Contents

1. [Enhanced Orchestrator API](#enhanced-orchestrator-api)
2. [Agent Factory API](#agent-factory-api)
3. [Handoff System API](#handoff-system-api)
4. [Tool APIs](#tool-apis)
5. [Context Optimization API](#context-optimization-api)
6. [Caching System API](#caching-system-api)
7. [Error Handling API](#error-handling-api)
8. [Logging API](#logging-api)
9. [Data Models](#data-models)
10. [Examples](#examples)

---

## Enhanced Orchestrator API

### Class: `EnhancedOrchestrator`

The main coordination hub for all agent interactions and workflow management.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize the enhanced orchestrator with all subsystems"""
```

#### Core Methods

##### `start_workflow(request: str, workflow_type: str = "complex_ui_feature") -> str`

Start a new workflow with the given request.

**Parameters:**
- `request` (str): Description of the work to be performed
- `workflow_type` (str, optional): Type of workflow to start. Defaults to "complex_ui_feature"

**Returns:**
- `str`: Unique workflow ID

**Example:**
```python
orchestrator = EnhancedOrchestrator()
workflow_id = await orchestrator.start_workflow(
    request="Create a user authentication system",
    workflow_type="complex_ui_feature"
)
```

##### `process_agent_completion(task_id: str, agent_output: str, session_id: Optional[str] = None, is_checkpoint: bool = False) -> Dict[str, Any]`

Process the completion of an agent task.

**Parameters:**
- `task_id` (str): Unique identifier for the completed task
- `agent_output` (str): Output from the agent including handoff packet
- `session_id` (Optional[str]): Session identifier for workflow tracking
- `is_checkpoint` (bool): Whether this is a checkpoint save

**Returns:**
- `Dict[str, Any]`: Routing result with next tasks or approval requirements

**Example:**
```python
result = await orchestrator.process_agent_completion(
    task_id="TASK-001",
    agent_output="Task completed successfully. {...handoff packet...}",
    session_id="session-123"
)
```

##### `process_human_approval(approval_id: str, decision: str) -> Dict[str, Any]`

Process human approval decision.

**Parameters:**
- `approval_id` (str): Unique identifier for the approval request
- `decision` (str): Human decision ("APPROVE", "CHANGES: feedback", "REJECT: reason")

**Returns:**
- `Dict[str, Any]`: Processing result with next actions

**Example:**
```python
result = await orchestrator.process_human_approval(
    approval_id="APPROVAL-001",
    decision="APPROVE"
)
```

##### `execute_llm_call_with_cache(agent_name: str, prompt: str, context: Dict[str, Any] = None) -> str`

Execute LLM call with intelligent caching.

**Parameters:**
- `agent_name` (str): Name of the agent making the call
- `prompt` (str): LLM prompt
- `context` (Dict[str, Any], optional): Context for the call

**Returns:**
- `str`: LLM response

**Example:**
```python
response = await orchestrator.execute_llm_call_with_cache(
    agent_name="Coder",
    prompt="Implement user authentication",
    context={"specification": "auth_spec.md"}
)
```

##### `get_workflow_status(workflow_id: str) -> Dict[str, Any]`

Get the current status of a workflow.

**Parameters:**
- `workflow_id` (str): Unique workflow identifier

**Returns:**
- `Dict[str, Any]`: Workflow status information

**Example:**
```python
status = orchestrator.get_workflow_status("workflow-123")
print(f"Status: {status['status']}, Agent: {status['current_agent']}")
```

##### `get_performance_metrics() -> Dict[str, Any]`

Get system performance metrics.

**Returns:**
- `Dict[str, Any]`: Performance metrics including cache hit rates, execution times, etc.

**Example:**
```python
metrics = await orchestrator.get_performance_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']}")
```

#### Context Optimization Methods

##### `get_section_for_agent(document_path: str, section_id: str, agent_id: str) -> Dict[str, Any]`

Get specific document section for an agent with optimization.

**Parameters:**
- `document_path` (str): Path to the document
- `section_id` (str): Section identifier
- `agent_id` (str): Agent requesting the section

**Returns:**
- `Dict[str, Any]`: Section content and metadata

##### `get_context_optimization_metrics() -> Dict[str, Any]`

Get context optimization performance metrics.

**Returns:**
- `Dict[str, Any]`: Optimization metrics including token reduction percentages

#### Workflow Management

##### `start_workflow_session(workflow_name: str, initial_agent: str) -> str`

Start a new workflow session with handoff caching.

**Parameters:**
- `workflow_name` (str): Name of the workflow
- `initial_agent` (str): Initial agent to start with

**Returns:**
- `str`: Session identifier

##### `get_active_workflows() -> Dict[str, Any]`

Get all currently active workflows.

**Returns:**
- `Dict[str, Any]`: Dictionary of active workflows and their status

---

## Agent Factory API

### Class: `AgentFactory`

Factory for creating and managing agents.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize agent factory with available agents"""
```

#### Core Methods

##### `list_available_agents() -> List[str]`

List all available agent types.

**Returns:**
- `List[str]`: List of available agent names

**Example:**
```python
factory = AgentFactory()
agents = factory.list_available_agents()
print(f"Available agents: {agents}")
```

##### `create_agent(agent_name: str, task: Dict[str, Any]) -> BaseAgent`

Create an agent instance for a specific task.

**Parameters:**
- `agent_name` (str): Name of the agent to create
- `task` (Dict[str, Any]): Task specification

**Returns:**
- `BaseAgent`: Agent instance

**Example:**
```python
agent = factory.create_agent("Coder", {
    "type": "implementation",
    "requirements": "auth_spec.md"
})
```

##### `get_agent_capabilities(agent_name: str) -> List[str]`

Get capabilities of a specific agent.

**Parameters:**
- `agent_name` (str): Name of the agent

**Returns:**
- `List[str]`: List of agent capabilities

##### `get_agent_template(agent_name: str) -> str`

Get the prompt template for an agent.

**Parameters:**
- `agent_name` (str): Name of the agent

**Returns:**
- `str`: Agent prompt template

---

## Handoff System API

### Class: `HandoffPacket`

Data structure for agent communication.

#### Constructor

```python
def __init__(self, completed_task_id: str, agent_name: str, status: TaskStatus, 
             artifacts_produced: List[str], next_step_suggestion: NextStepSuggestion,
             notes: str, timestamp: str, dependencies_satisfied: List[str] = None,
             blocking_issues: List[str] = None) -> None:
```

#### Attributes

- `completed_task_id` (str): Unique identifier for the completed task
- `agent_name` (str): Name of the agent that completed the task
- `status` (TaskStatus): Status of the task completion
- `artifacts_produced` (List[str]): List of artifacts created
- `next_step_suggestion` (NextStepSuggestion): Suggested next step
- `notes` (str): Additional notes about the completion
- `timestamp` (str): ISO format timestamp
- `dependencies_satisfied` (List[str]): Dependencies that were satisfied
- `blocking_issues` (List[str]): Issues that are blocking progress

### Class: `ConductorRouter`

Intelligent router for agent handoffs.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize router with routing rules"""
```

#### Core Methods

##### `route_next_task(handoff_packet: HandoffPacket) -> Dict[str, Any]`

Route the next task based on handoff packet.

**Parameters:**
- `handoff_packet` (HandoffPacket): Handoff packet from completed task

**Returns:**
- `Dict[str, Any]`: Routing decision with next agents and tasks

##### `can_route_to_agent(agent_name: str, task_type: str) -> bool`

Check if an agent can handle a specific task type.

**Parameters:**
- `agent_name` (str): Name of the agent
- `task_type` (str): Type of task

**Returns:**
- `bool`: True if agent can handle the task

---

## Tool APIs

### Task Tools (`task_tools`)

#### `create_task(task_id: str, agent_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]`

Create a new task.

**Parameters:**
- `task_id` (str): Unique task identifier
- `agent_name` (str): Agent assigned to the task
- `task_data` (Dict[str, Any]): Task specification

**Returns:**
- `Dict[str, Any]`: Created task information

#### `get_task_status(task_id: str) -> Dict[str, Any]`

Get the status of a task.

**Parameters:**
- `task_id` (str): Task identifier

**Returns:**
- `Dict[str, Any]`: Task status information

#### `update_task_status(task_id: str, status: str, notes: str = None) -> None`

Update task status.

**Parameters:**
- `task_id` (str): Task identifier
- `status` (str): New status
- `notes` (str, optional): Additional notes

### File Tools (`file_tools`)

#### `read_file(file_path: str) -> str`

Read file contents.

**Parameters:**
- `file_path` (str): Path to the file

**Returns:**
- `str`: File contents

#### `write_file(file_path: str, content: str) -> None`

Write content to file.

**Parameters:**
- `file_path` (str): Path to the file
- `content` (str): Content to write

#### `ensure_directory_exists(directory_path: str) -> None`

Ensure directory exists, create if necessary.

**Parameters:**
- `directory_path` (str): Path to the directory

### Git Tools (`git_tools`)

#### `git_commit(message: str, files: List[str] = None) -> Dict[str, Any]`

Commit changes to git repository.

**Parameters:**
- `message` (str): Commit message
- `files` (List[str], optional): Specific files to commit

**Returns:**
- `Dict[str, Any]`: Commit result

#### `git_push(branch: str = "main") -> Dict[str, Any]`

Push changes to remote repository.

**Parameters:**
- `branch` (str, optional): Branch to push. Defaults to "main"

**Returns:**
- `Dict[str, Any]`: Push result

#### `git_create_branch(branch_name: str) -> Dict[str, Any]`

Create a new git branch.

**Parameters:**
- `branch_name` (str): Name of the new branch

**Returns:**
- `Dict[str, Any]`: Branch creation result

---

## Context Optimization API

### Class: `DocumentSummaryGenerator`

Generates optimized summaries of documents.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize document summary generator"""
```

#### Core Methods

##### `generate_summary(document_path: str, optimization_level: str = "standard") -> Dict[str, Any]`

Generate document summary with section mapping.

**Parameters:**
- `document_path` (str): Path to the document
- `optimization_level` (str, optional): Level of optimization. Defaults to "standard"

**Returns:**
- `Dict[str, Any]`: Document summary with sections and metadata

**Example:**
```python
generator = DocumentSummaryGenerator()
summary = generator.generate_summary("spec.md")
print(f"Document has {len(summary['sections'])} sections")
```

##### `get_document_section(document_path: str, section_id: str) -> Dict[str, Any]`

Get specific section of a document.

**Parameters:**
- `document_path` (str): Path to the document
- `section_id` (str): Section identifier

**Returns:**
- `Dict[str, Any]`: Section content and metadata

##### `estimate_token_count(text: str) -> int`

Estimate token count for text.

**Parameters:**
- `text` (str): Text to analyze

**Returns:**
- `int`: Estimated token count

---

## Caching System API

### Class: `LLMCacheManager`

Manages LLM response caching.

#### Constructor

```python
def __init__(self, cache_size_mb: int = 100) -> None:
    """Initialize LLM cache manager"""
```

#### Core Methods

##### `get_cached_response(prompt_hash: str) -> Optional[str]`

Get cached response for a prompt.

**Parameters:**
- `prompt_hash` (str): Hash of the prompt

**Returns:**
- `Optional[str]`: Cached response if available

##### `cache_response(prompt_hash: str, response: str, metadata: Dict[str, Any] = None) -> None`

Cache an LLM response.

**Parameters:**
- `prompt_hash` (str): Hash of the prompt
- `response` (str): LLM response
- `metadata` (Dict[str, Any], optional): Additional metadata

##### `get_cache_stats() -> Dict[str, Any]`

Get cache performance statistics.

**Returns:**
- `Dict[str, Any]`: Cache statistics including hit rate, size, etc.

##### `clear_cache() -> None`

Clear all cached responses.

---

## Error Handling API

### Class: `ErrorClassifier`

Classifies and categorizes errors.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize error classifier"""
```

#### Core Methods

##### `classify_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]`

Classify an error and determine recovery strategy.

**Parameters:**
- `error` (Exception): The error to classify
- `context` (Dict[str, Any], optional): Context where error occurred

**Returns:**
- `Dict[str, Any]`: Error classification and recovery recommendations

##### `get_recovery_strategy(error_type: str) -> Dict[str, Any]`

Get recovery strategy for an error type.

**Parameters:**
- `error_type` (str): Type of error

**Returns:**
- `Dict[str, Any]`: Recovery strategy

### Class: `RetryManager`

Manages retry logic for failed operations.

#### Constructor

```python
def __init__(self, max_retries: int = 3, base_delay: float = 1.0) -> None:
    """Initialize retry manager"""
```

#### Core Methods

##### `should_retry(error: Exception, attempt: int) -> bool`

Determine if operation should be retried.

**Parameters:**
- `error` (Exception): The error that occurred
- `attempt` (int): Current attempt number

**Returns:**
- `bool`: True if should retry

##### `get_retry_delay(attempt: int) -> float`

Get delay before retry attempt.

**Parameters:**
- `attempt` (int): Current attempt number

**Returns:**
- `float`: Delay in seconds

---

## Logging API

### Log Tools (`log_tools`)

#### `record_log(task_id: str, event: str, data: Dict[str, Any]) -> None`

Record a log entry.

**Parameters:**
- `task_id` (str): Task identifier
- `event` (str): Event type
- `data` (Dict[str, Any]): Log data

#### `get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]`

Get recent log entries.

**Parameters:**
- `limit` (int, optional): Maximum number of logs to return. Defaults to 100

**Returns:**
- `List[Dict[str, Any]]`: List of log entries

#### `search_logs(query: str, time_range: str = "all") -> List[Dict[str, Any]]`

Search logs by query.

**Parameters:**
- `query` (str): Search query
- `time_range` (str, optional): Time range for search. Defaults to "all"

**Returns:**
- `List[Dict[str, Any]]`: Matching log entries

#### `set_log_level(level: str) -> None`

Set logging level.

**Parameters:**
- `level` (str): Logging level ("DEBUG", "INFO", "WARNING", "ERROR")

---

## Data Models

### Enums

#### `TaskStatus`

```python
class TaskStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
```

#### `NextStepSuggestion`

```python
class NextStepSuggestion(Enum):
    CODE_REVIEW = "CODE_REVIEW"
    IMPLEMENTATION_NEEDED = "IMPLEMENTATION_NEEDED"
    TESTING_NEEDED = "TESTING_NEEDED"
    MERGE_APPROVED = "MERGE_APPROVED"
    DEPLOY_TO_STAGING = "DEPLOY_TO_STAGING"
    DEPLOY_TO_PRODUCTION = "DEPLOY_TO_PRODUCTION"
    HUMAN_APPROVAL_NEEDED = "HUMAN_APPROVAL_NEEDED"
    DOCUMENTATION_NEEDED = "DOCUMENTATION_NEEDED"
    SECURITY_SCAN_NEEDED = "SECURITY_SCAN_NEEDED"
    DEBUG_NEEDED = "DEBUG_NEEDED"
```

### Data Structures

#### `TaskCheckpoint`

```python
@dataclass
class TaskCheckpoint:
    task_id: str
    agent_name: str
    checkpoint_data: Dict[str, Any]
    timestamp: str
    status: TaskStatus
```

#### `ErrorInfo`

```python
@dataclass
class ErrorInfo:
    error_type: str
    error_message: str
    error_context: Dict[str, Any]
    timestamp: str
    severity: str
    recovery_attempted: bool
```

---

## Examples

### Complete Workflow Example

```python
import asyncio
from core.enhanced_orchestrator import EnhancedOrchestrator

async def main():
    # Initialize orchestrator
    orchestrator = EnhancedOrchestrator()
    
    # Start workflow
    workflow_id = await orchestrator.start_workflow(
        request="Create a REST API for user management",
        workflow_type="complex_ui_feature"
    )
    
    print(f"Started workflow: {workflow_id}")
    
    # Monitor workflow
    while True:
        status = orchestrator.get_workflow_status(workflow_id)
        print(f"Status: {status['status']}, Agent: {status['current_agent']}")
        
        if status['status'] in ['completed', 'failed']:
            break
        
        # Check for human approval
        if status['status'] == 'awaiting_approval':
            approval_id = status['approval_id']
            decision = input("Enter decision (APPROVE/CHANGES:/REJECT:): ")
            
            result = await orchestrator.process_human_approval(
                approval_id=approval_id,
                decision=decision
            )
            print(f"Approval processed: {result}")
        
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent Creation Example

```python
from tools.agent_factory import AgentFactory
from tools.handoff_system import HandoffPacket, TaskStatus, NextStepSuggestion

# Create agent factory
factory = AgentFactory()

# Create agent
agent = factory.create_agent("Coder", {
    "type": "implementation",
    "requirements": "Create authentication middleware",
    "context": {"framework": "FastAPI"}
})

# Execute task
task = {
    "task_id": "TASK-001",
    "type": "implementation",
    "requirements": "Implement JWT authentication",
    "context": {"framework": "FastAPI"}
}

result = await agent.execute_task(task)
print(f"Task completed with status: {result.status}")
```

### Context Optimization Example

```python
from tools.document_summary_generator import DocumentSummaryGenerator

# Initialize generator
generator = DocumentSummaryGenerator()

# Generate summary
summary = generator.generate_summary("requirements.md")
print(f"Document sections: {len(summary['sections'])}")

# Get specific section
section = generator.get_document_section("requirements.md", "SEC-001")
print(f"Section content: {section['content'][:100]}...")
```

### Caching Example

```python
from tools.llm_cache import llm_cache

# Cache response
await llm_cache.cache_response(
    prompt_hash="abc123",
    response="Implementation complete",
    metadata={"agent": "Coder", "timestamp": "2025-01-25T10:00:00Z"}
)

# Get cached response
cached = await llm_cache.get_cached_response("abc123")
if cached:
    print(f"Using cached response: {cached}")

# Get cache statistics
stats = llm_cache.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']}")
```

### Error Handling Example

```python
from tools.error_handling import error_classifier, retry_manager

try:
    # Some operation that might fail
    result = await some_operation()
except Exception as e:
    # Classify error
    error_info = error_classifier.classify_error(e, {"context": "agent_execution"})
    
    # Check if should retry
    if retry_manager.should_retry(e, attempt=1):
        delay = retry_manager.get_retry_delay(attempt=1)
        await asyncio.sleep(delay)
        # Retry operation
    else:
        # Handle failure
        print(f"Operation failed: {error_info}")
```

---

*This API reference provides comprehensive documentation for all public interfaces in the Autonomous Multi-Agent Software Development System. Use these APIs to integrate with and extend the system's capabilities.*
