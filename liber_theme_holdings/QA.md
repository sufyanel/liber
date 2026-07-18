# Liber Holdings Theme — QA checklist (Phase 7)

## Automated checks (local, 2026-07-17)
| Route | Status | Notes |
|-------|--------|-------|
| `/` | 200 | Liber hero + H1 present; canonical liberholdings.com |
| `/shop` | 200 | Add to cart text CTAs; footer theme |
| `/quote` | 200 | Quote form H1 |
| `/contact` | 200 | 301 rewrite → `/contactus` |
| `/shop/category/bearings-1` | 200 | Shop renders |
| Die Springs category | 200 | Brand filter present; Add to cart |

## Manual / production follow-ups
- [ ] Set GA4 measurement ID (G-…) in Website settings (UA cleared)
- [ ] Configure CDN URL then enable CDN
- [ ] Tag quote-only SKUs with **Request Quote**
- [ ] Compress/move large PDF catalogs out of module static
- [ ] Fill missing product images
- [ ] Lighthouse Home + Shop after deploy; compare to PERFORMANCE.md baseline
- [ ] Verify Shop mega dropdown categories on desktop + mobile
- [ ] Submit test quote → CRM lead
- [ ] Confirm sibling websites unchanged (Tooling/RBC/etc.)
