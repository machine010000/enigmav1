# Engineering Principles

## Principle 1
No Fake Data

- No mocked products
- No fake audiences
- No fake keywords
- No fake trends
- No fake competitors

The system must always work against real information.

---

## Principle 2
Every feature must be testable immediately.

No feature is considered complete unless it can be executed from the Frontend.

---

## Principle 3
Every Worker is independently executable.

Every Worker must expose:

Input

Output

Execution Time

Status

Error

Confidence Score

---

## Principle 4

The Brain never guesses.

If confidence is below threshold:

Request more information

or

Run another Worker

or

Ask user

Never hallucinate.

---

## Principle 5

All research must be reproducible.

Every answer must include:

Source

Timestamp

Worker

Confidence

---

## Principle 6

Everything is observable.

Every execution appears inside the Developer Dashboard.

---

## Principle 7

Knowledge First, LLM Second.

The workflow must prioritize existing knowledge before asking the model.

Workflow:

Worker

↓

Knowledge Service

↓

Is the information already known?

↓

Yes

↓

Use it

No

↓

Research

↓

LLM

↓

Verify

↓

Evidence

↓

Knowledge Graph

↓

Return result

The LLM is the last resort, not the first choice.

---

## Principle 8

Experience Before Intelligence.

Master Brain

↓

Memory Engine

↓

Knowledge Service

↓

Research Service

↓

LLM Gateway

The system must always reuse previous experience before generating new intelligence.
