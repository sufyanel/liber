# -*- coding: utf-8 -*-
from odoo import api, models


CATEGORY_INTROS = {
    "Bearings": "Deep groove, spherical, tapered, and specialty bearings for industrial MRO.",
    "Seals": "Shaft seals and sealing solutions to protect rotating equipment.",
    "Press Die Components": "Die springs and press tooling components for stamping and forming.",
    "Gearboxes": "Industrial gearboxes and speed reduction for power transmission.",
    "Tools": "Maintenance and production tools for plant operations.",
    "Electrical": "Industrial electrical components for spare-parts programs.",
    "Chain and Sprockets": "Drive chain and sprockets for conveyors and machinery.",
    "Belts and Sheaves": "V-belts, timing belts, and sheaves for power transmission.",
    "Abrasives": "Abrasives and finishing supplies for fabrication and maintenance.",
    "Conveyor Components": "Conveyor components to keep material handling lines running.",
    "Conveyor Componernts": "Conveyor components to keep material handling lines running.",
}


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    @api.model
    def _liber_seed_category_seo(self):
        for cat in self.search([("parent_id", "=", False)]):
            name = cat.name or ""
            intro = CATEGORY_INTROS.get(name)
            if intro and not (cat.website_description or "").strip():
                cat.website_description = f"<p>{intro}</p>"
            if not cat.website_meta_description and intro:
                cat.website_meta_description = intro
            if not cat.website_meta_title:
                cat.website_meta_title = f"{name} | Liber Industrial Parts"
