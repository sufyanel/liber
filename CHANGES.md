# liber_pricelist_sync - change log

## 17.0.1.2.0 - WhatsApp 1 Oct 2026 + meetings 7 / 16 Oct
| Item | Change |
|---|---|
| Cost Rule per pricelist | "Vendor price list first" (default, meetings 7 + 16 Oct) or "Higher of vendor price list and last vendor bill" (Dale's WhatsApp 1 Oct: tariff increases entered on the vendor price list must never be undercut by an older bill). Both fall back to the average cost |
| Average cost | Only read, never changed (Dale: no change to a written-off part's average cost) |
| Sync result | Lists the products skipped for having no cost anywhere (first 25, then "and N more") |

## 17.0.1.1.0 - meeting 7 Oct 2026
| Requirement (Dale) | Change |
|---|---|
| "Prioritize off the vendor price list... pull off the top, not the cheapest" | Cost = top valid line of the vendor price list (Purchase tab order), converted for currency, UoM and discount |
| "If there is no vendor price list... the last vendor bill... then the average cost" | Then the latest posted vendor bill (bill line itself), then the average cost |
| "We use gross margin, not markup" | Percentage is Gross Margin: price = cost / (1 - margin); 50% doubles the cost; >= 100% refused |
| "So I can get all my products on the website listed" | Sync creates variant-level lines for saleable products without one and updates existing lines |
| Traceability | "Cost Source" column: vendor price list / vendor bill / average cost / entered manually |
| Upgrade | Migration converts stored markup to the equivalent gross margin - no price changes (100% -> 50%, 15% -> 13.04%) |

Tests: 7 passed. Deploy through the repository (Python module), then Apps > Upgrade.
