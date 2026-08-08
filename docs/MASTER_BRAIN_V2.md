# Master Brain V2

## Purpose

The Master Brain V2 is the central intelligence layer of ENIGMA. It is responsible for understanding a user goal, framing the problem, generating hypotheses, and producing an execution plan that can be handed to the Planner.

> The legacy Master Brain implementation has been deprecated. Master Brain V2 is now the only supported runtime implementation.

## Core Thinking Flow

User Goal

↓

Understand User

↓

Identify Business Type

↓

Generate User Journey

↓

Generate Product Journey

↓

Recall Memory

↓

Read Academy

↓

Read Knowledge Graph

↓

Detect Missing Information

↓

Generate Hypotheses

↓

Prioritize Hypotheses

↓

Generate Execution Plan

↓

Send Plan to Planner

## Step Definitions

### 1. Understand User
Input:
- User message
- User profile
- Existing context

Output:
- User intent
- User constraints
- User needs

Success Criteria:
- The user goal is clearly framed.
- The target outcome is understandable.

### 2. Identify Business Type
Input:
- User goal
- Domain context

Output:
- Business category
- Market context
- Strategic lens

Success Criteria:
- The business context is properly classified.

### 3. Generate User Journey
Input:
- User intent
- Business context

Output:
- User journey stages
- Likely pain points
- Expectations

Success Criteria:
- The journey is coherent and actionable.

### 4. Generate Product Journey
Input:
- User journey
- Product context

Output:
- Product journey stages
- Product opportunities
- Product risks

Success Criteria:
- The product path is meaningful and aligned to the user's needs.

### 5. Recall Memory
Input:
- Goal
- Product context
- Prior execution history

Output:
- Similar episodes
- Reusable strategies
- Matching patterns

Success Criteria:
- Previous experience is surfaced before new reasoning begins.

### 6. Read Academy
Input:
- Goal
- Business context
- Recalled experience

Output:
- Academy guidance
- Domain constraints
- Strategic principles

Success Criteria:
- The guidance is relevant and reusable.

### 7. Read Knowledge Graph
Input:
- Goal
- Known entities
- Product context

Output:
- Relevant facts
- Linked entities
- Relationship context

Success Criteria:
- The system uses stored facts instead of starting from zero.

### 8. Detect Missing Information
Input:
- Current understanding
- Available memory
- Available facts

Output:
- Missing information list
- Uncertainty areas

Success Criteria:
- The system identifies what remains unknown.

### 9. Generate Hypotheses
Input:
- Missing information
- Context
- Evidence

Output:
- Candidate hypotheses
- Reasoning paths

Success Criteria:
- Hypotheses are testable and explainable.

### 10. Prioritize Hypotheses
Input:
- Hypotheses
- Evidence quality
- Constraints

Output:
- Ranked hypotheses
- Preferred path

Success Criteria:
- The selected path is the most likely and best justified.

### 11. Generate Execution Plan
Input:
- Ranked hypotheses
- Constraints
- Available workers

Output:
- Execution plan
- Task list
- Expected outputs

Success Criteria:
- The plan can be handed to the Planner without ambiguity.

### 12. Send Plan to Planner
Input:
- Execution plan

Output:
- Planner-ready execution graph

Success Criteria:
- The plan is structured for execution and validation.

## Architectural Boundaries

- The Master Brain never executes workers.
- The Master Brain does not perform raw research itself.
- The Master Brain produces reasoning, plans, and decisions.
- The Master Brain is the single orchestrator of understanding.
