---
name: agent-continuous-improvement
description: Automatically and continuously improve an agent through iterative evaluation, analysis, and optimization cycles. Use this skill when the user wants to "持续改进agent", "自动优化agent", "进入优化循环", or requests continuous/automatic agent improvement. This skill runs a fully automated loop that evaluates performance, identifies improvement opportunities, implements changes, and repeats until no further improvements are possible.
---

# Agent Continuous Improvement Loop

This skill implements a fully automated continuous improvement cycle for agents. It repeatedly evaluates the agent, analyzes results, implements optimizations, and merges successful improvements until no further gains are possible.

## Overview

The improvement loop follows this workflow:

1. **Evaluate** - Run agent-performance-evaluation to measure current performance
2. **Analyze** - Identify the most valuable improvement opportunities
3. **Decide** - Determine if meaningful improvements are possible
4. **Branch** - Create optimization branch from feat/harness-loop
5. **Plan** - Design the optimization approach
6. **Implement** - Execute changes and verify tests pass
7. **Merge** - Integrate successful improvements back to feat/harness-loop
8. **Loop** - Repeat until 3 consecutive cycles find no improvements

## When to Use This Skill

Trigger this skill when the user requests:
- "持续改进agent" (continuously improve agent)
- "自动优化agent" (automatically optimize agent)
- "进入优化循环" (enter optimization loop)
- Any request for automated, iterative agent improvement

## Prerequisites

Before starting the loop, verify:
- The `agent-performance-evaluation` skill is available
- You're in the agent's repository
- The `feat/harness-loop` branch exists
- Test suite is runnable (e.g., `uv run pytest`)
- Evaluation test set exists (e.g., `test_queries.json`)

## Loop State Tracking

Maintain state across iterations using a JSON file at `.dev_process/optimization_state.json`:

```json
{
  "iteration": 1,
  "consecutive_no_improvement": 0,
  "baseline_score": null,
  "current_score": null,
  "history": [
    {
      "iteration": 1,
      "branch": "harness-optimize/2026-05-24-001/improve-accuracy",
      "improvement_target": "Improve accuracy scores",
      "baseline_score": 7.2,
      "new_score": 7.8,
      "improved": true,
      "merged": true
    }
  ]
}
```

If this file doesn't exist, create it with iteration 1 and empty history.

## Workflow Steps

### Step 1: Evaluate Current Performance

Use the `agent-performance-evaluation` skill to measure current agent performance:

```bash
# The skill will run the evaluation and produce results
```

Extract key metrics from the evaluation results:
- Overall score
- Individual dimension scores (accuracy, relevance, coherence, etc.)
- Performance bottlenecks
- Common failure patterns

Save the evaluation results to `.dev_process/eval_iteration_N.json` for tracking.

### Step 2: Analyze and Identify Improvements

Based on the evaluation results, analyze:

**What to look for:**
- Lowest-scoring dimensions (biggest improvement opportunity)
- Recurring error patterns across test cases
- Missing capabilities or knowledge gaps
- Performance bottlenecks (speed, token usage)
- Logic flaws in reasoning or tool usage

**Prioritization criteria:**
- Impact: How much could this improve overall performance?
- Feasibility: Can this be implemented reliably?
- Risk: How likely to introduce regressions?

**Decision logic:**
- If you identify clear, actionable improvements → proceed to Step 3
- If no obvious improvements exist → increment `consecutive_no_improvement` counter
- If `consecutive_no_improvement >= 3` → exit loop and report final results

### Step 3: Create Optimization Branch

Generate branch name with format: `harness-optimize/YYYY-MM-DD-NNN/description`

- Date: Current date (e.g., 2026-05-24)
- NNN: Zero-padded iteration number (001, 002, etc.)
- description: Short kebab-case description of the improvement (e.g., improve-accuracy, fix-citation-logic)

```bash
# Ensure we're on feat/harness-loop and it's up to date
git checkout feat/harness-loop
git pull origin feat/harness-loop

# Create and checkout new optimization branch
git checkout -b harness-optimize/2026-05-24-001/improve-accuracy
```

### Step 4: Plan the Optimization

Create a detailed optimization plan in `.dev_docs/plan/optimization_iteration_N.md`:

**Plan structure:**
```markdown
# Optimization Iteration N

## Target Issue
[What specific problem are we solving?]

## Root Cause Analysis
[Why is this happening?]

## Proposed Solution
[What changes will we make?]

## Implementation Steps
1. [Specific file and change]
2. [Another change]
3. [Test verification]

## Expected Impact
- Baseline score: X.X
- Target score: X.X
- Risk assessment: [Low/Medium/High]

## Rollback Plan
[How to revert if this fails]
```

### Step 5: Implement the Optimization

Execute the planned changes:

1. **Make code changes** according to the plan
2. **Run tests** to ensure nothing breaks:
   ```bash
   uv run pytest
   ```
3. **If tests fail**: Fix issues or abort this iteration
4. **Commit changes**:
   ```bash
   git add <modified-files>
   git commit -m "optimize: [description of improvement]
   
   - [Specific change 1]
   - [Specific change 2]
   
   Target: Improve [dimension] from X.X to Y.Y"
   ```

**Critical requirement**: Tests MUST pass before proceeding. If tests fail after multiple fix attempts, abort this iteration and mark it as unsuccessful.

### Step 6: Evaluate the Improvement

Run agent-performance-evaluation again on the optimized version:

```bash
# Use the same test set as baseline evaluation
```

Compare results:
- Did the overall score improve?
- Did the target dimension improve?
- Did any other dimensions regress?

**Success criteria:**
- Overall score increased OR target dimension significantly improved without major regressions
- All tests still pass
- No critical functionality broken

### Step 7: Merge or Discard

**If improvement was successful:**

```bash
# Switch to feat/harness-loop
git checkout feat/harness-loop

# Merge the optimization branch
git merge --no-ff harness-optimize/2026-05-24-001/improve-accuracy -m "Merge optimization: [description]

Improved [dimension] from X.X to Y.Y"

# Delete the optimization branch
git branch -d harness-optimize/2026-05-24-001/improve-accuracy
```

Update state:
- Reset `consecutive_no_improvement` to 0
- Update `current_score` to new score
- Add successful iteration to history
- Set `merged: true`

**If improvement failed:**

```bash
# Switch back to feat/harness-loop
git checkout feat/harness-loop

# Delete the failed optimization branch
git branch -D harness-optimize/2026-05-24-001/improve-accuracy
```

Update state:
- Increment `consecutive_no_improvement`
- Add failed iteration to history
- Set `merged: false`

### Step 8: Loop Control

After each iteration:

1. Update `.dev_process/optimization_state.json`
2. Increment iteration counter
3. Check stopping condition:
   - If `consecutive_no_improvement >= 3` → Stop and report final results
   - Otherwise → Return to Step 1

## Final Report

When the loop terminates, generate a summary report:

```markdown
# Agent Optimization Complete

## Final Performance Metrics
- Starting score: X.X
- Final score: Y.Y
- Total improvement: +Z.Z points

## Optimization History
- Total iterations: N
- Successful improvements: M
- Failed attempts: K

## Detailed Results
[Table showing each iteration's results]

## Key Improvements Made
1. [Description of improvement 1] - Impact: +X.X points
2. [Description of improvement 2] - Impact: +Y.Y points

## Current Limitations
[Analysis of why further improvement wasn't possible]

## Recommendations
[Suggestions for future work, if any]
```

Save this report to `.dev_docs/summary/optimization_complete_YYYY-MM-DD.md`.

## Important Notes

### Fully Automated Operation

This skill runs completely automatically. Do NOT ask for user confirmation at each step. The user has requested autonomous operation.

### Test Requirements

Always run the full test suite after making changes. If tests fail:
1. Attempt to fix the test failures
2. If fixes don't work after 2-3 attempts, abort the iteration
3. Mark the iteration as failed and move on

### Same Test Set

Use the same evaluation test set throughout all iterations. This ensures fair comparison across iterations. Do not modify `test_queries.json` during the optimization loop.

### Branch Hygiene

- Always branch from `feat/harness-loop`, never from other optimization branches
- Delete branches after merging or discarding
- Use descriptive branch names that indicate what's being optimized

### Handling Edge Cases

**If feat/harness-loop doesn't exist:**
- Ask user which branch to use as base
- Update all references in this workflow

**If evaluation skill fails:**
- Log the error
- Count as a failed iteration
- Continue to next iteration (don't exit immediately)

**If git conflicts occur during merge:**
- This shouldn't happen if we're always branching from feat/harness-loop
- If it does, abort the merge, report the issue, and ask user for guidance

### Performance Considerations

Each iteration involves:
- Full evaluation run (can be slow/expensive)
- Code analysis and modification
- Test suite execution
- Another evaluation run

Expect each iteration to take significant time. This is normal for thorough optimization.

## Example Execution

```
Iteration 1:
- Evaluate: Overall score 7.2, accuracy 6.5 (lowest)
- Analyze: Citation extraction logic is incomplete
- Branch: harness-optimize/2026-05-24-001/improve-citations
- Implement: Enhanced citation extraction in utils.py
- Test: All tests pass
- Evaluate: Overall score 7.8, accuracy 7.5
- Result: SUCCESS (+0.6 points) → Merge

Iteration 2:
- Evaluate: Overall score 7.8, coherence 7.0 (lowest)
- Analyze: Storyline generation lacks structure
- Branch: harness-optimize/2026-05-24-002/improve-storyline
- Implement: Added storyline templates
- Test: All tests pass
- Evaluate: Overall score 8.1, coherence 7.8
- Result: SUCCESS (+0.3 points) → Merge

Iteration 3:
- Evaluate: Overall score 8.1
- Analyze: No obvious improvement points, scores are balanced
- Result: NO IMPROVEMENT (count: 1)

Iteration 4:
- Evaluate: Overall score 8.1
- Analyze: Attempted relevance optimization
- Branch: harness-optimize/2026-05-24-003/improve-relevance
- Implement: Modified search query logic
- Test: All tests pass
- Evaluate: Overall score 8.0 (regression)
- Result: FAILED → Discard branch (count: 2)

Iteration 5:
- Evaluate: Overall score 8.1
- Analyze: No clear improvements without major refactoring
- Result: NO IMPROVEMENT (count: 3)

STOP: 3 consecutive iterations without improvement
Final score: 8.1 (improved from 7.2)
```

## Troubleshooting

**Loop runs forever:**
- Check that `consecutive_no_improvement` counter is being incremented correctly
- Verify the "no improvement" detection logic is working

**Tests keep failing:**
- Review what changes are being made
- Consider if the optimization approach is too aggressive
- May need to adjust the improvement strategy

**Scores fluctuate randomly:**
- Evaluation may have high variance
- Consider running evaluation multiple times and averaging
- May indicate the test set is too small or not representative

**Merge conflicts:**
- Ensure always branching from latest feat/harness-loop
- Check that no other process is modifying the branch

## Success Criteria

The skill has succeeded when:
1. Agent performance has measurably improved from baseline
2. All tests pass on the final merged code
3. Loop terminated naturally (3 consecutive no-improvements)
4. Final report clearly documents the improvements made
