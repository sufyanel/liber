# Liber Holdings Theme — Performance baseline (Phase 0 / Phase 6)

## Targets
- Home LCP < 2.5s (mid-tier mobile network)
- TTFB < 600ms with CDN / Odoo.sh cache in production
- Perceived instant nav via sticky header + deferred non-critical JS

## Before (production audit snapshot)
- Homepage HTML ~24KB; TTFB ~0.8–1.1s
- Shop HTML ~287KB; TTFB ~1.0–2.2s
- `web.assets_frontend.min.css` ~787KB
- `web.assets_frontend_lazy.min.js` ~2.7MB
- Canonical incorrectly pointed at liber.odoo.com
- Legacy UA analytics (UA-82752407-6)
- Google Fonts remote; 25MB PDF in addon static

## After (this module)
- Domain set to https://www.liberholdings.com (canonical fix)
- UA key cleared — set GA4 `G-…` in Website > Configuration > Settings
- Self-hosted Barlow / Barlow Condensed WOFF2 (no fonts.googleapis.com)
- Design tokens + lean theme SCSS in `liber_theme_holdings`
- Hybrid Cart / Quote reduces dead-end PDP flows
- `/contact` → `/contactus` 301
- Category SEO intros seeded for top categories
- Conveyor typo fixed to "Conveyor Components"
- CDN: enable in Website settings when CDN URL is configured (Odoo.sh / CloudFront)

## Ops checklist (production)
1. Website domain = https://www.liberholdings.com
2. Paste GA4 measurement ID
3. Configure CDN URL + activate CDN filters for `/web/image` and `/web/assets`
4. Compress catalog PDFs; host via Documents / attachments (remove 25MB static files when ready)
5. Defer livechat to contact pages in Website settings if available
6. Fill missing product images (priority published without image_1920)
7. Tag quote-only SKUs with product tag **Request Quote**
