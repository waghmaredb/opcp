# Why the scorecard measures what it measures

The Exit-Readiness Scorecard rates each critical process on seven measures. This page sets out the published evidence behind each one: peer-reviewed research, supervisory analysis and competition-authority findings. Every source was opened and checked on 24 October 2026. The full list, with links, is in [`references/research.yaml`](../references/research.yaml). The obligations each question relates to are in the question bank and [`references/frameworks.yaml`](../references/frameworks.yaml).

Findings are paraphrased. Figures are given as each source states them.

## The problem is real, measured and growing

- **Most critical outsourced functions cannot easily be replaced.** ECB Banking Supervision reported that the share of outsourced critical functions at significant banks that are difficult or impossible to substitute rose from 80% to 82%, and that 95% of those are difficult or impossible to bring back in-house ([ECB 2025](https://www.bankingsupervision.europa.eu/press/supervisory-newsletters/newsletter/2025/html/ssm.nl250219_2.en.html)).
- **Spend is concentrated in a few providers.** Across 109 significant banks, about half of the budget for critical third-party contracts went to the top 20 providers ([ECB 2024](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.outsourcing_horizontal_analysis_202402~2b85022be5.en.pdf)).
- **Customers rarely switch.** The UK Competition and Markets Authority found that fewer than 1% of cloud customers switch provider each year, and identified egress fees and licensing practices as barriers ([CMA 2025](https://assets.publishing.service.gov.uk/media/688b20e6ff8c05468cb7b120/summary_of_final_decision.pdf)).
- **Third parties are a major source of disruption.** In the EU, 29% of the 3,383 major ICT incidents reported by financial entities in 2025 were caused by a failure attributable to a third-party provider ([ESAs 2026](https://www.eiopa.europa.eu/publications/esas-joint-report-major-ict-related-incidents-2025_en)). Across nine years of publicly reported outages, Uptime Institute attributes about two-thirds to third-party IT and data-centre providers ([Uptime 2025](https://uptimeinstitute.com/about-ui/press-releases/uptime-announces-annual-outage-analysis-report-2025)).
- **AI raises the stakes.** The Financial Stability Board lists third-party dependency and provider concentration first among the AI vulnerabilities that could increase systemic risk ([FSB 2024](https://www.fsb.org/uploads/P14112024.pdf)). The Bank of England's Financial Policy Committee and the IMF make similar observations ([Bank of England 2025](https://www.bankofengland.co.uk/financial-stability-in-focus/2025/april-2025); [IMF 2026](https://www.imf.org/-/media/files/publications/imf-notes/2026/english/insea2026005.pdf)).
- **Firms underweight the risk at the start.** In a survey of 114 participants, only 8.4% named building lock-in risk into the initial risk assessment as a best practice ([Opara-Martins et al. 2016](https://link.springer.com/article/10.1186/s13677-016-0054-z)).

## Measure by measure

### Logic ownership

When a supplier holds the rules and thresholds of a process, replacing the supplier means rediscovering how the business works. No regulation requires a firm to own its process logic as such. But the Basel Committee's 2021 operational resilience principles ask firms to map what each critical operation depends on, and EU rules require exit plans that can move a service to another provider or back in-house. Neither is possible if only the supplier knows how the process works (see the references on question ERS-LOG-01).

### Context residency

Data that can be exported is not the same as a process that can move. Raw records may leave while tuned settings, corrections and model-specific work stay behind. Research on large language models finds that prompts engineered for one model often perform substantially worse on another, so AI processes carry a re-engineering cost when they move ([Wang et al. 2025, preprint](https://arxiv.org/abs/2512.01420)). The scorecard therefore asks about decisions, corrections and history, not just data.

### Authority

If a supplier's system can act on customers or the firm without the firm's approval, the firm's control depends on the supplier's permission model. Exiting such a supplier means rebuilding controls as well as functionality. No regulation prescribes a firm-owned permission model, but supervisory texts consistently keep responsibility with the firm and ask for contractual access, audit and information rights, which serve the same aim of keeping the firm in control.

### Lock-in debt

Economic research has long shown that switching costs give suppliers market power over customers once they are locked in, and that suppliers tend to seek more incompatibility than is efficient ([Farrell & Klemperer 2007](https://ideas.repec.org/h/eee/indchp/3-31.html); [Klemperer 1995](https://ideas.repec.org/a/oup/restud/v62y1995i4p515-539..html)). Firm-level evidence puts the cost of switching IT outsourcing providers at about one-third of annual spend on professional services ([Peukert 2019](https://ideas.repec.org/a/taf/tjisxx/v28y2019i3p291-317.html)). Counting supplier-only features makes that debt visible before it is due.

### Contract exit terms

Switching costs are partly set by the contract: data return, transition assistance and notice periods determine how fast an exit can start. International principles from the Basel Committee, IOSCO and the FSB all call for termination rights, data return and transition support in contracts for critical services (see framework references).

### Time-to-swap

Exits take longer than firms expect. The US Treasury reported that moving complex workloads to another cloud provider or back in-house was expected to take many months, or even years, in nearly every case ([US Treasury 2023](https://home.treasury.gov/system/files/136/Treasury-Cloud-Report.pdf)). The Basel Committee's 2025 principles expect exit plans that are kept up to date and tested ([BCBS 2025](https://www.bis.org/publications/202512-guidelines-principles-sound-management-third-party-risk.pdf)). That is why the scorecard separates estimated from proven time-to-swap, and splits it into contracting, onboarding and cutover: the first two are often the longest.

### Fallback supplier

A named, qualified alternative changes the risk profile sharply. In an illustrative ESMA model of simultaneous outages of two hours or more, the probability of a systemic event under cloud outsourcing without backup was around a thousand times the no-cloud baseline, and fell to about the baseline when each firm had a backup provider ([ESMA 2021](https://www.esma.europa.eu/sites/default/files/trv_2021_2-cloud_outsourcing_and_financial_stability_risks.pdf)). The model assumes a provider's clients fail together and that different providers fail independently; the authors note that correlated provider failures would weaken the benefit. Treat the figure as directional.

### Concentration across the portfolio

Individual-firm assessments miss shared dependencies. The BIS Financial Stability Institute notes that firm-by-firm third-party frameworks do not capture the systemic effect of a dominant provider failing ([BIS FSI 2023](https://www.bis.org/fsi/publ/insights53.htm)). The UK now oversees critical third parties directly ([PRA/FCA PS16/24](https://www.bankofengland.co.uk/prudential-regulation/publication/2024/november/operational-resilience-critical-third-parties-to-the-uk-financial-sector-policy-statement)). The scorecard's concentration view applies the same logic inside one firm.

## Why a standard question bank

Standardised questionnaires are how third-party assessment became comparable across firms. Examples include the Cloud Security Alliance's Consensus Assessments Initiative Questionnaire and the Shared Assessments SIG. OPCP's question bank follows the same principle: stable question IDs, closed answers and evidence levels. Unlike those, it is open under Apache 2.0 and focused on exit readiness rather than security controls. OPCP writes its own questions; where it relates to Cloud Controls Matrix controls, it cites their IDs only.

## Limits of this evidence

- Most quantitative evidence comes from financial services in the EU, UK and US. Its applicability elsewhere is an assumption.
- Some sources use voluntary samples, such as the ESAs' 2023 provider landscape.
- One AI source is a preprint. No peer-reviewed study of AI platform lock-in was found.
- The scorecard's thresholds (for example, a 90-day swap tolerance) are defaults for firms to set, not findings from this research.
