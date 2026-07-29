# -*- coding: utf-8 -*-
{
    'name': 'Liber Web Design Layer (Variant 003 Hybrid Builder)',
    'summary': 'Brand palettes, fonts, trust/CTA/spec snippets, and SEO rich-result '
               'schema for the Tooling Components and RBC Industrial websites.',
    'description': """
Liber Holdings — Odoo Website Redesign (Variant 003: The Hybrid Builder)
========================================================================

A single, upgrade-safe module that implements the "Hybrid Builder" direction from the
Website Redesign Research (v1.1). It layers ON TOP of the existing websites — it does NOT
replace their current theme.

What it delivers
----------------
* Two brand colour palettes (Tooling Components, RBC Industrial) selectable per website
  from Website ▸ Edit ▸ Theme ▸ Colors — this closes the biggest brand-compliance gap in
  Section 7 of the research.
* Brand font configuration (Inter for Tooling Components; a distinct heading treatment
  for RBC Industrial), exposed in the font picker.
* Five brand-constrained, drag-and-drop snippets (the Variant 003 "snippet palette"):
  Trust Badges, Conversion CTA, Spec Table, Cross-Brand Compatibility, Author Bio.
* Product rich-result schema (schema.org Product/Offer + MPN/SKU) on every shop product
  page — the Section 9 P0 gap.
* Breadcrumb rich-result schema (schema.org BreadcrumbList) on every page.

Everything reads from the two palettes, so re-branding a site is a matter of changing
ten hex values in one SCSS file (or picking the other palette in the UI).
""",
    'author': 'Axiom World',
    'website': 'https://www.axiomworld.co',
    'category': 'Website',
    # Odoo major.minor + module major.minor.patch. Built and validated against 17.0.
    # The palette/font/snippet/schema mechanisms used here are stable across 17.0–19.0;
    # see README.md → "Version compatibility" before installing on 18.0/19.0.
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_blog',
        'website_sale',
    ],
    'data': [
        'views/snippets.xml',
        'views/snippets_register.xml',
        'views/product_jsonld.xml',
    ],
    'assets': {
        # Palettes + fonts must live in the primary-variables bundle so the Website
        # Builder can offer them. One file, listed explicitly (SaaS/Odoo.sh requirement).
        'web._assets_primary_variables': [
            'axiom_liber_theme/static/src/scss/primary_variables.scss',
        ],
        # Component styling + the breadcrumb JSON-LD injector run on the public site.
        'web.assets_frontend': [
            'axiom_liber_theme/static/src/scss/theme.scss',
            'axiom_liber_theme/static/src/js/breadcrumb_jsonld.js',
        ],
    },
    'installable': True,
    'application': False,
}
