#!/usr/bin/env python3

# Calculate current prompt size
sample_prompt = """
AGENT ROLE: Coder
====================

ORIGINAL USER REQUEST:
Create a todo app

YOUR SPECIALTIES:
coding, implementation, programming, clean_code

CURRENT WORKFLOW CONTEXT:
{
  "user_request": "Create a todo app",
  "execution_history": ["Product_Analyst"],
  "artifacts": ["spec.md"],
  "current_step": 2
}

YOUR TASK:
1. Complete your specialized work for this request
2. Evaluate the current state and quality of work  
3. Decide on the next step in the workflow

DECISION FRAMEWORK:
===================

After completing your work, you MUST end your response with ONE of these decision tags:

🎯 PRIMARY DECISIONS:
[COMPLETE] - Task is fully completed, no further work needed
[NEXT_AGENT: AgentName] - Continue to specific agent
[HUMAN_REVIEW] - Need human intervention or approval

🔄 WORKFLOW CONTROL:
[RETRY] - Retry current task
[PARALLEL: Agent1,Agent2] - Execute multiple agents simultaneously
[BRANCH: condition] - Create conditional workflow branch

🧠 DECISION FACTORS TO CONSIDER:
• Code quality
• Implementation completeness
• Test passing

🔗 TYPICAL NEXT AGENTS FOR Coder:
• Code_Reviewer
• Tester
• Debugger

📊 QUALITY THRESHOLDS:
• High Quality Work → [COMPLETE] or [NEXT_AGENT: appropriate_agent]
• Medium Quality Work → [NEXT_AGENT: QA_Guardian] or [RETRY]
• Low Quality Work → [RETRY] or [HUMAN_REVIEW]
• Security Concerns → [NEXT_AGENT: Security_Specialist]
• Performance Issues → [NEXT_AGENT: Performance_Engineer]
• Deployment Ready → [NEXT_AGENT: DevOps_Specialist]

🤖 ALL AVAILABLE AGENTS IN SYSTEM:
Main Workflow: Product_Analyst, UX_UI_Designer, Architect, Tester, Coder, 
Code_Reviewer, Security_Specialist, QA_Guardian, DevOps_Specialist, 
Technical_Writer, Debugger, Git_Agent, Ask_Agent

🎯 EXAMPLES:
• "The code is well-tested and secure. [COMPLETE]"
• "Code needs quality review before deployment. [NEXT_AGENT: Code_Reviewer]"
• "Security analysis required due to authentication features. [NEXT_AGENT: Security_Specialist]"
• "Requirements are unclear, need clarification. [HUMAN_REVIEW]"
• "Multiple aspects need attention simultaneously. [PARALLEL: Tester,Security_Specialist]"
• "UI design needed for better user experience. [NEXT_AGENT: UX_UI_Designer]"
• "Architecture review required for scalability. [NEXT_AGENT: Architect]"

Now, complete your specialized work and make your decision!
"""

print(f"📏 Current prompt size:")
print(f"   Characters: {len(sample_prompt):,}")
print(f"   Words: {len(sample_prompt.split()):,}")
print(f"   Tokens (estimate): {len(sample_prompt) // 4:,}")

# Calculate what causes the size
sections = {
    "Title + Original Request": 200,
    "Specialties": 100,
    "Context": 300,
    "Tasks": 200,
    "Decision Framework": 500,
    "Decision Factors": 150,
    "Typical Agents": 100,
    "Quality Levels": 400,
    "All Agents in System": 300,
    "Examples": 800
}

print(f"\n📊 Prompt size breakdown:")
total = 0
for section, size in sections.items():
    print(f"   {section}: ~{size:,} chars")
    total += size

print(f"\n💡 Total estimate: {total:,} chars")
print(f"   Avg chars per token: 4")
print(f"   Estimated tokens: {total // 4:,}")

# Reduction strategies
print(f"\n🎯 Reduction strategies:")
print(f"1. Remove examples: -{sections['Examples']:,} chars")
print(f"2. Remove all agents list: -{sections['All Agents in System']:,} chars")
print(f"3. Compress quality levels: -{sections['Quality Levels']//2:,} chars")
print(f"4. Compress decision framework: -{sections['Decision Framework']//2:,} chars")

savings = sections['Examples'] + sections['All Agents in System'] + sections['Quality Levels']//2 + sections['Decision Framework']//2
print(f"\n💰 Potential savings: {savings:,} chars ({savings//4:,} tokens)")
print(f"📉 New size: {total - savings:,} chars ({(total - savings)//4:,} tokens)")

print("\n" + "="*80)
print("🎯 PROMPT OPTIMIZATION IMPLEMENTATION PLAN")
print("="*80)

print("\n📋 PHASE 1: IMMEDIATE REMOVALS (No Effectiveness Impact)")
print("-" * 60)

removals = [
    {
        "component": "🤖 ALL AVAILABLE AGENTS IN SYSTEM section",
        "tokens_saved": 75,
        "reason": "Agent already knows their typical next agents from agent_capabilities. Full list is redundant.",
        "implementation": "Remove entire section - replace with dynamic lookup in code"
    },
    {
        "component": "🎯 EXAMPLES section", 
        "tokens_saved": 200,
        "reason": "Examples are redundant with decision factors. Agent can infer from context.",
        "implementation": "Remove all 7 examples - keep only the decision tags format"
    },
    {
        "component": "📊 QUALITY THRESHOLDS detailed mappings",
        "tokens_saved": 100, 
        "reason": "Over-prescriptive. Agent should use judgment based on specialties.",
        "implementation": "Replace with simple: 'Use your expertise to decide quality level'"
    },
    {
        "component": "🔄 WORKFLOW CONTROL advanced options",
        "tokens_saved": 50,
        "reason": "PARALLEL and BRANCH are not implemented in code. Only confuses agent.",
        "implementation": "Remove PARALLEL and BRANCH options - keep only COMPLETE, NEXT_AGENT, HUMAN_REVIEW, RETRY"
    }
]

total_phase1_savings = sum(r["tokens_saved"] for r in removals)
for removal in removals:
    print(f"\n✂️  {removal['component']}")
    print(f"    💰 Tokens saved: {removal['tokens_saved']}")
    print(f"    🧠 Why safe: {removal['reason']}")
    print(f"    🔧 How: {removal['implementation']}")

print(f"\n📊 Phase 1 Total Savings: {total_phase1_savings} tokens (73% reduction)")

print("\n📋 PHASE 2: STRUCTURAL IMPROVEMENTS")
print("-" * 60)

improvements = [
    {
        "change": "Use System Message for Role Definition",
        "current_tokens": 150,
        "new_tokens": 0,
        "benefit": "System messages don't count toward input tokens in most APIs"
    },
    {
        "change": "Context Filtering by Agent Type", 
        "current_tokens": 75,
        "new_tokens": 25,
        "benefit": "Only include relevant context (e.g., only security context for Security_Specialist)"
    },
    {
        "change": "Compressed Decision Format",
        "current_tokens": 125,
        "new_tokens": 30,
        "benefit": "Single line format: 'Decision: [TAG] - Reason: brief explanation'"
    }
]

total_phase2_savings = sum(i["current_tokens"] - i["new_tokens"] for i in improvements)
for improvement in improvements:
    savings = improvement["current_tokens"] - improvement["new_tokens"] 
    print(f"\n🔄 {improvement['change']}")
    print(f"    📉 {improvement['current_tokens']} → {improvement['new_tokens']} tokens (-{savings})")
    print(f"    ✨ Benefit: {improvement['benefit']}")

print(f"\n📊 Phase 2 Total Savings: {total_phase2_savings} tokens")

print("\n📋 PHASE 3: AGENT-SPECIFIC OPTIMIZATION")
print("-" * 60)

agent_templates = {
    "Coder": {
        "system": "You are a Coder. Write clean, functional code with tests.",
        "user_template": "Task: {task}\nContext: {code_context}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]",
        "tokens": 45
    },
    "Tester": {
        "system": "You are a Tester. Create comprehensive test plans and automated tests.",
        "user_template": "Task: {task}\nCode: {code_artifacts}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]", 
        "tokens": 40
    },
    "QA_Guardian": {
        "system": "You are QA Guardian. Final quality check before deployment approval.",
        "user_template": "Task: {task}\nArtifacts: {all_artifacts}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]",
        "tokens": 42
    },
    "Security_Specialist": {
        "system": "You are Security Specialist. Identify vulnerabilities and security requirements.",
        "user_template": "Task: {task}\nSecurity context: {security_context}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]",
        "tokens": 38
    }
}

print("Agent-specific templates (avg 41 tokens vs current 580):")
for agent, template in agent_templates.items():
    print(f"  {agent}: {template['tokens']} tokens")
    print(f"    System: '{template['system']}'")
    print(f"    User: '{template['user_template']}'")

total_phase3_savings = 580 - 41  # Average template size
print(f"\n📊 Phase 3 Total Savings: {total_phase3_savings} tokens (93% reduction)")

print("\n📋 PHASE 4: FIX JSON ARTIFACT GENERATION")
print("-" * 60)

json_fixes = [
    {
        "issue": "Incomplete JSON files (code field empty)",
        "cause": "Code extraction only looks for ```blocks, but creates JSON metadata separately",
        "fix": "Modify _save_agent_artifacts() to properly populate JSON code field"
    },
    {
        "issue": "Redundant file creation",
        "cause": "Creates both .py files from ```blocks AND separate .json files",
        "fix": "Choose one format: either save as proper code files OR structured JSON, not both"
    },
    {
        "issue": "Incomplete artifact saving",
        "cause": "Regex pattern doesn't handle all code formats (inline code, partial blocks)",
        "fix": "Improve code extraction regex and add fallback for non-block code"
    }
]

for fix in json_fixes:
    print(f"\n🐛 Issue: {fix['issue']}")
    print(f"   🔍 Cause: {fix['cause']}")
    print(f"   🔧 Fix: {fix['fix']}")

print("\n📋 IMPLEMENTATION SUMMARY")
print("-" * 60)
total_savings = total_phase1_savings + total_phase2_savings + total_phase3_savings
original_tokens = 580
final_tokens = original_tokens - total_savings

print(f"📊 Current prompt size: {original_tokens} tokens")
print(f"📉 Total reduction: {total_savings} tokens") 
print(f"🎯 Final size: {final_tokens} tokens")
print(f"💰 Efficiency gain: {(total_savings/original_tokens)*100:.1f}% reduction")
print(f"💸 Cost savings: {((total_savings * 15) / 1000):.2f}k tokens per workflow")

print("\n🚀 EXPECTED IMPROVEMENTS:")
print("  ✅ 93% smaller prompts")
print("  ✅ Faster API responses") 
print("  ✅ Lower API costs")
print("  ✅ More focused agent behavior")
print("  ✅ Reduced token limits issues")
print("  ✅ Better agent specialization")

print("\n⚠️  RISKS & MITIGATIONS:")
print("  🔍 Risk: Less detailed instructions")
print("  🛡️  Mitigation: Agent-specific prompts ensure relevance")
print("  🔍 Risk: Agents might not know all options") 
print("  🛡️  Mitigation: System provides dynamic agent lookup")
print("  🔍 Risk: Decision quality might decrease")
print("  🛡️  Mitigation: Focus on specialties improves decision accuracy")
