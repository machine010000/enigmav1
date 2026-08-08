# ENIGMA Blueprint

## Overview

ENIGMA is a learning-first business intelligence platform. Its purpose is not to answer every request with a fresh language model call, but to accumulate experience, structure knowledge, and produce explainable decisions over time.

## Core Flow

Enigma

↓

Master Brain V2

↓

Intelligence Engine

↓

Reasoning Context

↓

Decision Engine

↓

Planner

↓

Execution Engine

↓

Workers

↓

Dashboard

↓

Evolution Brain

## Module Responsibilities

### Master Brain V2
Responsible for understanding goals, user context, business type, journeys, hypotheses, and execution orchestration. It is the system's central reasoning layer and the only active Master Brain implementation in the current architecture.

Inputs:
- User goal
- User profile
- Product context
- Previous decisions
- Intelligence Engine context

Outputs:
- Goals understood
- Hypotheses
- Execution plan
- Decision proposals

> Note: Legacy Master Brain has been deprecated and removed from active runtime flows. All new code must use `app.ai.master_brain`.

### Academy
Responsible for permanent domain knowledge and reasoning frameworks. It provides structured knowledge and principles without executing work.

Inputs:
- Business domain questions
- Repeated patterns
- Learned principles
- Expert guidance

Outputs:
- Domain guidance
- Validation rules
- Strategic frameworks

### Memory
Responsible for storing experience from previous executions. It captures what worked, what failed, and what patterns repeated.

Inputs:
- Episodes
- Strategies
- Patterns

Outputs:
- Similar episodes
- Best strategies
- Pattern matches

### Knowledge Graph
Responsible for storing structured factual relationships between entities such as products, audiences, platforms, features, problems, and benefits.

Inputs:
- Nodes
- Relationships
- Evidence-backed facts

Outputs:
- Fact graph
- Neighbor relationships
- Product-centric views

### Research
Responsible for gathering external evidence. It provides supporting information but does not make business decisions.

Inputs:
- Research queries
- Context
- Constraints

Outputs:
- Research reports
- Evidence items
- Ranked sources

### Planner
Responsible for turning a decision into a concrete execution plan. It breaks work into tasks, detects dependencies, and produces an execution graph.

Inputs:
- Goal
- Context
- Hypotheses

Outputs:
- Tasks
- Dependencies
- Execution graph

### Decision Engine
Responsible for turning a plan into a concrete decision lifecycle. It stores decisions, versions, reasoning, and execution outcomes.

Inputs:
- Goal
- Context
- Selected capability
- Plan

Outputs:
- Decision records
- Decision versions
- Execution outcome

### Execution Engine
Responsible for dispatching work to the appropriate workers and tracking execution state.

Inputs:
- Execution plan
- Worker definitions
- Runtime context

Outputs:
- Worker results
- Execution history
- Status updates

### Workers
Responsible for domain-specific execution. They perform a task, produce evidence, and return structured results.

Inputs:
- Execution context
- Product or task payload

Outputs:
- WorkerResult
- Evidence
- Status

### Dashboard
Responsible for making the system observable to developers and operators.

Inputs:
- Decisions
- Execution events
- Memory metrics
- Knowledge activity

Outputs:
- Live console
- Metrics panels
- Timeline views

### Evolution Brain
Responsible for long-term improvement. It observes outcomes, patterns, and changes over time and recommends future improvements.

Inputs:
- Historical decisions
- Execution outcomes
- Trends and feedback

Outputs:
- Improvement recommendations
- Learning priorities
- Evolution signals

## Design Principles

- The Master Brain is the single orchestrator.
- Responsibility boundaries are explicit and non-overlapping.
- Decisions must be explainable.
- Memory captures experience.
- Knowledge Graph captures facts.
- Research supplies evidence.
- Workers do not decide strategy.
