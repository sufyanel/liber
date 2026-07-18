# -*- coding: utf-8 -*-
from odoo import api, models

from odoo.addons.http_routing.models.ir_http import slug

from ..hooks import _configure_liber_holdings


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _liber_theme_setup(self):
        _configure_liber_holdings(self.env)

    @api.model
    def _liber_rebuild_holdings_menu(self):
        """Rebuild Liber Holdings top menu IA (Shop dropdown + Resources + Contact)."""
        website = self.sudo().browse(1)
        if not website.exists():
            website = self.sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
        if not website or not website.menu_id:
            return

        Menu = self.env["website.menu"].sudo()
        top = website.menu_id

        def upsert(name, url, sequence, parent=top):
            existing = Menu.search([
                ("website_id", "=", website.id),
                ("parent_id", "=", parent.id),
                ("name", "=", name),
            ], limit=1)
            vals = {
                "name": name,
                "url": url,
                "parent_id": parent.id,
                "website_id": website.id,
                "sequence": sequence,
            }
            if existing:
                existing.write(vals)
                return existing
            return Menu.create(vals)

        home = upsert("Home", "/", 10)
        shop = upsert("Shop", "/shop", 20)
        brands = upsert("Brands", "/brands", 30)
        resources = upsert("Resources", "/news", 40)
        about = upsert("About", "/about-us", 50)
        contact = upsert("Contact", "/contactus", 60)

        # Remove legacy top-level duplicates
        for legacy_name in ("News", "About Us"):
            legacy = Menu.search([
                ("website_id", "=", website.id),
                ("parent_id", "=", top.id),
                ("name", "=", legacy_name),
            ])
            keep = {resources.id, about.id}
            (legacy - Menu.browse(list(keep))).unlink()

        # Shop children: All Products first, then top categories
        shop.child_id.unlink()
        Menu.create({
            "name": "All Products",
            "url": "/shop",
            "parent_id": shop.id,
            "website_id": website.id,
            "sequence": 1,
        })
        seq = 10
        for categ in website._get_liber_mega_categories():
            Menu.create({
                "name": categ.name,
                "url": "/shop/category/%s" % slug(categ),
                "parent_id": shop.id,
                "website_id": website.id,
                "sequence": seq,
            })
            seq += 10

        resources.child_id.unlink()
        upsert("News", "/news", 10, parent=resources)
        upsert("Catalogs", "/shop", 20, parent=resources)

        for menu, seq_val in (
            (home, 10), (shop, 20), (brands, 30),
            (resources, 40), (about, 50), (contact, 60),
        ):
            menu.sequence = seq_val

        self._liber_rebuild_brands_page()
        self._liber_rebuild_news_page()
        self._liber_cleanup_about_page()
        self._liber_set_blog_post_views()
        self._liber_style_contact_page()

    @api.model
    def _liber_style_contact_page(self):
        """Add stable theme hooks to the website-built contact page."""
        from lxml import etree

        website = self.sudo().browse(1)
        if not website.exists():
            website = self.sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/contactus"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        view = page.view_id
        arch = view.arch_db or ""
        try:
            root = etree.fromstring(arch.encode("utf-8"))
        except etree.XMLSyntaxError:
            return

        def add_class(node, *names):
            classes = (node.get("class") or "").split()
            for name in names:
                if name not in classes:
                    classes.append(name)
            node.set("class", " ".join(classes))

        wraps = root.xpath("//*[@id='wrap']")
        if wraps:
            add_class(wraps[0], "o_liber_contact_page")

        heroes = root.xpath("//section[contains(concat(' ', normalize-space(@class), ' '), ' s_title ')]")
        if heroes:
            add_class(heroes[0], "o_liber_contact_hero")

        forms = root.xpath("//*[@id='contactus_form']")
        if not forms:
            return
        form = forms[0]
        form_sections = form.xpath("ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' s_website_form ')][1]")
        if form_sections:
            add_class(form_sections[0], "o_liber_contact_form")

        main_sections = form.xpath(
            "ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' s_text_block ')][1]"
        )
        if main_sections:
            main = main_sections[0]
            add_class(main, "o_liber_contact_main")
            rows = main.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' row ')][1]")
            if rows:
                row = rows[0]
                add_class(row, "o_liber_contact_grid")
                columns = row.xpath("./div[contains(concat(' ', normalize-space(@class), ' '), ' col-lg-4 ')]")
                if columns:
                    add_class(columns[0], "o_liber_contact_form_panel")
                if len(columns) >= 3:
                    # The original snippet split Liber Holdings from the other
                    # company contacts. Keep one contact sidebar beside the form.
                    source = columns[1]
                    target = columns[-1]
                    for child in reversed(list(source)):
                        target.insert(0, child)
                    row.remove(source)
                    columns = [columns[0], target]
                if len(columns) > 1:
                    details = columns[-1]
                    add_class(details, "o_liber_contact_details")
                    self._liber_rebuild_contact_companies(details)

        cleaned = etree.tostring(root, encoding="unicode")
        if cleaned != arch:
            view.write({"arch_db": cleaned})

    def _liber_rebuild_contact_companies(self, details_node):
        """Replace legacy mixed markup with uniform per-company contact cards."""
        import re
        from lxml import etree
        from odoo.tools import html_escape
        from urllib.parse import quote_plus

        companies = [
            {
                "name": "Liber Holdings",
                "address": "3950 Doniphan Dr, Ste P, El Paso, TX 79922",
                "phone": "+1 (832) 791-2535",
                "email": "sales@liberholding.com",
            },
            {
                "name": "Roger Brown Co",
                "address": "3950 Doniphan Dr, Ste P, El Paso, TX 79922",
                "phone": "+1 (915) 845-8188",
                "email": "sales@rogerbrownco.com",
            },
            {
                "name": "Liber Industrial",
                "address": "30131 Bulverde Ln, #370, Bulverde, TX 78163",
                "phone": "+1 (832) 764-7979",
                "email": "sales@liberindustrial.com",
            },
            {
                "name": "Tooling Components",
                "address": "8314 W High St, Union City, PA 16438",
                "phone": "+1 (814) 438-7657",
                "email": "sales@toolingcomponent.com",
            },
        ]

        blocks = []
        for company in companies:
            tel = re.sub(r"[^\d+]", "", company["phone"])
            map_url = "https://www.google.com/maps/search/?api=1&query=%s" % quote_plus(
                company["address"]
            )
            blocks.append(
                '<div class="o_liber_company_block">'
                f'<div class="o_liber_company_name">{html_escape(company["name"])}</div>'
                '<div class="o_liber_company_line o_liber_company_address">'
                '<i class="fa fa-map-marker fa-fw" role="presentation"/>'
                f'<a href="{html_escape(map_url)}" target="_blank" '
                f'rel="noopener noreferrer" aria-label="View {html_escape(company["name"])} on Google Maps">'
                f'{html_escape(company["address"])}</a>'
                "</div>"
                '<div class="o_liber_company_line">'
                '<i class="fa fa-phone fa-fw" role="presentation"/>'
                f'<a href="tel:{html_escape(tel)}">{html_escape(company["phone"])}</a>'
                "</div>"
                '<div class="o_liber_company_line">'
                '<i class="fa fa-envelope fa-fw" role="presentation"/>'
                f'<a href="mailto:{html_escape(company["email"])}">{html_escape(company["email"])}</a>'
                "</div>"
                "</div>"
            )

        fragment = etree.fromstring(
            '<div class="o_liber_company_list">%s</div>' % "".join(blocks)
        )
        details_node.text = None
        for child in list(details_node):
            details_node.remove(child)
        details_node.append(fragment)

    @api.model
    def _liber_set_blog_post_views(self):
        """Use Liber-friendly blog post layout options (COW-safe)."""
        website = self.sudo().browse(1)
        if not website.exists():
            website = self.sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
        if not website:
            return
        website_env = website.with_context(website_id=website.id)
        for key, active in (
            ("website_blog.opt_blog_post_regular_cover", True),
            ("website_blog.opt_blog_post_breadcrumb", True),
            ("website_blog.opt_blog_post_read_next", True),
            # Posts are built with snippets (multi-column rows); the narrow
            # "readable" column squeezes them and breaks their layout.
            ("website_blog.opt_blog_post_readable", False),
        ):
            view = website_env.viewref(key, raise_if_not_found=False)
            if view and view.active != active:
                view.with_context(website_id=website.id).write({"active": active})

    @api.model
    def _liber_cleanup_about_page(self):
        """Drop empty leftover sections that leave a huge gap above the footer."""
        import re

        website = self.sudo().browse(1)
        if not website.exists():
            website = self.sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/about-us"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        view = page.view_id
        arch = view.arch_db or ""
        # Empty Image-Text block with o_half_screen_height ≈ half viewport blank space
        cleaned = re.sub(
            r'<section\b[^>]*\bo_half_screen_height\b[^>]*>\s*'
            r'<div class="container">\s*'
            r'<div class="row[^"]*"[^>]*>\s*'
            r'(?:<p><br/?>\s*</p>\s*)*'
            r'</div>\s*</div>\s*</section>\s*',
            "",
            arch,
            flags=re.I,
        )
        if cleaned != arch:
            view.write({"arch_db": cleaned})

    @api.model
    def _liber_rebuild_news_page(self):
        """Restyle /news: Liber hero band + readable card-layout blog posts."""
        import re

        website = self.sudo().browse(1)
        if not website.exists():
            website = self.sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/news"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        view = page.view_id
        arch = view.arch_db or ""
        # Preserve the dynamic snippet filter already configured on this DB
        m = re.search(r'data-filter-id="(\d+)"', arch)
        filter_id = m.group(1) if m else ""
        filter_attr = f' data-filter-id="{filter_id}"' if filter_id else ""

        new_arch = (
            '<t t-name="website.news">'
            '<t t-call="website.layout">'
            '<div id="wrap" class="oe_structure oe_empty o_liber_news_page">'
            '<section class="o_liber_page_hero" data-name="Title">'
            '<div class="container">'
            "<h1>News</h1>"
            '<p class="o_liber_page_hero_lead">'
            "Events and updates from Liber Holdings and our family of companies."
            "</p>"
            "</div></section>"
            '<section data-snippet="s_blog_posts" data-name="Blog Posts"'
            ' class="s_blog_posts s_dynamic_snippet_blog_posts s_blog_post_card'
            ' s_dynamic pt40 pb48 o_colored_level o_dynamic_empty o_liber_news_posts"'
            ' style="background-image: none;"'
            f"{filter_attr}"
            ' data-template-key="website_blog.dynamic_filter_template_blog_post_card"'
            ' data-number-of-elements="3" data-filter-by-blog-id="-1"'
            ' data-number-of-elements-small-devices="1" data-number-of-records="16">'
            '<div class="o_not_editable container">'
            '<div class="css_non_editable_mode_hidden">'
            '<div class="missing_option_warning alert alert-info rounded-0 fade show'
            ' d-none d-print-none o_default_snippet_text">'
            "Your Dynamic Snippet will be displayed here..."
            "</div></div>"
            '<div class="dynamic_snippet_template"/>'
            "</div></section>"
            "</div>"
            "</t></t>"
        )
        view.write({"arch_db": new_arch})
        page.write({
            "website_meta_title": "News | Liber Holdings",
            "website_meta_description": (
                "News, events and updates from Liber Holdings and our family "
                "of industrial supply companies."
            ),
            "is_seo_optimized": True,
        })

    @api.model
    def _liber_rebuild_brands_page(self):
        """Replace masonry brands page with a uniform Liber logo grid."""
        import re
        from urllib.parse import unquote
        from odoo.tools import html_escape

        website = self.sudo().browse(1)
        if not website.exists():
            website = self.sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/brands"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        view = page.view_id
        arch = view.arch_db or ""
        # Prefer existing logos; fall back to current rendered sources already in arch
        srcs = re.findall(r'src="(/web/image/[^"]+)"', arch)
        logos = []
        seen = set()
        for src in srcs:
            if src in seen:
                continue
            if "placeholder" in src.lower() or "s_image" in src.lower():
                continue
            seen.add(src)
            logos.append(src)

        if not logos:
            return

        cells = []
        for src in logos:
            filename = unquote(src.rsplit("/", 1)[-1])
            alt = re.sub(r"\.(png|jpe?g|gif|webp|svg).*$", "", filename, flags=re.I)
            alt = re.sub(r"[\-_]+", " ", alt)
            alt = re.sub(r"\s*\(\d+\)\s*", " ", alt).strip() or "Brand"
            cells.append(
                '<div class="col-6 col-sm-4 col-md-3 col-xl-2">'
                '<div class="o_liber_brand_tile">'
                f'<img src="{html_escape(src)}" alt="{html_escape(alt)}" loading="lazy"/>'
                f'<span class="o_liber_brand_name">{html_escape(alt)}</span>'
                "</div></div>"
            )

        new_arch = (
            '<t t-name="website.brands">'
            '<t t-call="website.layout">'
            '<div id="wrap" class="o_liber_brands_page">'
            '<section class="o_liber_brands_hero">'
            '<div class="container">'
            "<h1>Brands</h1>"
            '<p class="o_liber_brands_lead">'
            "Manufacturers we stock for industrial spare parts — "
            "bearings, power transmission, seals, and MRO."
            "</p>"
            "</div></section>"
            '<section class="o_liber_section o_liber_brands_section">'
            '<div class="container">'
            '<div class="row g-3 o_liber_brands_grid">'
            + "".join(cells)
            + "</div>"
            '<div class="o_liber_howto_ctas mt-4">'
            '<a href="/shop" class="btn btn-primary">Shop parts</a>'
            '<a href="/quote" class="btn btn-outline-liber">Request quote</a>'
            "</div>"
            "</div></section>"
            "</div>"
            "</t></t>"
        )
        view.write({"arch_db": new_arch})

        # Clear stale SEO that still carried the old duplicate marketing line
        page.write({
            "website_meta_title": "Brands | Liber Holdings",
            "website_meta_description": (
                "Manufacturers Liber stocks for industrial spare parts — "
                "bearings, power transmission, seals, and MRO."
            ),
            "is_seo_optimized": True,
        })

    def _get_liber_mega_categories(self):
        return self.env["product.public.category"].search(
            [("parent_id", "=", False)],
            order="sequence, name",
            limit=16,
        )
