בהחלט. זהו שלב קריטי - לוודא שלא רק הגדרנו את הסוכנים, אלא שיש לנו תוכנית ברורה לשלב אותם לתוך תהליך עבודה קוהרנטי. התוכנית תתמקד ב"הדבקה" של הסוכנים יחד, תוך שימת דגש על העברת המקל וההחלטה "מי הבא בתור?".

התוכנית הבאה מתארת איך לשלב כל סוכן וסוכן לתוך ה-Workflows, ומוסיפה מנגנון קבלת החלטות שיאפשר למערכת להיות דינמית וחכמה יותר.

---
---

### **Action Plan: Agent Integration and Intelligent Workflow Orchestration**

**Document Objective:** This document provides a detailed plan for integrating each defined agent into the operational workflows. It moves beyond static task chains and introduces a mechanism for the **Conductor** to intelligently decide "who's next?" based on the context and output of the previous task.

---

### **Part 1: Step-by-Step Agent Integration Plan**

This plan outlines how to progressively add each agent into the main workflow, ensuring each one has a clear entry point, task, and hand-off procedure. We will build upon the completed `Workflow 2` (Complex UI Feature) as our base case.

**Prerequisite:** The core loop managed by the **Conductor** is running. The `Librarian` and `Git Agent` are functioning as core services.

**Step 1: Integrate the Planning Trio (Analyst, UX/UI Designer, Architect)**

*   **Objective:** Solidify the initial planning phase where the core project plan is created.
*   **Integration Flow:**
    1.  **Trigger:** A new high-level request from the human user.
    2.  **Conductor's Action:** Creates a main task (e.g., `TASK-005: Plan User Profile Page`) and assigns the first sub-task (`SUB-005.1: Create Specification`) to the **Product Analyst**.
    3.  **Product Analyst's Role:** Executes the task, producing `spec.md`.
    4.  **Handoff:** Upon completion, the Analyst's final output signals that the "Specification" stage is done.
    5.  **Conductor's Action:** Assigns `SUB-005.2: Create UI/UX Design` to the **UX/UI Designer**, providing the path to `spec.md` as context.
    6.  **UX/UI Designer's Role:** Executes, producing `design_plan.md` with Mermaid diagrams.
    7.  **Conductor's Action:** Assigns `SUB-005.3: Create Technical Architecture` to the **Architect**, providing paths to both `spec.md` and `design_plan.md`.
    8.  **Architect's Role:** Executes, producing `architecture_plan.md` and environment config files.
    9.  **Completion:** The Conductor now has all three planning artifacts and can proceed to the Human Approval Gate.

**Step 2: Integrate the Execution Duo (Coder & Tester) with TDD**

*   **Objective:** Implement the core development loop using Test-Driven Development.
*   **Integration Flow (Post-Human-Approval):**
    1.  **Trigger:** User approval of the plan.
    2.  **Conductor's Action:** Creates a development task (e.g., `TASK-009: Develop Backend API`). It assigns the first sub-task (`SUB-009.1: Write Failing Test for API`) to the **Tester**.
    3.  **Tester's Role:** Gets a go-ahead, creates a new Git branch, writes a failing test, and commits.
    4.  **Handoff:** The Tester's output is a commit hash and a log confirming a failing test exists.
    5.  **Conductor's Action:** Assigns `SUB-009.2: Implement Code to Pass Test` to the **Coder**, providing the context of the failing test.
    6.  **Coder's Role:** Gets a go-ahead, writes the minimum code required to make the test pass, verifies locally, and commits to the same branch.
    7.  **Handoff:** The Coder's output is a commit hash and a log confirming the test now passes. This loop (Tester->Coder) can repeat for different functionalities within the same feature.

**Step 3: Integrate the Quality Agents (Code Reviewer & Security Specialist)**

*   **Objective:** Add the quality assurance layer that runs *after* a piece of functionality is "code complete".
*   **Integration Flow:**
    1.  **Trigger:** The `Coder` completes an implementation task.
    2.  **Conductor's Action:** Creates two **parallel** sub-tasks:
        *   `SUB-009.3.A: Review Code Quality` assigned to the **Code Reviewer**.
        *   `SUB-009.3.B: Scan Code for Security Vulnerabilities` assigned to the **Security Specialist**.
    3.  **Agents' Roles:** Both agents run concurrently on the same feature branch. The `Code Reviewer` produces `review_report.md`. The `Security Specialist` produces `security_report.md`.
    4.  **Handoff:** Both agents report their findings.
    5.  **Conductor's Action:** The Conductor gathers both reports. If either report contains critical issues, it creates a new "fix" task and re-assigns it to the `Coder`, including the reports as context. If both reports are clean, it proceeds.

**Step 4: Integrate the Finalization Agents (QA Guardian, DevOps, Technical Writer)**

*   **Objective:** Formalize the final stages of merging, deploying, and documenting.
*   **Integration Flow:**
    1.  **Trigger:** A feature branch has passed all development, testing, review, and security checks.
    2.  **Conductor's Action:** Assigns `SUB-009.4: Final Verification and Merge Approval` to the **QA Guardian**.
    3.  **QA Guardian's Role:** Reviews all artifacts and reports for the task (`spec`, `code`, `tests`, `review_report`, `security_report`). If everything is aligned, it gives the final "GO" signal.
    4.  **Handoff:** The "GO" signal from the QA Guardian.
    5.  **Conductor's Action:** Instructs the **Git Agent** to create and merge the Pull Request.
    6.  **Conductor's Action (in parallel):**
        *   Assigns a documentation task to the **Technical Writer**: "The feature `TASK-009` is now complete. Please write the relevant user and API documentation."
        *   Once the main branch is updated, assigns a deployment task to the **DevOps Specialist**: "Deploy the latest version of the main branch to the Staging environment."

---

### **Part 2: Implementing an Intelligent "Who's Next?" Mechanism**

To move beyond a hardcoded workflow, the **Conductor** needs to become a true orchestrator. This requires a "routing" mechanism.

**The "Handoff Packet" Concept**

Instead of just signaling "done," each agent's final output will be a structured "Handoff Packet" (a JSON object). This packet provides the Conductor with the context it needs to make an intelligent decision.

**Structure of a Handoff Packet:**

```json
{
  "completed_task_id": "SUB-009.2",
  "status": "SUCCESS",
  "artifacts_produced": [
    "src/api/profile.py"
  ],
  "next_step_suggestion": "CODE_REVIEW", // A key suggestion from the agent
  "notes": "Implementation is complete and all tests are passing."
}
```

**Implementing the Conductor's Routing Logic**

The Conductor's main loop will be refactored into a router.

1.  **Receive the Packet:** The Conductor receives the Handoff Packet from the completed task.
2.  **Analyze the Context:** It looks at the `completed_task_id` and the `next_step_suggestion`.
3.  **Apply Routing Rules:** The Conductor will have a set of rules, which can be a simple `if/elif/else` structure or a more complex dictionary lookup.

**Example Routing Rules in the Conductor:**

```python
def route_next_task(handoff_packet):
    suggestion = handoff_packet.get("next_step_suggestion")
    
    if suggestion == "CODE_REVIEW":
        # Rule: If code was just written, it needs review and security scan.
        create_and_assign_task("Review Code Quality", "Code_Reviewer")
        create_and_assign_task("Scan for Vulnerabilities", "Security_Specialist")
    
    elif suggestion == "IMPLEMENTATION_NEEDED":
        # Rule: If a test was just written, it needs code.
        create_and_assign_task("Implement Code to Pass Test", "Coder")
        
    elif suggestion == "MERGE_APPROVED":
        # Rule: If the QA Guardian approved, it's time to merge, document, and deploy.
        instruct_git_agent_to_merge()
        create_and_assign_task("Write Documentation", "Technical_Writer")
        create_and_assign_task("Deploy to Staging", "DevOps_Specialist")
        
    elif handoff_packet.get("status") == "FAILURE":
        # Rule: If anything failed, trigger the debugger.
        create_and_assign_task("Diagnose Failure", "Debugger")
        
    else:
        # Default/Fallback Rule: If unsure, ask the human.
        ask_human_for_clarification("Task completed. How should we proceed?")

```

**Implementation Plan for the Router:**

1.  **Phase 1 - Standardize Output:** Modify the `system_prompt` and instructions for every agent to require them to produce a structured "Handoff Packet" as their final output.
2.  **Phase 2 - Build the Router Logic:** Implement the `route_next_task` function inside the Conductor (`main.py`). Start with simple, explicit rules for your main workflows.
3.  **Phase 3 - Refine and Expand:** As you build more complex capabilities, add more sophisticated rules to the router, making the system more autonomous and less dependent on hardcoded process flows.

By following this integration plan and implementing the intelligent routing mechanism, you will create a system that is not only comprised of expert agents but also functions as a cohesive, adaptable, and truly intelligent team.