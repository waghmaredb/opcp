# Exporting to regulatory registers

Registers of third-party arrangements ask some of the same questions as the scorecard: how substitutable a provider is, whether the service could be brought back in-house, whether an alternative has been identified, and the contract's notice period and end date. `opcp scorecard export` turns an assessment into **suggested** register values, so a firm can check what it reports against its scorecard answers instead of answering twice.

```bash
opcp scorecard export answers.json --register dora -o dora-suggestions.csv
```

The output is a CSV with one row per critical process. It is a suggestion for review, **never a filing**. The firm fills in its own contract reference and provider code, checks each value against its records, and copies what it agrees with into its register.

## Supported registers

| Register | Status | Source |
|---|---|---|
| EU DORA register of information | **Supported**: B_07.01 and two B_02.02 fields | Commission Implementing Regulation (EU) 2024/2956, Annex I |
| UK PRA/FCA outsourcing and third-party register | Not yet. The final fields (PS7/26, March 2026, applying from March 2027) are only partly confirmed. | PRA PS7/26 / FCA PS26/2 |
| APRA CPS 230 material service provider register | Not yet. The column list sits in APRA's template workbook and has not been checked. | APRA CPS 230 para 51 |
| MAS register of third-party arrangements (proposed) | Not yet. The draft template is in the March 2026 consultation (P004-2026) and has not been checked. | MAS P004-2026, Annex B |

## How the DORA values are suggested

The field codes and closed-list values come from the regulation. Turning scorecard answers into those values is OPCP's own reasoning, set out here so a reviewer can disagree with it.

| Field | Suggested value | Rule |
|---|---|---|
| B_07.01.0050 Substitutability | `Highly complex substitutability`, `Medium complexity in terms of substitutability` or `Easily substitutable` | The worst of four measures: time-to-swap, lock-in, context residency and fallback. Locked gives highly complex, partial gives medium, and ready gives easily. **Easily substitutable** is suggested only when the time-to-swap is proven by a drill; an estimate caps it at medium. **Not substitutable** is never suggested: it means the market has no real alternative, which is the firm's judgement, and an alternative not yet identified is not evidence of that. |
| B_07.01.0060 Reason | `1`, `2` or `3` | Given only for highly complex. 1: no alternative identified. 2: migrating data and workloads is difficult, because context isn't fully exportable, lock-in or time-to-swap isn't ready, or the logic is held by the supplier. 3: both. |
| B_07.01.0080 Existence of an exit plan | `Yes` or blank | The scorecard doesn't ask whether a documented exit plan exists. It suggests `Yes` only when a swap drill within 12 months of the assessment date shows a plan working in practice. Otherwise the field is left for the firm. |
| B_07.01.0090 Possibility of reintegration | `Easy`, `Difficult` or `Highly complex` | The harder of bringing back the logic (owned, shared or vendor-held) and the context (exportable, partial or trapped). |
| B_07.01.0110 Alternative providers identified | `Yes` or `No` | Whether the assessment names a fallback supplier. |
| B_07.01.0120 Identification of alternative ICT TPP | text | The fallback supplier as named. Replace it with the provider's identification code before filing. |
| B_02.02.0080 End date | date | The contract end or renewal date, if given. |
| B_02.02.0100 Notice period for the financial entity | days | The firm's notice period to end the contract. |

Every row ends with a **basis** column saying which answers drove each suggestion.

## What stays with the firm

- **The key columns.** B_07.01.0010 (contractual arrangement reference number) and B_07.01.0020 (provider identification code) are left blank.
- **Columns the scorecard has no answers for:**
  - B_07.01.0030 type of code
  - B_07.01.0040 type of ICT services
  - B_07.01.0070 date of the last audit. A swap drill is not an audit, so the drill date never goes here.
  - B_07.01.0100 impact of discontinuing the service
  - all of B_06.01, the function-level template
- **Contract-level reporting.** Under DORA each row describes a contractual arrangement. If one process uses several contracts, or one contract serves several processes, the firm decides how the suggestions apply.

## Before relying on it

The field codes and value labels were checked against the published regulation in October 2026, through a summarised reading of the EUR-Lex text. Check them against the official text, and against the technical package your supervisor uses for submissions, before you copy anything. The closed-list labels may be filed as codes rather than as words.
