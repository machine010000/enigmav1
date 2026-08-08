# Decision & Engagement Architecture

## Purpose

The Decision & Engagement Architecture introduces the critical Decision Layer between Marketplace Intelligence and Expert Domains. Every work request must pass through an explicit decision process before execution is allowed.

## Architecture

### Before (Direct Execution):

```
Marketplace
      ↓
Work Specification
      ↓
Capabilities
      ↓
Tasks
      ↓
Execution
```

### After (Decision Layer):

```
Marketplace
      ↓
Work Specification
      ↓
Decision Engine
      ↓
Decision Record
      ↓
Capability Selection
      ↓
Execution Planning
      ↓
Execution
```

## Key Principles

1. **Decision Gate**: Execution is architecturally gated by an explicit decision record
2. **No Direct Execution**: Work specifications cannot directly trigger execution
3. **Risk Assessment**: Every work request must undergo risk assessment
4. **Scope Validation**: Scope must be validated before execution
5. **Pricing & Negotiation**: Pricing and negotiation must be resolved
6. **Acceptance Gate**: Execution only allowed for ACCEPT or ACCEPT_WITH_CONDITIONS

## Decision Contract

### DecisionRecord

A `DecisionRecord` represents the decision made for a work request:

- **Decision ID**: Unique identifier
- **Work Specification ID**: Reference to work specification
- **Timestamp**: When the decision was made
- **Decision Status**: Status of the decision
- **Decision Confidence**: Confidence in the decision (0.0 to 1.0)
- **Decision Reasoning**: List of reasoning statements
- **Missing Knowledge**: Knowledge gaps identified
- **Missing Evidence**: Evidence gaps identified
- **Missing Capabilities**: Capability gaps identified
- **Required Research**: Research needed
- **Estimated Risk**: Risk score (0.0 to 1.0)
- **Estimated Profitability**: Profitability estimate (0.0 to 1.0)
- **Estimated Complexity**: Complexity estimate (0.0 to 1.0)
- **Estimated Delivery Time**: Estimated time to deliver
- **Estimated Success Probability**: Success probability (0.0 to 1.0)
- **Rejection Reasons**: Reasons for rejection
- **Acceptance Conditions**: Conditions for acceptance

### Decision Status

Possible decision statuses:

- **PENDING**: Decision is pending
- **NEED_RESEARCH**: Research is required
- **NEED_LEARNING**: Learning is required
- **NEED_NEGOTIATION**: Negotiation is required
- **NEED_CLARIFICATION**: Clarification is required
- **NEED_PORTFOLIO**: Portfolio evidence is required
- **REJECT**: Work request is rejected
- **ACCEPT**: Work request is accepted
- **ACCEPT_WITH_CONDITIONS**: Work request is accepted with conditions

### Acceptance Gate

Execution is allowed only for:
- **ACCEPT**: Direct acceptance
- **ACCEPT_WITH_CONDITIONS**: Acceptance with conditions

All other statuses block execution.

## Risk Assessment

### Risk Types

The framework supports the following risk types:

- **Technical Risk**: Technical implementation risks
- **Business Risk**: Business impact risks
- **Knowledge Risk**: Knowledge gap risks
- **Execution Risk**: Execution process risks
- **Financial Risk**: Financial impact risks
- **Legal Risk**: Legal compliance risks
- **Platform Risk**: Platform-specific risks
- **Client Risk**: Client-related risks

### Risk Assessment

A `RiskAssessment` includes:

- **Overall Risk Score**: 0 to 100
- **Risk Category**: low, medium, high, critical
- **Individual Risk Scores**: For each risk type
- **Risk Factors**: Individual risk factors with severity, impact, likelihood
- **Recommendations**: Mitigation recommendations

### Risk Scoring

Risk is calculated based on:
- **Severity**: Low, Medium, High, Critical
- **Impact**: Minimal, Moderate, Significant, Severe, Catastrophic
- **Likelihood**: Rare, Unlikely, Possible, Likely, Certain

## Scope Validation

### Scope Status

Scope validation determines:

- **CLEAR**: Scope is clear and complete
- **MISSING**: Scope is missing elements
- **AMBIGUOUS**: Scope is ambiguous
- **IMPOSSIBLE**: Scope is impossible to execute

### Scope Validation

A `ScopeValidation` includes:

- **Clarity Score**: 0.0 to 1.0
- **Completeness Score**: 0.0 to 1.0
- **Feasibility Score**: 0.0 to 1.0
- **Overall Score**: 0.0 to 1.0
- **Scope Issues**: List of identified issues
- **Missing Elements**: List of missing scope elements
- **Required Clarifications**: Clarifications needed
- **Recommendations**: Recommendations for improvement

### Scope Issues

Common scope issues:

- **Missing Requirements**: Requirements are not specified
- **Unclear Objectives**: Objectives are not clear
- **Conflicting Requirements**: Requirements conflict
- **Undefined Boundaries**: Boundaries are not defined
- **Unrealistic Timeline**: Timeline is unrealistic
- **Insufficient Budget**: Budget is insufficient
- **Technical Feasibility**: Technical feasibility issues
- **Resource Constraints**: Resource constraints
- **Compliance Issues**: Compliance issues

## Pricing

### Pricing Models

The framework supports the following pricing models:

- **HOURLY**: Hourly rate based pricing
- **FIXED**: Fixed price for the work
- **MILESTONE**: Milestone-based pricing
- **RETAINER**: Retainer-based pricing
- **CUSTOM**: Custom pricing models

### Pricing Model

A `PricingModel` includes:

- **Model Type**: Type of pricing model
- **Currency**: Currency for pricing
- **Base Rate**: Hourly rate (for hourly)
- **Total Amount**: Total amount (for fixed)
- **Estimated Hours**: Estimated hours (for hourly)
- **Payment Terms**: Payment terms
- **Billing Frequency**: Billing frequency
- **Milestones**: Milestone details (for milestone)
- **Retainer Hours**: Retainer hours (for retainer)
- **Custom Terms**: Custom terms

### Pricing Proposal

A `PricingProposal` represents a proposal for work:

- **Pricing Model**: The pricing model used
- **Status**: Draft, Pending, Approved, Rejected, Negotiated
- **Proposed By**: Who proposed the pricing
- **Approved By**: Who approved the pricing
- **Negotiation History**: History of negotiations
- **Validity Period**: How long the proposal is valid

## Negotiation

### Negotiation Items

The framework supports the following negotiation item types:

- **QUESTION**: Questions that need answers
- **SCOPE_CHANGE**: Changes to scope
- **BUDGET_CHANGE**: Changes to budget
- **TIMELINE_CHANGE**: Changes to timeline
- **DELIVERABLE_CHANGE**: Changes to deliverables
- **RISK_WARNING**: Risk warnings
- **TERM_CHANGE**: Changes to terms

### Negotiation Status

Negotiation items can have the following statuses:

- **PENDING**: Pending response
- **UNDER_REVIEW**: Under review
- **ACCEPTED**: Accepted
- **REJECTED**: Rejected
- **COUNTERED**: Countered
- **RESOLVED**: Resolved

### Negotiation Record

A `NegotiationRecord` tracks a negotiation process:

- **Negotiation Items**: List of items being negotiated
- **Status**: Active, Completed, Abandoned
- **Total/Resolved/Rejected/Pending Items**: Item counts
- **Negotiation Summary**: Summary of the negotiation

## Decision Engine

### DecisionInput

Input for decision-making includes:

- **Work Specification ID**: Reference to work specification
- **Available Knowledge**: Available knowledge areas
- **Available Evidence**: Available evidence
- **Available Capabilities**: Available capabilities
- **Knowledge Readiness**: Knowledge readiness score (0.0 to 1.0)
- **Capability Readiness**: Capability readiness score (0.0 to 1.0)
- **Evidence Coverage**: Evidence coverage score (0.0 to 1.0)
- **Complexity**: Complexity score (0.0 to 1.0)
- **Risk Score**: Risk score (0.0 to 1.0)
- **Client Quality**: Client quality score (0.0 to 1.0)
- **Portfolio Match**: Portfolio match score (0.0 to 1.0)

### Decision Making

The `DecisionEngine`:

1. Identifies missing knowledge, evidence, and capabilities
2. Determines decision status based on gaps and risk
3. Calculates decision confidence
4. Estimates risk, profitability, complexity, and success probability
5. Builds decision reasoning
6. Creates a decision record

### Success Probability

Success probability is calculated based on:

- **Knowledge Readiness**: How ready the knowledge is
- **Capability Readiness**: How ready the capabilities are
- **Evidence Coverage**: How complete the evidence is
- **Complexity**: How complex the work is
- **Risk**: How risky the work is
- **Client Quality**: How good the client is
- **Portfolio Match**: How well it matches the portfolio

## Registry

The `EngagementRegistry` provides:

- **Decision Records**: Registration and retrieval
- **Risk Assessments**: Registration and retrieval
- **Scope Validations**: Registration and retrieval
- **Pricing Models**: Registration and retrieval
- **Pricing Proposals**: Registration and retrieval
- **Negotiation Records**: Registration and retrieval
- **Negotiation Templates**: Registration and retrieval
- **Decision Engine**: Access to decision-making

## Extension Guide

To extend the engagement framework:

1. **Create Decision Input**: Prepare `DecisionInput` with all relevant information
2. **Make Decision**: Use `DecisionEngine.make_decision()` to create a decision
3. **Assess Risk**: Use `RiskAssessmentFramework` to assess risks
4. **Validate Scope**: Use `ScopeValidationFramework` to validate scope
5. **Create Pricing**: Use `PricingFramework` to create pricing models
6. **Negotiate**: Use `NegotiationFramework` to manage negotiations
7. **Register Components**: Register all components with `EngagementRegistry`
8. **Check Acceptance**: Use `can_proceed()` to check if execution can proceed

## Testing

Tests are located in `tests/engagement/` and cover:

- Decision contract validation
- Risk assessment validation
- Scope validation
- Pricing model validation
- Negotiation validation
- Decision engine behavior
- Registry integration

Run tests with:
```bash
pytest tests/engagement/
```

## Integration

The Engagement Framework integrates with:

- **Work Specifications**: Consumes work specifications from the Work Framework
- **Expert Domains**: Provides decisions to Expert Domains
- **Marketplace Intelligence**: Receives work requests from marketplaces
- **Risk Framework**: Uses risk assessment for decision-making
- **Pricing Framework**: Uses pricing for proposals
- **Negotiation Framework**: Uses negotiation for conflict resolution

## Backward Compatibility

The framework maintains backward compatibility:
- Does not modify existing Expert Domain Framework
- Does not modify existing Work Framework
- Does not modify existing Capability Framework
- Does not modify existing Task Framework
- Integrates through decision records and registry

## Future Enhancements

Future versions may include:
- Advanced decision algorithms
- Machine learning for risk assessment
- Automated negotiation agents
- Dynamic pricing models
- Real-time scope tracking
- Multi-decision workflows
- Decision history and learning
