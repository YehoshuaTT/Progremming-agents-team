# PROMPT OPTIMIZATION IMPLEMENTATION PLAN
# =====================================

## EXECUTIVE SUMMARY
**Current State**: 580 token prompts causing inefficiency and high costs
**Target State**: ~40 token agent-specific prompts with better specialization
**Expected Savings**: 93% token reduction, improved agent focus

---

## PHASE 1: IMMEDIATE REMOVALS (Safe, No Effectiveness Impact)

### 1.1 Remove "ALL AVAILABLE AGENTS IN SYSTEM" Section
- **Tokens Saved**: 75
- **Rationale**: Agent already knows typical next agents from `agent_capabilities` dict
- **Implementation**: Delete section, use dynamic lookup in code
- **Risk**: None - information available programmatically

### 1.2 Remove Examples Section  
- **Tokens Saved**: 200
- **Rationale**: Examples are redundant with decision factors and agent specialties
- **Implementation**: Keep only decision tag format, remove all 7 examples
- **Risk**: None - agents can infer patterns from context

### 1.3 Simplify Quality Thresholds
- **Tokens Saved**: 100  
- **Rationale**: Over-prescriptive mappings reduce agent autonomy
- **Implementation**: Replace with "Use your expertise to determine quality level"
- **Risk**: None - specialists should use professional judgment

### 1.4 Remove Unimplemented Workflow Controls
- **Tokens Saved**: 50
- **Rationale**: PARALLEL and BRANCH options not implemented in code
- **Implementation**: Keep only COMPLETE, NEXT_AGENT, HUMAN_REVIEW, RETRY
- **Risk**: None - removing unused features

**Phase 1 Total: 425 tokens saved (73% reduction)**

---

## PHASE 2: STRUCTURAL IMPROVEMENTS

### 2.1 System Message Migration
- **Current**: 150 tokens in user prompt for role definition
- **New**: 0 tokens (moved to system message)
- **Benefit**: System messages don't count toward billable input tokens
- **Implementation**: Move agent role/specialty to system message

### 2.2 Context Filtering by Agent Type
- **Current**: 75 tokens of generic context
- **New**: 25 tokens of relevant context only
- **Benefit**: Security_Specialist gets only security context, Tester gets only testing context
- **Implementation**: Create context filters per agent type

### 2.3 Compressed Decision Format  
- **Current**: 125 tokens of verbose decision instructions
- **New**: 30 tokens single-line format
- **Benefit**: Clear, concise decision format
- **Implementation**: "Decision: [TAG] - Reason: brief explanation"

**Phase 2 Total: 295 tokens saved**

---

## PHASE 3: AGENT-SPECIFIC OPTIMIZATION

### 3.1 Agent-Specific Templates
Replace generic 580-token prompt with specialized templates:

#### Coder (45 tokens)
```
System: "You are a Coder. Write clean, functional code with tests."
User: "Task: {task}\nContext: {code_context}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]"
```

#### Tester (40 tokens)  
```
System: "You are a Tester. Create comprehensive test plans and automated tests."
User: "Task: {task}\nCode: {code_artifacts}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]"
```

#### QA_Guardian (42 tokens)
```
System: "You are QA Guardian. Final quality check before deployment approval." 
User: "Task: {task}\nArtifacts: {all_artifacts}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]"
```

#### Security_Specialist (38 tokens)
```
System: "You are Security Specialist. Identify vulnerabilities and security requirements."
User: "Task: {task}\nSecurity context: {security_context}\nDecide: [COMPLETE] or [NEXT_AGENT: AgentName]"
```

**Phase 3 Total: 539 tokens saved (93% reduction to ~40 tokens average)**

---

## PHASE 4: FIX JSON ARTIFACT GENERATION

### 4.1 Incomplete JSON Files Issue
- **Problem**: JSON code field is empty because code extraction only finds ```blocks
- **Root Cause**: Code saved separately from JSON metadata
- **Solution**: Modify `_save_agent_artifacts()` to populate JSON code field properly

### 4.2 Redundant File Creation
- **Problem**: Creates both .py files AND .json files for same content
- **Root Cause**: Two separate save mechanisms
- **Solution**: Choose single format - either structured JSON OR language-specific files

### 4.3 Improved Code Extraction
- **Problem**: Regex only handles ```blocks, misses inline code
- **Root Cause**: Limited regex pattern `r'```(\w+)?\n(.*?)```'`
- **Solution**: Add fallback patterns for non-block code formats

### 4.4 Implementation Details
```python
# Fixed artifact saving function
def _save_agent_artifacts_fixed(self, agent_response: str, workflow_id: str):
    # 1. Extract all code (blocks and inline)
    # 2. Choose format: JSON with embedded code OR separate files
    # 3. Ensure no empty/incomplete files
    # 4. Log all saved artifacts properly
```

---

## IMPLEMENTATION SUMMARY

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Prompt Size** | 580 tokens | ~40 tokens | 93% reduction |
| **API Cost per Workflow** | 8,700 tokens | 600 tokens | 93% reduction |
| **Agent Focus** | Generic | Specialized | Better decisions |
| **Context Relevance** | 30% | 90% | More efficient |
| **Loop Prevention** | Poor | Good | Clearer exit conditions |

## EXPECTED IMPROVEMENTS

✅ **Performance**: 93% smaller prompts = faster API responses  
✅ **Cost**: 93% reduction in token usage = major cost savings  
✅ **Quality**: Agent-specific prompts = better specialization  
✅ **Reliability**: Clearer decision criteria = fewer loops  
✅ **Scalability**: Lower token limits = support for larger workflows  
✅ **Maintainability**: Simpler prompts = easier to debug and improve  

## RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| Less detailed instructions | Medium | Agent-specific prompts ensure relevance |
| Agents unaware of all options | Low | Dynamic agent lookup provides complete info |
| Decision quality decrease | Medium | Focus on specialties improves accuracy |
| Implementation complexity | Low | Phased rollout with testing |

## ROLLOUT PLAN

1. **Week 1**: Implement Phase 1 (safe removals)
2. **Week 2**: Implement Phase 2 (structural improvements)  
3. **Week 3**: Implement Phase 3 (agent-specific templates)
4. **Week 4**: Implement Phase 4 (JSON fixes) + testing
5. **Week 5**: A/B testing and performance validation
6. **Week 6**: Full deployment and monitoring

## SUCCESS METRICS

- [ ] Prompt size reduced to <50 tokens average
- [ ] API costs reduced by >85%
- [ ] Agent loop frequency reduced by >70%
- [ ] Decision quality maintained or improved
- [ ] JSON artifact completeness = 100%
- [ ] Workflow completion rate improved by >20%
