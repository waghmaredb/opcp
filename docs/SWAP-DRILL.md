# Rehearsing a supplier swap

A swap drill replaces an estimated time-to-swap with a measured one. Most exit plans are written but never rehearsed. A drill shows whether the plan works and how long each part really takes.

The specification defines time-to-swap as the elapsed days from a decision to replace the supplier behind a capability to the replacement running in production at equal or better quality, with no customer-facing disruption ([spec section 12.3](../spec/SPEC.md#123-time-to-swap)). It is reported in three parts: contracting, onboarding and technical cutover. Only a completed drill makes the figure `proven`.

## Pick the right process and the right kind of drill

What a drill may safely touch depends on the capability's reversibility class ([spec section 10](../spec/SPEC.md#10-authority-gate)):

| Capability | Typical class | Drill that is safe |
|---|---|---|
| `check`, `extract`, `retrieve` (identity checks, document extraction, lookups) | R0 | **Shadow drill:** the alternative supplier processes copies of real cases in parallel, and its results are compared but never acted on. |
| `generate`, `notify` (drafting, customer messages) | R1 to R4 | **Shadow drill** with output suppressed (nothing is sent), or a live cutover on an internal or test audience. |
| `transact` (payments, postings) | R2 and above | **Test-environment drill** only, or a live cutover on a small segment with each action approved. |
| `human_task` (manual review) | depends | **Live cutover** of a small queue to another team or provider, with supervision. |

For a first pilot, choose an R0 capability where a second supplier already exists or can be trialled cheaply. Identity verification and document extraction usually qualify.

## Run it

1. **Start the clock.** Record the date the swap is decided. This is day 0.
2. **Contracting.** Record the days to a signed agreement, a trial agreement or a standby contract with the alternative supplier. If a standby contract already exists, record 0 and cite it.
3. **Onboarding.** Record the days for security review, data-protection assessment and any regulator notification the swap would need. If no notification is needed for a drill, record what one would take, and mark that part as estimated.
4. **Technical cutover.** Point the capability at the alternative supplier. In the OPCP reference runtime this is a route change: a `weighted` route sends a share of traffic to the alternative. The runtime does not yet have a copy-only shadow mode, so a shadow drill sends copies of cases to the alternative through a test harness or the supplier's sandbox. Run until it has handled a representative sample.
5. **Compare quality.** Use the measures the process already tracks: match rate, accuracy, exception rate, latency, cost per case. It passes when the replacement is equal or better on each measure the process owner chose before the drill.
6. **Stop the clock.** Record the date the replacement met the quality bar. Then switch back, or keep it as the fallback supplier.

## Record the result

Update the answers file for the process:

- **ERS-EXT-01 to ERS-EXT-03:** the measured days for each part, with evidence `tested` and a reference to the drill record.
- **ERS-EXT-04:** the drill date.
- **ERS-DEP-02:** the alternative supplier, with evidence `tested`.

## When "proven" is honest

Mark the time-to-swap as proven only when all three parts were either measured in the drill or already in place, such as a standby contract signed before the drill. When one part was only estimated, a regulator notification for example, keep the figure `estimated`. The answers for the parts you did measure still carry `tested` evidence. That is not a failure: it tells the board exactly which part of the exit remains unknown.

A drill that found problems is the most useful kind. Record the gaps in the process notes, such as rules that lived only in the supplier's console or data that would not export. They become the actions the report recommends.
