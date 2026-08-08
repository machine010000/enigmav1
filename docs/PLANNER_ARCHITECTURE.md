# Planner Architecture

## Purpose

The Planner is responsible for converting a goal and context into an executable plan. It breaks work into tasks, detects dependencies, identifies parallel work, and produces an execution graph.

## Responsibilities

The Planner must:
- Receive an execution goal
- Analyze the goal into tasks
- Detect dependencies between tasks
- Detect parallel tasks
- Estimate execution order
- Produce an execution graph

## Input

- Goal
- Context
- Business constraints
- Available workers
- Available evidence

## Output

Each task should be represented in the following structure:

Task

↓

Dependencies

↓

Worker

↓

Expected Output

↓

Validation

## Task Structure

### Task
A single unit of work to accomplish.

### Dependencies
Other tasks that must finish before this one can start.

### Worker
The worker or capability responsible for executing the task.

### Expected Output
What the task should produce if it succeeds.

### Validation
How the output will be verified.

## Planning Rules

- Planner never makes business decisions.
- Planner does not execute workers.
- Planner produces structure, not final judgment.
- Planner must preserve task ordering and dependency clarity.

## Example Planning Output

Task: Verify product details
Dependencies: None
Worker: product_verification
Expected Output: Verified name, category, and attributes
Validation: Evidence-backed result and confidence threshold

Task: Research audience fit
Dependencies: Verify product details
Worker: research_service
Expected Output: Evidence-backed audience insights
Validation: Source quality and confidence
