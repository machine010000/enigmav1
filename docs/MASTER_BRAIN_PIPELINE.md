# Master Brain Pipeline

## Purpose

This document defines the final operating pipeline for the Master Brain so that it behaves consistently and avoids overlapping responsibilities with other components.

## Final Pipeline

Receive Goal

↓

Understand User

↓

Identify Scenario

↓

Generate Journey

↓

Recall Memory

↓

Read Academy

↓

Read Knowledge

↓

Need Research?

↓

Yes

↓

Research

↓

Need More?

↓

No

↓

Planner

↓

Execution

## Pipeline Stages

### 1. Receive Goal
- Input: user request or system trigger
- Output: initial goal object

### 2. Understand User
- Input: goal, context, profile
- Output: clarified intent and constraints

### 3. Identify Scenario
- Input: goal and context
- Output: scenario classification

### 4. Generate Journey
- Input: scenario and intent
- Output: user journey and product journey

### 5. Recall Memory
- Input: goal and prior experience
- Output: similar episodes and applicable strategies

### 6. Read Academy
- Input: goal, context, scenario
- Output: reasoning principles and domain guidance

### 7. Read Knowledge
- Input: entities and current context
- Output: structured facts and links

### 8. Need Research?
- Input: current understanding and gaps
- Output: decision to gather more evidence or proceed

### 9. Research
- Input: unresolved questions
- Output: evidence-backed findings

### 10. Need More?
- Input: evidence gathered so far
- Output: continue research or move forward

### 11. Planner
- Input: chosen hypothesis and context
- Output: execution plan

### 12. Execution
- Input: plan
- Output: worker execution and results

## Pipeline Rule

The Master Brain is responsible for understanding and planning direction, not for directly executing workers. Once the plan is prepared, the responsibility moves to execution and decision layers.
