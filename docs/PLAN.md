Master Document: Autonomous Software Development Team Architecture


  1. System Description: Autonomous Software Development Team


  The system we have described is a Multi-Agent System that simulates a
  holistic, intelligent, and efficient software development team. Its
  purpose is to take a general requirement from a human user and
  translate it into a working, documented, and secure software product,
  managing all stages of the process automatically.


  Core Principles of the System:


   1. Single Source of Truth: The system does not rely on volatile memory.       
      All information—tasks, decisions, code, documentation, and logs—is
      stored in a structured file and folder system within a Git
      repository. This is the "collective brain" of the team.
   2. Structured and Hierarchical Communication: Agents do not "talk"
      freely. Communication is managed by the management agents (primarily       
      the "Conductor" and the "Librarian"), who transfer tasks and
      deliverables in a defined format between the various agents.
   3. Task Decomposition: No agent receives a huge task. The system excels       
      at breaking down large goals into small, atomic, and measurable
      tasks, each with a unique identifier.
   4. Verification Loop: No deliverable is accepted as "done" without human      
      or automated verification. Code undergoes review and testing,
      specifications undergo logical validation, and design is checked
      against requirements. The process only proceeds after explicit
      approval.

  ---

  2. List of Agents in the Team

  Group A: Management, Orchestration & Control Agents


   * The Conductor / Project Manager
   * The Librarian / Documentation & Process Manager
   * The Architect
   * The Quality Assurance Guardian
   * The Git Agent / Configuration Manager

  Group B: Technical, Execution & Specialist Agents


   * The Product Analyst / Specification Writer
   * The UX/UI Designer
   * The Coder / Developer
   * The Code Reviewer
   * The Tester
   * The DevOps Specialist / Deployment Manager
   * The Security Specialist
   * The Technical Writer
   * The Debugger
   * The Ask Agent

  ---

  3. Expanded Agent Roles

  Group A: Management, Orchestration & Control Agents


  1. The Conductor / Project Manager
   * Essence: The central brain and entry point of the system.
     Communicates with the human user.
   * Key Responsibilities:
       * Receive the initial requirement and break it down into main
         stages (specification, design, development, etc.).
       * Assign the main tasks to the appropriate agents.
       * Orchestrate the workflow between the different agents, including        
         closing dependency loops (e.g., starting the Frontend task after        
         the Backend is complete).
       * Manage control and approval points with the human user.
   * Place in the Process: At the top of the pyramid, communicating with
     all primary agents.


  2. The Librarian / Documentation & Process Manager
   * Essence: The central nervous system and memory of the project.
     Enforces order and process.
   * Key Responsibilities:
       * Assign a unique serial number to each task and sub-task.
       * Document every action and event in an event log
         (event_log.jsonl).
       * Provide other agents with "history" and "context" on demand.
       * Enforce the order of tasks and ensure that steps are not skipped.       
       * Semantic Indexing: Automatically parse new documents
         (specifications, architecture) and index them in a free vector
         database (like ChromaDB) for future semantic search.
   * Place in the Process: Every task passes through it to receive an ID
     and documentation. It serves all agents.


  3. The Architect
   * Essence: The lead technology planner. Thinks about the big picture
     before a line of code is written.
   * Key Responsibilities:
       * Choose the technologies (languages, databases, libraries).
       * Define the overall architecture.
       * Produce diagrams and technical documents describing the system
         structure.
       * Configuration Management: Define the structure of configuration
         files for different environments (e.g., config.development.json,        
         config.staging.json, config.production.json).
   * Place in the Process: After the specification phase and before the
     development phase.


  4. The Quality Assurance Guardian
   * Essence: The conscience of the system. Responsible for the final
     approval of deliverables.
   * Key Responsibilities:
       * Ensure the specification is complete and free of contradictions.        
       * Ensure that all deliverables (code, design) meet the original
         requirements.
       * Finally approve the results of the automated tests.
   * Place in the Process: A central checkpoint after every significant
     stage.


  5. The Git Agent / Configuration Manager
   * Essence: The technical expert for version control. Executes all
     operations against the Git repository.
   * Key Responsibilities:
       * Create new branches for each task.
       * Commit changes with standardized messages linked to the task ID.        
       * Create and manage Pull Requests.
       * Merge code into the main branch and delete completed branches.
   * Place in the Process: A service agent that all other agents creating        
     files use.


  Group B: Technical & Specialist Agents


  6. The Product Analyst / Specification Writer
   * Essence: Translates the user's raw idea into a detailed and clear
     requirements document.
   * Key Responsibilities: Writing User Stories, acceptance criteria, or
     Behavior-Driven Development (BDD) descriptions.
   * Place in the Process: In the first stage, receives the requirement
     from the "Conductor".


  7. The UX/UI Designer
   * Essence: Responsible for the look and feel of the application, and
     its ease of use.
   * Key Responsibilities: Creating sketches and visual layouts using
     text-based diagram languages (like Mermaid.js). This allows for the
     creation of flowcharts, component diagrams, and wireframes directly
     within Markdown files, without the need for an external graphical
     tool.
   * Main Deliverables: A Markdown file (design_plan.md) containing the
     design in Mermaid format.
   * Place in the Process: Receives the specification from the "Analyst"
     and passes the design to the "Coder".


  8. The Coder / Developer
   * Essence: The workhorse. Writes the actual code, according to a
     well-defined task.
   * Key Responsibilities: Writing clean and efficient code that
     implements the requirements, design, and architecture.
   * Place in the Process: The heart of the development work. Receives a
     task from the "Conductor" and submits the deliverable to the "Git
     Agent".


  9. The Code Reviewer
   * Essence: A special quality inspector for code. Checks the logic and
     quality, not just if the code works.
   * Key Responsibilities: Checking for readability, efficiency,
     maintainability, and adherence to good design principles.
   * Place in the Process: After the "Coder" and before the code is passed       
     for broader testing.


  10. The Tester
   * Essence: Writes and runs automated tests to ensure the code does what       
     it is supposed to do.
   * Key Responsibilities: Writing Unit Tests, Integration Tests, and
     End-to-End Tests.
   * Place in the Process: Operates in parallel with or after (and in TDD        
     methodology, before) the Coder.


  11. The DevOps Specialist / Deployment Manager
   * Essence: Takes the code that has passed all tests and ensures it runs       
     in the target environment.
   * Key Responsibilities: Packaging the application (e.g., Docker),
     writing deployment scripts (CI/CD), setting up infrastructure, and
     using the environment-specific configuration files (config.*.json)
     defined by the Architect.
   * Place in the Process: The final stage, after development and testing        
     are complete.


  12. The Security Specialist
   * Essence: A dedicated security expert who operates throughout the
     project lifecycle.
   * Key Responsibilities: Reviewing specifications and architecture to
     identify vulnerabilities, running security scans on the code, and
     checking dependencies.
   * Place in the Process: Integrated into all stages, from specification        
     to deployment.


  13. The Technical Writer
   * Essence: Responsible for creating clear and useful documentation for        
     developers and end-users.
   * Key Responsibilities: Writing API documentation, user guides, and
     internal architecture documentation.
   * Place in the Process: Operates in parallel with development,
     documenting features as they are built.

  14. The Debugger
   * Essence: An expert software debugger specializing in systematic problem diagnosis and resolution.
   * Key Responsibilities:
       * Troubleshooting issues, investigating errors, and diagnosing problems.
       * Adding logging to validate assumptions.
       * Analyzing stack traces and identifying root causes before applying fixes.
   * Place in the Process: Called upon by the Orchestrator when a task fails or an error is detected.

  15. The Ask Agent
   * Essence: A knowledgeable technical assistant focused on answering questions and providing information about software development, technology, and related topics.
   * Key Responsibilities:
       * Answering technical questions.
       * Explaining concepts.
       * Analyzing existing code.
       * Providing recommendations.
   * Place in the Process: A service agent that can be called by any other agent to get information.

  ---

  4. Universal Behavior Protocol (The Constitution)


  These are the procedures and rules that every agent in the system is
  obligated to follow. Enforcing these procedures does not require a
  separate agent, but is built into the system's execution loop (Agent 
  Runner / Orchestrator). This loop, managed by the "Conductor," is
  responsible for activating these procedures before and after each
  agent activation, thus making them part of the infrastructure and not
  something the agent can "forget."


   1. Task Start Protocol (The "Onboarding" Protocol):
       * Principle: Do not start work "blindly."
       * Process: Before activating an agent, the execution loop
         automatically gathers all context for it from the "Librarian"
         (specification, architecture, history). The agent proactively
         analyzes the briefing and sends a "request for go-ahead." Work
         begins only after receiving approval from the "Conductor."


   2. Communication and Dependency Protocol (The "Ask, Don't Assume" 
      Protocol):
       * Principle: Assumptions are the source of errors.
       * Process: If an agent encounters a lack of information, it returns       
         a "waiting for clarification" status to the execution loop. The
         loop forwards the detailed query to the "Conductor," who can
         answer, route to another agent, or ask the human user.


   3. Task Completion Protocol (The "Definition of Done" Protocol):
       * Principle: A task is done only when it meets a defined standard.        
       * Process: After the agent finishes, the execution loop checks its        
         deliverables against the task's "Definition of Done" checklist
         before passing the baton to the next agent in the chain.


   4. Error Handling Protocol (The "Fail Gracefully" Protocol):
       * Principle: Failure is a learning opportunity.
       * Process: If an agent fails, the execution loop catches the error,       
         documents it with all relevant logs, and automatically initiates        
         the correction process, including sending a failure report to the       
         appropriate agent.


   5. Focus Maintenance Protocol (The "Single Responsibility" Protocol):
       * Principle: Each agent is an expert in its field and must stay
         within it.
       * Process: Each agent's prompt clearly defines not only what it
         must do, but also what it must not do. The "QA Guardian" ensures        
         that deliverables do not exceed the task's scope.


   6. Dependency Management Protocol (The "Supply Chain" Protocol):
       * Principle: Every external dependency is a risk to be managed.
       * Process: Adding a new external library requires submitting a
         formal request and an approval process with the "Architect" and
         "Security Specialist," who check licensing, security, and
         maintenance.


   7. Confidentiality and Sensitive Information Management Protocol (The         
      "Need to Know" Protocol):
       * Principle: Sensitive information is managed securely and
         separately from the code.
       * Process: Secrets are kept out of Git (e.g., in .env files). The
         code refers only to environment variables, and the secret values        
         are injected into the environment only at runtime.


   8. Self-Documenting Protocol:
       * Principle: The priority is for code and processes that explain
         themselves.
       * Process: An inherent requirement for all agents to use clear and        
         descriptive names, add internal documentation to the code
         (Docstrings), and write commit messages that explain the "why."

  ---

  5. System Toolbox (Tools)

  Part A: Universal and General Tools


   * File Management:
       * read_file(path): "Read the content of a specific file."
       * write_file(path, content): "Write or overwrite a file with new
         content."
       * append_to_file(path, content): "Append content to the end of an
         existing file."
       * list_files(path): "Get a list of all files and folders in a given       
         path."
       * create_directory(path): "Create a new folder at the specified
         path."
   * Task and Process Management:
       * get_task_details(task_id): "Get all the structured details about        
         a specific task."
       * update_task_status(task_id, new_status, message): "Update the
         status of a task."
       * record_log(level, message, details): "Record a technical log
         event. Use this to document your steps or errors."
   * Search and Communication:
       * semantic_search_documentation(query): "Search for relevant
         information in the project documents based on meaning."
       * search_in_files(query, path): "Search for a text string within
         all files in a given path."
       * ask_human_for_clarification(question): "Stop the process and ask        
         the human user for clarification."
       * get_current_datetime(): "Get the current date and time."

  Part B: Dedicated and Specific Tools


   * Project Management (for the "Conductor"):
       * create_new_task(title, description, parent_task_id): "Create a
         new task in the system."
       * assign_task_to_agent(task_id, agent_name): "Assign a task to a
         specific agent."
       * notify_agent(agent_name, message, task_id): "Send a message to
         another agent."
   * Version Control (for the "Git Agent"):
       * git_create_branch(branch_name): "Create a new branch in Git."
       * git_add_and_commit(files_to_add, commit_message): "Commit
         changes."
       * git_push(): "Push changes to the remote repository."
       * git_create_pull_request(title, body): "Create a Pull Request."
   * Command Execution and Testing (for relevant technical agents):
       * execute_shell_command(command): "Run a shell (terminal) command."       
       * run_tests(path): "Run all automated tests in the project."
       * lint_code(path): "Run a Linter on the code to check standards."
   * Security and Secrets (for Security and DevOps agents):
       * run_security_scan(path): "Run a static security scan (SAST) on
         the code."
       * check_dependencies(): "Scan the project dependencies for
         vulnerabilities."
       * get_environment_variable(variable_name): "Read the value of an
         environment variable."

  ---

  6. Full Workflows

  Workflow 1: Simple and Linear (with Enhanced Controls)


  Feature: Add the ability to export a user list to a CSV file.


   1. Step 0: Request: The human user requests the feature from the
      "Conductor."
   2. Step 1: Specification and Planning:
       * The "Conductor" assigns TASK-001 to the "Analyst."
       * The "Analyst" activates the "Task Start Protocol," gets approval,       
         and writes a specification.
       * The "Conductor" assigns TASK-002 to the "Architect."
       * The "Architect" activates the "Task Start Protocol," gets
         approval, and writes a technical plan.
   3. Step 2: Human Approval Gate:
       * The "Conductor" assigns TASK-003 to the "Analyst" to summarize
         the plan.
       * The "Conductor" presents the summary to the human user with the
         question "Do you approve?".
       * The process is paused until a "yes" response is received from the       
         user.
   4. Step 3: Development and Testing (TDD):
       * The "Conductor" assigns SUB-004.1 (write test) to the "Tester."
       * The "Tester" gets the go-ahead, creates a Git branch, writes a
         failing test, and commits.
       * The "Conductor" assigns SUB-004.2 (write code) to the "Coder."
       * The "Coder" gets approval, writes the code that makes the test
         pass, and commits.
       * The "Conductor" assigns SUB-004.3 (code review) to the "Code
         Reviewer."
       * The "Code Reviewer" approves the code.
   5. Step 4: Completion and Integration:
       * The "QA Guardian" verifies that everything is correct and
         instructs the "Git Agent" to create and merge a Pull Request.
       * The "Conductor" closes the task and reports to the human user.

  Workflow 2: Complex with User Interface (with Enhanced Controls)

  Feature: Build a new user profile page.


   1. Step 0: Request: The user requests the feature from the "Conductor."       
   2. Step 1: Multi-layered Planning:
       * Analyst (TASK-005) writes a specification.
       * UX/UI Agent (TASK-006) creates a design using Mermaid.js syntax
         in a design_plan.md file.
       * Architect (TASK-007) plans the API, UI components, and
         environment configuration files.
   3. Step 2: Human Approval Gate:
       * The "Conductor" instructs the "Analyst" to create a summary
         including the specification, the Mermaid diagram, and a technical       
         explanation.
       * The "Conductor" presents the summary to the human user for
         approval.
       * The process is paused until approval is received, including
         revision cycles if necessary.
   4. Step 3: Parallel Development:
       * The "Conductor" creates two main tasks: TASK-009 (Backend
         development) and TASK-010 (Frontend development).
       * The Backend team develops the API in its own Git branch.
       * The Frontend team develops the UI in a separate Git branch, using       
         mock data based on the approved API design.
   5. Step 4: Integration, Deployment, and Completion:
       * The Backend API is ready and merged into the main branch.
         TASK-009 is completed.
       * The Conductor identifies the dependency completion. It creates a        
         new sub-task under TASK-010: SUB-010.2: Integrate with live API,        
         and assigns it to the "Frontend Coder."
       * The "Frontend Coder" connects the UI to the real API.
       * After all tests pass, all branches are merged.
       * The "Conductor" assigns TASK-011 to the "DevOps Specialist" to
         deploy to Staging.
       * The "DevOps Specialist" uses the config.staging.json file to
         perform the deployment.
       * The "Conductor" sends a link to the Staging environment for final       
         approval from the human user.
       * After receiving approval, deployment to Production is carried
         out.
       * The "Conductor" closes all tasks and reports to the user.
   1. Step 0: Request: The user requests the feature from the
      "Conductor."
   2. Step 1: Multi-layered Planning:
       * Analyst (TASK-005) writes a specification.
       * UX/UI Agent (TASK-006) creates a design using Mermaid.js syntax
         in a design_plan.md file.
       * Architect (TASK-007) plans the API, UI components, and
         environment configuration files.
   3. Step 2: Human Approval Gate:
       * The "Conductor" instructs the "Analyst" to create a summary
         including the specification, the Mermaid diagram, and a
         technical explanation.
       * The "Conductor" presents the summary to the human user for
         approval.
       * The process is paused until approval is received, including
         revision cycles if necessary.
   4. Step 3: Parallel Development:
       * The "Conductor" creates two main tasks: TASK-009 (Backend
         development) and TASK-010 (Frontend development).
       * The Backend team develops the API in its own Git branch.
       * The Frontend team develops the UI in a separate Git branch,
         using mock data based on the approved API design.
   5. Step 4: Integration, Deployment, and Completion:
       * The Backend API is ready and merged into the main branch.
         TASK-009 is completed.
       * The Conductor identifies the dependency completion. It creates
         a new sub-task under TASK-010: SUB-010.2: Integrate with live
         API, and assigns it to the "Frontend Coder."
       * The "Frontend Coder" connects the UI to the real API.
       * After all tests pass, all branches are merged.
       * The "Conductor" assigns TASK-011 to the "DevOps Specialist" to




Work Plan: Dynamic Tool/Capability Integration for All Agents
Objective
Ensure that all agent implementations in the system dynamically retrieve their capabilities and available tools from the central AgentKnowledgeRegistry, rather than relying on static, hardcoded definitions.

1. Identify Static Agents
Agents currently using static capabilities (based on code review):

All agents in agent_driven_workflow.py
All agents in full_agent_workflow.py
Any other scripts or modules with hardcoded agent capability/tool lists
2. Upgrade Plan for Each Static Agent
For each static agent implementation:

Locate the agent’s capability/tool definition.
Replace static definitions with a call to the central registry, e.g.:
Use get_agent_capabilities(agent_name) or get_agent_tools(agent_name) from the registry.
If async context is not available, refactor to support async or use a synchronous wrapper.
Inject or initialize the registry in the agent’s context or constructor.
Update all logic that relies on static lists to use the dynamic data structure returned by the registry.
Test: Ensure the agent now always reflects the latest tools/capabilities, including new ones added dynamically.
3. Code Refactoring Steps
Refactor agent_driven_workflow.py:
Remove the static agent_capabilities dictionary.
On agent initialization or before each action, fetch the agent’s capabilities/tools from the registry.
Refactor full_agent_workflow.py and similar scripts:
Replace any hardcoded agent logic with dynamic queries to the registry.
Add dependency injection or initialization logic for the registry where needed.
4. Validation
Add or update tests to verify that:
Agents always receive the latest list of tools/capabilities.
Adding a new tool to the system is immediately reflected in agent behavior without code changes.
Document the new pattern in the developer guide.
5. Documentation
Update the QUICK_REFERENCE.md and developer docs to instruct future contributors to always use the registry for agent capabilities/tools.
Add code examples for dynamic capability retrieval.
6. Agents to Update (Initial List)
Agent Name	Static File(s)	Dynamic?
Product_Analyst	agent_driven_workflow.py	❌
UX_UI_Designer	agent_driven_workflow.py	❌
Architect	agent_driven_workflow.py	❌
Tester	agent_driven_workflow.py	❌
Coder	agent_driven_workflow.py	❌
Code_Reviewer	agent_driven_workflow.py	❌
Security_Specialist	agent_driven_workflow.py	❌
QA_Guardian	agent_driven_workflow.py	❌
DevOps_Specialist	agent_driven_workflow.py	❌
Technical_Writer	agent_driven_workflow.py	❌
Debugger	agent_driven_workflow.py	❌
Git_Agent	agent_driven_workflow.py	❌
Ask_Agent	agent_driven_workflow.py	❌
Developer	full_agent_workflow.py	❌
QA_Engineer	full_agent_workflow.py	❌
7. Timeline & Milestones
Refactor one agent as a template (1 day)
Refactor all remaining static agents (2-3 days)
Update tests and documentation (1 day)
Review and merge (1 day)
Note: Agents managed via AgentFactory and EnhancedOrchestrator already support dynamic capabilities and do not require changes.

