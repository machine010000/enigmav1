# Data Flow

## Overview

This document captures the end-to-end data movement across ENIGMA so that every handoff is explicit, typed, and traceable.

## Core Flow

User

↓

Master Brain

↓

Memory

↓

Academy

↓

Knowledge Graph

↓

Research Service

↓

Planner

↓

Execution Engine

↓

Workers

↓

Evidence

↓

Memory Update

↓

Dashboard

## Flow Definitions

### 1. User → Master Brain
- Input: user goal, context, constraints, preferences
- Output: interpreted intent, scenario, journey, and initial hypothesis
- Format: structured request context

### 2. Master Brain → Memory
- Input: goal and context
- Output: prior episodes, relevant strategies, similar patterns
- Format: ranked memory records

### 3. Master Brain → Academy
- Input: business context, goal, scenario
- Output: domain guidance, reasoning principles, reusable frameworks
- Format: academy module response

### 4. Master Brain → Knowledge Graph
- Input: entities, product context, current goal
- Output: facts, related entities, relationship context
- Format: graph query result

### 5. Master Brain → Research Service
- Input: missing information, uncertainty areas, research questions
- Output: evidence, references, supporting facts
- Format: research report

### 6. Master Brain → Planner
- Input: selected hypothesis, context, evidence, constraints
- Output: execution plan with tasks and dependencies
- Format: plan object / execution graph

### 7. Planner → Execution Engine
- Input: execution plan
- Output: ordered tasks ready for runtime dispatch
- Format: task list with dependency metadata

### 8. Execution Engine → Workers
- Input: task payload, worker selection, runtime context
- Output: capability execution result
- Format: worker result object

### 9. Workers → Evidence
- Input: task execution output
- Output: evidence, structured observations, status, and confidence
- Format: evidence payload

### 10. Evidence → Decision Engine
- Input: evidence and execution result
- Output: updated decision status and decision history entry
- Format: decision update event

### 11. Evidence → Memory Update
- Input: completed execution, results, outcomes
- Output: episode, strategy, and pattern updates
- Format: memory event

### 12. Evidence → Knowledge Graph
- Input: verified facts from execution
- Output: new graph nodes and relationships
- Format: knowledge write payload

### 13. Decision / Evidence → Dashboard
- Input: decision state, execution events, memory metrics
- Output: user-visible observability and audit trail
- Format: event stream / dashboard state

## Data Flow Principle

Every major handoff must preserve:
- source context
- evidence trail
- timestamp
- confidence level
- status
- linked decision id
