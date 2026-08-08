# Decision Lifecycle

## Purpose

This document defines the full lifecycle of a decision in ENIGMA, from goal intake to final evidence-backed outcome.

## Lifecycle Flow

Goal

↓

Hypothesis

↓

Evidence Needed

↓

Planner

↓

Execution

↓

Evidence Collected

↓

Decision Updated

↓

Episode Stored

↓

Knowledge Updated

## Lifecycle Stages

### 1. Goal
The decision begins with a user or system goal.

- Input: business request, product objective, or strategic need
- Output: decision intent

### 2. Hypothesis
The system formulates one or more candidate hypotheses.

- Input: context, memory, academy guidance, knowledge
- Output: proposed hypothesis set

### 3. Evidence Needed
The system determines what evidence is required to validate the hypothesis.

- Input: hypothesis and uncertainty areas
- Output: evidence requirements

### 4. Planner
The planner transforms the decision into an execution structure.

- Input: hypothesis and evidence requirements
- Output: actionable task plan

### 5. Execution
The execution layer runs the relevant tasks through workers.

- Input: task plan
- Output: execution results and raw observations

### 6. Evidence Collected
The system gathers and normalizes evidence from execution.

- Input: worker output
- Output: structured evidence payload

### 7. Decision Updated
The decision record is updated with evidence, confidence, and outcome.

- Input: evidence and runtime results
- Output: updated decision version

### 8. Episode Stored
The completed decision and execution experience are stored in memory.

- Input: decision outcome and execution context
- Output: stored episode

### 9. Knowledge Updated
Verified facts from the decision are written into the knowledge graph.

- Input: validated evidence
- Output: new or updated knowledge facts

## Lifecycle Rules

- Every decision must have a traceable history.
- Every decision must be grounded in evidence.
- Every decision must produce observable outcomes.
- Every decision should create memory and knowledge updates where appropriate.
