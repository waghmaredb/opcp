# AI Adoption MVP

**Goal:** prove that a financial institution can adopt and replace AI capabilities without rebuilding the business process.

## The five-minute demo

### Scenario

A bank processes an SME credit application.

### Process

```text
Application received
       |
       v
Document extraction
       |
       v
KYC / identity verification
       |
       v
Business / trust score
       |
       +---- exception ----> Human review
       |
       v
Credit decision
```

### Demo state A — incumbent suppliers

The process runs with the incumbent supplier for each capability. The console shows:

- process owner;
- capability contract;
- supplier;
- data classification and residency;
- authority class;
- evidence requirements;
- quality / confidence;
- latency;
- cost;
- current fallback.

### Demo state B — supplier swap

Select one capability and click **Run Swap Drill**.

The system must:

1. freeze the process version;
2. identify the current supplier and candidate replacement;
3. prove both adapters conform to the same contract;
4. run the same business test set against both;
5. compare outputs and exception paths;
6. verify that authority and context rules are unchanged;
7. replay representative cases in shadow mode;
8. produce a signed swap report;
9. record measured time-to-swap.

### Target result

```text
SUPPLIER SWAP — PASSED

Capability              Document extraction
From                    Supplier A
To                      Supplier B
Process changed         NO
Authority changed       NO
Context schema changed  NO
Contract conformance    PASS
Regression tests        147 / 147
Critical deviations     0
Measured time-to-swap   2d 6h

[ Export evidence ]  [ Promote replacement ]
```

The exact numbers above are illustrative. The runtime must never fabricate a passed result; the UI should show real test counts and real timings from the drill.

## MVP components

### A. Process pack

A machine-readable SME credit origination process containing:

- named steps;
- capability IDs;
- variation points by country/entity/product;
- authority policy;
- test cases;
- exception outcomes;
- accountable roles.

### B. Two supplier adapters

At least two independent adapters for the same capability. The first implementation can use deterministic simulators; the design must make a later live supplier adapter a drop-in change.

### C. Swap engine

The minimum engine should compare:

- contract conformance;
- output schema validity;
- business-rule outcomes;
- evidence availability;
- confidence;
- latency;
- cost;
- exception routing;
- authority decisions.

### D. Context Home

For the MVP, store process intelligence in open files owned by the institution:

- process definition;
- capability contracts;
- route definitions;
- test sets;
- thresholds;
- exception labels;
- decision/event log.

No supplier-specific prompt, rule or decision history should be the source of truth.

### E. Evidence report

Every swap drill should produce an exportable evidence bundle containing:

- process version;
- capability contract version;
- suppliers and adapter versions;
- test-set hash;
- results summary;
- deviations;
- authority policy result;
- context lease result;
- timestamps;
- measured time-to-swap;
- operator / approver identity.

## MVP acceptance criteria

- [ ] One end-to-end SME credit process runs through the reference runtime.
- [ ] Two suppliers implement at least one identical capability contract.
- [ ] The same process definition can route between the suppliers without code changes.
- [ ] Context lease prevents undeclared fields from reaching the supplier.
- [ ] Authority gate blocks an autonomous R4 action.
- [ ] The swap drill runs the same test set against both suppliers.
- [ ] A failing replacement cannot be promoted.
- [ ] A passing replacement produces an exportable evidence bundle.
- [ ] The event log records enough evidence to reconstruct the drill.
- [ ] The process can be restored to the previous supplier using configuration only.

## What is deliberately out of scope

Do not build a full enterprise BPM replacement, model-training platform, data lake, procurement suite or generic agent builder in the first milestone.

The MVP exists to prove one sentence:

> **The bank owns the process; AI suppliers are interchangeable capabilities underneath it.**

## Design-partner proof

The software milestone is not enough. The MVP is successful only when a design partner says all three are true:

1. "This represents a real critical process."
2. "The evidence would help me approve or change an AI supplier."
3. "I believe I can leave the supplier without rebuilding the process."
