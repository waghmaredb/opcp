# Soven integration boundary

Soven is a commercial product built on OPCP. OPCP remains the open protocol and standard for institution-owned processes, context and authority with interchangeable capability suppliers.

## Boundary

### OPCP owns

- capability archetypes and contracts;
- standard envelopes, routes and eligibility semantics;
- context lease semantics;
- authority and reversibility semantics;
- event/evidence semantics;
- supplier portability and shadow-drill primitives;
- conformance requirements and fixtures;
- portable process and capability representations.

These must remain implementable without Soven.

### Soven owns

- enterprise user experience;
- Process Studio and Control Center UX;
- operational analytics and adoption intelligence;
- supplier discovery and commercial intelligence;
- managed swap workflows and recommendations;
- deployment, integrations and enterprise administration;
- product-specific scoring and workflow automation;
- commercial services and ecosystem/network features.

These are product capabilities and must not become hidden protocol requirements.

## Integration contract

A Soven deployment should be able to:

1. ingest an OPCP process/capability definition;
2. execute or delegate capability calls through an OPCP-compatible runtime;
3. collect standard OPCP events and evidence;
4. run portability/shadow drills using protocol-defined semantics;
5. export process, context-contract, authority-policy and drill evidence in open formats;
6. replace Soven with another OPCP implementation without losing the institution-owned process definition.

The last point is a design constraint, not a marketing claim.

## Product-to-protocol rule

When a proposed Soven feature introduces a reusable interoperability primitive, first ask whether that primitive belongs in OPCP. If it affects how independent implementations exchange process, capability, context, authority or evidence information, prefer an OPCP proposal. If it primarily improves the operator experience, commercial workflow, analytics or managed service, keep it in Soven.

## Flagship integration scenario

The first end-to-end demonstration should be SME credit origination:

- institution-owned process definition;
- institution-owned context contract;
- incumbent and candidate suppliers implementing the same capability contract;
- unchanged authority policy;
- candidate exercised through shadow or approved test routing;
- standard evidence captured;
- promotion only after conformance and regression gates pass.

Soven presents and operates this workflow. OPCP defines the interoperable semantics underneath it.

## Independence test

A feature belongs in OPCP when an independent bank, supplier or open-source implementation would need the same semantic contract to interoperate.

A feature belongs in Soven when it creates differentiated product value without being necessary for two independent OPCP implementations to understand each other.
