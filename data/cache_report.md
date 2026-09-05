# Cache data report

years: 2015–2025
mode: cached-only (no network, no synthetic sample)

## Signal coverage (1 = cached, 0 = missing)

| field | papers | repos (latest yr) | questions (latest yr) |
|---|---|---|---|
| AI / Machine Learning | full | 11/11 yrs | 11/11 yrs |
| Applied Mathematics | full | 11/11 yrs | 11/11 yrs |
| Computer Science (general) | full | 11/11 yrs | 11/11 yrs |
| Software Engineering | full | 11/11 yrs | 11/11 yrs |
| Quantitative Finance | full | 11/11 yrs | 11/11 yrs |
| Cryptocurrency / FinTech | full | 11/11 yrs | 0/11 yrs |
| Quantum Computing / Cryptography | full | 0/11 yrs | 11/11 yrs |
| Chips / GPU / Memory Hardware | — | 0/11 yrs | 0/11 yrs |

## Descriptive statistics

| field | papers_latest | papers_CAGR | repos_latest | repos_CAGR | q_latest | q_CAGR | repos_burst | q_burst | CSI_latest |
|---|---|---|---|---|---|---|---|---|---|
| AI / Machine Learning | 2726909 | 0.205 | 71217 | 0.289 | 471 | -0.638 | 1 | 0 | 0.65 |
| Applied Mathematics | 2611411 | 0.15 | 3054 | 0.205 | 792 | -0.612 | 1 | 0 | 0.65 |
| Computer Science (general) | 3264476 | 0.073 | 12025 | 0.016 | 1884 | -0.607 | 1 | 0 | 0.593 |
| Software Engineering | 1515112 | 0.071 | 10300 | 0.481 | 314 | -0.481 | 1 | 0 | 0.645 |
| Quantitative Finance | 1559499 | 0.161 | 2550 | 0.844 | 1079 | -0.706 | 1 | 0 | 0.65 |
| Cryptocurrency / FinTech | 336670 | 0.182 | 5366 | -0.209 | 0 | None | 0 | 0 | 0.685 |
| Quantum Computing / Cryptography | 92494 | 0.107 | 0 | None | 12 | -0.347 | 0 | 0 | 0.526 |
| Chips / GPU / Memory Hardware | 0 | None | 0 | None | 0 | None | 0 | 0 | 0.0 |

## Cross-field correlation of CSI (latest 5 years)

| | AI / Machi | Applied Ma | Computer S | Software E | Quantitati | Cryptocurr | Quantum Co | Chips / GP |
| AI / Machi | 1.0 | 0.8 | -0.57 | 0.39 | 0.94 | 0.14 | -0.81 | None |
| Applied Ma | 0.8 | 1.0 | 0.0 | 0.5 | 0.94 | 0.5 | -0.97 | None |
| Computer S | -0.57 | 0.0 | 1.0 | -0.19 | -0.29 | 0.27 | 0.07 | None |
| Software E | 0.39 | 0.5 | -0.19 | 1.0 | 0.56 | 0.89 | -0.66 | None |
| Quantitati | 0.94 | 0.94 | -0.29 | 0.56 | 1.0 | 0.43 | -0.96 | None |
| Cryptocurr | 0.14 | 0.5 | 0.27 | 0.89 | 0.43 | 1.0 | -0.63 | None |
| Quantum Co | -0.81 | -0.97 | 0.07 | -0.66 | -0.96 | -0.63 | 1.0 | None |
| Chips / GP | None | None | None | None | None | None | None | None |

> Generated from disk cache only. Constant (all-zero) signals are dropped from CSI with weight renormalization, so a missing GitHub source does not silently zero a field.