# Brain Responsibility Matrix

## Purpose

This document defines the responsibility boundaries between the main ENIGMA components so that no module overlaps another in a way that creates ambiguity or duplicated decision-making.

## Responsibility Matrix

| Component | Primary Responsibilities | Cannot Do |
|---|---|---|
| Master Brain | Understand user goals, frame the problem, identify scenarios, generate journeys, recall relevant experience, read academy guidance, read knowledge, and trigger planning | Execute workers directly |
| Planner | Break goals into tasks, identify dependencies, structure execution flow, and produce an execution plan | Decide business strategy |
| Decision Engine | Evaluate hypotheses, maintain decision lifecycle, preserve decision versions, and update decisions with evidence and outcomes | Execute workers |
| Execution Engine | Execute plans, dispatch work, and track runtime progress | Think or decide strategy |
| Worker | Execute one capability or domain action and return structured results | Make strategic decisions |
| Academy | Store permanent domain knowledge, reasoning principles, and reusable frameworks | Execute work |
| Knowledge Graph | Store structured facts and relationships between entities | Infer business meaning on its own |
| Memory Engine | Store experiences, episodes, strategies, and patterns for reuse | Store facts as primary knowledge |
| Research Service | Collect evidence, gather external context, and provide supporting information | Decide the final business action |

## Boundary Rules

1. The Master Brain is the reasoning and orchestration layer.
2. The Planner is the structure layer.
3. The Decision Engine is the decision lifecycle layer.
4. The Execution Engine is the runtime dispatch layer.
5. Workers are capability executors only.
6. The Academy is a knowledge and guidance layer.
7. The Knowledge Graph is a factual layer.
8. The Memory Engine is an experiential layer.
9. Research is an evidence layer.

## Conflict Prevention

No component should both execute and decide strategy in the same step. Each component has a single responsibility axis:

- Reasoning → Master Brain
- Structuring → Planner
- Decision lifecycle → Decision Engine
- Execution → Execution Engine / Workers
- Knowledge → Academy / Knowledge Graph
- Experience → Memory Engine
- Evidence → Research Service
