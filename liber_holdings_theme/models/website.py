# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug
from ..hooks import _configure_liber_holdings


class Website(models.Model):
    _inherit = "website"

    # Sibling themes each raise their own flag on the website they style.
    # Liber is the base layer, so a website belongs to Liber when no sibling
    # has claimed it. Computed as superuser so a public visitor can read it.
    LIBER_SIBLING_FLAGS = (
        "x_rbc_theme_active",
        "x_tc_theme_active",
        "x_tooling_theme_active",
        "x_tooling_components_theme_active",
        "x_globe_theme_active",
    )

    is_liber_site = fields.Boolean(
        string="Liber Holdings styling",
        compute="_compute_is_liber_site",
        compute_sudo=True,
        help="True when no sibling theme has claimed this website. Convenience for code; the templates use an import-safe check so they also work when the module is installed through Apps > Import Module, which strips Python.",
    )

    @api.depends(lambda self: [f for f in self.LIBER_SIBLING_FLAGS if f in self._fields])
    def _compute_is_liber_site(self):
        flags = [f for f in self.LIBER_SIBLING_FLAGS if f in self._fields]
        for website in self:
            website.is_liber_site = not any(website[f] for f in flags)

    def _liber_is_holding_website(self):
        """Liber Holdings itself (not a sibling, not Liber Industrial). Same rule as the controller."""
        from ..controllers.main import _liber_is_holding_website
        return _liber_is_holding_website(self)

    def rule_is_enumerable(self, rule):
        """Backstop for the live /sitemap.xml 500 (Dale, 17 + 24 Sep 2026): a controller override in another module
        that lacks @http.route() becomes a functools.partial without original_endpoint, and Odoo's check raised
        AttributeError, killing the whole sitemap on all four sites. Such a route is now skipped instead."""
        try:
            return super().rule_is_enumerable(rule)
        except AttributeError:
            return False

    def _enumerate_pages(self, query_string=None, force=False):
        """Keep the catalog out of the Liber Holdings sitemap.xml (Dale, 9 Oct 2026); other websites unchanged."""
        holding = self._liber_is_holding_website()
        # Globe Electric's catalog is view-only and must not be indexed (Dale, 14 Oct 2026)
        globe = "x_globe_theme_active" in self._fields and bool(self.x_globe_theme_active)
        for page in super()._enumerate_pages(query_string=query_string, force=force):
            if (holding or globe) and (page.get("loc") or "").startswith("/shop"):
                continue
            yield page

    @api.model
    def _liber_theme_setup(self):
        _configure_liber_holdings(self.env)

    @api.model
    def _liber_sync_shop_meta_copies(self):
        """Website-specific copies of products_shop_meta get the module arch."""
        generic = self.env.ref("liber_holdings_theme.products_shop_meta", raise_if_not_found=False)
        if not generic:
            return
        View = self.env["ir.ui.view"].sudo().with_context(active_test=False, lang="en_US")
        generic = View.browse(generic.id)
        copies = View.search([("key", "=", generic.key), ("website_id", "!=", False)])
        for view in copies:
            if "Industrial Spare Parts Shop" in (view.arch_db or ""):
                view.with_context(no_cow=True).write({"arch_db": generic.arch_db})

    @api.model
    def _liber_rebuild_holdings_menu(self):
        """Rebuild Liber Holdings top menu IA:
        Home, Family of Companies, Brands We Represent, Parts Catalog, Company History, News, Contact."""
        website = self if self.exists() else self.env["website"].get_current_website()
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
        companies = upsert("Family of Companies", "/#companies", 20)
        brands = upsert("Brands We Represent", "/brands", 30)
        about = upsert("Company History", "/about-us", 50)
        news = upsert("News & Updates", "/news", 60)
        contact = upsert("Contact Us", "/contactus", 70)

        # Remove legacy duplicates, and the catalog: Liber Holdings is view-only (Dale, 9 Oct 2026)
        for legacy_name in ("News", "About", "About Us", "Shop", "Resources", "Brands", "Parts Catalog", "Shop Parts"):
            legacy = Menu.search([
                ("website_id", "=", website.id),
                ("parent_id", "=", top.id),
                ("name", "=", legacy_name),
            ])
            keep = {home.id, companies.id, brands.id, about.id, news.id, contact.id}
            (legacy - Menu.browse(list(keep))).unlink()
        Menu.search([("website_id", "=", website.id), ("url", "=like", "/shop%")]).unlink()

    @api.model
    def _liber_style_contact_page(self):
        """Add stable theme hooks to the website-built contact page."""
        from lxml import etree

        website = self if self.exists() else self.env["website"].get_current_website()
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
        """Replace legacy markup with uniform per-company contact cards for Liber Holdings group."""
        import re
        from lxml import etree
        from odoo.tools import html_escape
        from urllib.parse import quote_plus

        companies = [
            {
                "name": "Liber Holdings (Corporate HQ)",
                "address": "3950 Doniphan Dr, Ste P, El Paso, TX 79922",
                "phone": "+1 (832) 791-2535",
                "email": "AP@liberholding.com",
            },
            {
                "name": "RBC Industrial",
                "address": "3950 Doniphan Dr, Ste P, El Paso, TX 79922",
                "phone": "+1 (915) 845-8188",
                "email": "sales@rogerbrownco.com",
            },
            {
                "name": "Tooling Components",
                "address": "8314 W High St, Union City, PA 16438",
                "phone": "+1 (814) 438-7657",
                "email": "sales@toolingcomponent.com",
            },
            {
                "name": "Globe Electric Supply",
                "address": "3950 Doniphan Dr, Ste P, El Paso, TX 79922",
                "phone": "+1 (832) 791-2535",
                "email": "sales@globeelectricsupply.com",
            },
            {
                "name": "Liber Industrial",
                "address": "30131 Bulverde Ln, #370, Bulverde, TX 78163",
                "phone": "+1 (832) 764-7979",
                "email": "sales@liberindustrial.com",
            },
        ]

        blocks = []
        for company in companies:
            tel = re.sub(r"[^\d+]", "", company["phone"])
            map_url = "https://www.google.com/maps/search/?api=1&query=%s" % quote_plus(company["address"])
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
        """Use clean blog post layout options (COW-safe)."""
        website = self if self.exists() else self.env["website"].get_current_website()
        if not website:
            return
        website_env = website.with_context(website_id=website.id)
        for key, active in (
            ("website_blog.opt_blog_post_regular_cover", True),
            ("website_blog.opt_blog_post_breadcrumb", True),
            ("website_blog.opt_blog_post_read_next", True),
            ("website_blog.opt_blog_post_readable", False),
        ):
            view = website_env.viewref(key, raise_if_not_found=False)
            if view and view.active != active:
                view.with_context(website_id=website.id).write({"active": active})

    @api.model
    def _liber_cleanup_about_page(self):
        """Clean about page and populate Liber Holdings heritage & company history."""
        website = self if self.exists() else self.env["website"].get_current_website()
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/about-us"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        new_arch = """
<t t-name="website.aboutus">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure oe_empty o_liber_about_page">
            <section class="o_liber_page_hero">
                <div class="container">
                    <span class="badge bg-danger mb-2 px-3 py-2 text-uppercase"><t t-if="website and (website.id == 7 or 'liberindustrial' in (website.domain or ''))">Est. 2018 • SDVOSB · Service-Disabled Veteran-Owned Small Business</t><t t-else="">Est. 2016 • Veteran-Owned</t></span>
                    <h1 class="display-4 fw-bold">Company History &amp; Leadership</h1>
                    <p class="lead" style="max-width: 750px;">
                        Liber Holdings is a privately-held industrial distribution and engineering group headquartered in El Paso, Texas.
                        Operating heritage since 1946, supplying heavy industry, aerospace, automotive stamping, and critical infrastructure across North America.
                    </p>
                </div>
            </section>
            <section class="py-5 bg-white">
                <div class="container">
                    <div class="row g-5 align-items-center">
                        <div class="col-lg-6">
                            <h2 class="h3 fw-bold mb-3">Our History &amp; Heritage</h2>
                            <p class="text-muted">
                                Liber Holdings LLC was formed in 2016 and in August of that year acquired Roger Brown Co. of El Paso, Texas, which was founded in 1946 and operates today as RBC Industrial - supplying precision bearings, power transmission, and specialized mechanical replacement parts to Southwest plants.
                            </p>
                            <p class="text-muted">
                                Since then the group has grown to include Liber Industrial (2018), Tooling Components (precision die spring and tooling specialists in Union City, PA) and Globe Electric Supply—forming Liber Holdings as the parent operating company.
                            </p>
                            <p class="text-muted">
                                Today, as a proud 100% veteran-owned enterprise, Liber Holdings maintains robust credit standing, extensive supplier networks, and strategic warehouse hubs in Texas and Pennsylvania.
                            </p>
                        </div>
                        <div class="col-lg-6">
                            <div class="p-4 rounded-3 border bg-light">
                                <h3 class="h5 fw-bold mb-3 text-danger"><i class="fa fa-shield me-2"/>Vendor &amp; Financial Governance</h3>
                                <p class="small text-muted mb-2">
                                    Liber Holdings serves as the primary corporate guarantor and credit partner for its operating subsidiaries.
                                </p>
                                <ul class="list-unstyled small text-muted mb-4">
                                    <li class="py-1"><i class="fa fa-check text-success me-2"/> Continuous operating heritage since 1946</li>
                                    <li class="py-1"><i class="fa fa-check text-success me-2"/> Fully audited accounting &amp; transparent trade credit references</li>
                                    <li class="py-1"><i class="fa fa-check text-success me-2"/> Unified logistics and ERP replenishment across multi-state warehouses</li>
                                </ul>
                                <a href="/contactus" class="btn btn-primary btn-sm w-100">Contact Corporate Credit Department</a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>
"""
        page.view_id.write({"arch_db": new_arch})
        page.write({
            "website_meta_title": "About Us & Company History | Liber Holdings",
            "website_meta_description": "Liber Holdings LLC (est. 2016) is a veteran-owned industrial distribution group with operating heritage since 1946, based in El Paso, TX.",
            "is_seo_optimized": True,
        })

    @api.model
    def _liber_rebuild_news_page(self):
        """Restyle /news: Liber hero band + readable card-layout blog posts."""
        website = self if self.exists() else self.env["website"].get_current_website()
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/news"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        new_arch = """
<t t-name="website.news">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure oe_empty o_liber_news_page">
            <section class="o_liber_page_hero">
                <div class="container">
                    <h1 class="display-4 fw-bold">Corporate News &amp; Updates</h1>
                    <p class="lead">
                        Announcements, brand partnerships, and industry developments from Liber Holdings and our family of companies.
                    </p>
                </div>
            </section>
            <section class="py-5 bg-white">
                <div class="container">
                    <div class="row g-4">
                        <div class="col-md-6 col-lg-4">
                            <div class="card h-100 border shadow-sm">
                                <div class="card-body">
                                    <span class="badge bg-danger mb-2">Corporate Announcement</span>
                                    <h5 class="card-title fw-bold">Liber Holdings Expands Regional Distribution Capabilities</h5>
                                    <p class="card-text text-muted small">
                                        Enhancing MRO and mechanical replenishment routing between RBC Industrial and Western Refinery warehouse hubs.
                                    </p>
                                </div>
                                <div class="card-footer bg-transparent border-0 pt-0">
                                    <small class="text-muted">October 2026</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="card h-100 border shadow-sm">
                                <div class="card-body">
                                    <span class="badge bg-secondary mb-2">Brand Representation</span>
                                    <h5 class="card-title fw-bold">Expanded Die Spring &amp; Tooling Inventory</h5>
                                    <p class="card-text text-muted small">
                                        Tooling Components broadens direct partnership inventory for Raymond, Danly, and Bordeon industrial springs.
                                    </p>
                                </div>
                                <div class="card-footer bg-transparent border-0 pt-0">
                                    <small class="text-muted">September 2026</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="card h-100 border shadow-sm">
                                <div class="card-body">
                                    <span class="badge bg-dark mb-2">Vendor Partnerships</span>
                                    <h5 class="card-title fw-bold">Vendor Onboarding &amp; Trade Credit Streamlining</h5>
                                    <p class="card-text text-muted small">
                                        New automated compliance and centralized credit validation launched for prospective suppliers.
                                    </p>
                                </div>
                                <div class="card-footer bg-transparent border-0 pt-0">
                                    <small class="text-muted">August 2026</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>
"""
        page.view_id.write({"arch_db": new_arch})
        page.write({
            "website_meta_title": "Corporate News & Updates | Liber Holdings",
            "website_meta_description": "News, brand partnerships, and industry developments from Liber Holdings.",
            "is_seo_optimized": True,
        })

    @api.model
    def _liber_rebuild_brands_page(self):
        """Build comprehensive 'Brands We Represent' page with organized brand cards."""
        website = self if self.exists() else self.env["website"].get_current_website()
        if not website:
            return

        page = self.env["website.page"].sudo().search([
            ("url", "=", "/brands"),
            ("website_id", "=", website.id),
        ], limit=1)
        if not page or not page.view_id:
            return

        new_arch = """
<t t-name="website.brands">
    <t t-call="website.layout">
        <div id="wrap" class="o_liber_brands_page">
            <section class="o_liber_brands_hero">
                <div class="container">
                    <span class="badge bg-danger mb-2 px-3 py-2 text-uppercase">Authorized Supplier Network</span>
                    <h1 class="display-4 fw-bold">Brands We Represent</h1>
                    <p class="lead" style="max-width: 750px;">
                        Liber Holdings distributes premier domestic and international brands across our operating companies:
                        RBC Industrial, Tooling Components, and Globe Electric Supply.
                    </p>
                </div>
            </section>
            <section class="py-5 bg-white">
                <div class="container">
                    <div class="mb-5">
                        <h2 class="h4 fw-bold pb-2 border-bottom"><i class="fa fa-cogs text-danger me-2"/>Die Springs &amp; Press Tooling</h2>
                        <p class="text-muted small">Represented primarily through <strong>Tooling Components</strong> (Union City, PA)</p>
                        <div class="row g-4 pt-2">
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Raymond</h5>
                                    <p class="small text-muted mb-0">Heavy-duty die springs, mechanical springs &amp; die supplies.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Danly</h5>
                                    <p class="small text-muted mb-0">Standard and custom die sets, guide posts, and press components.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Bordeon</h5>
                                    <p class="small text-muted mb-0">High-performance industrial springs and hardware.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Lempco</h5>
                                    <p class="small text-muted mb-0">Rotary bushings, die components &amp; guiding systems.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="mb-5">
                        <h2 class="h4 fw-bold pb-2 border-bottom"><i class="fa fa-circle-o text-danger me-2"/>Bearings, Seals &amp; Power Transmission</h2>
                        <p class="text-muted small">Represented primarily through <strong>RBC Industrial</strong> (El Paso, TX)</p>
                        <div class="row g-4 pt-2">
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Timken</h5>
                                    <p class="small text-muted mb-0">Tapered roller bearings, spherical bearings &amp; housing units.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">SKF</h5>
                                    <p class="small text-muted mb-0">Deep groove ball bearings, mounted units, and sealing systems.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Browning</h5>
                                    <p class="small text-muted mb-0">V-belts, sheaves, sprockets, and mechanical drives.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Diamond Chain (Timken)</h5>
                                    <p class="small text-muted mb-0">Premium ANSI roller chain and attachment chain for drives and conveyors.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Martin Sprocket</h5>
                                    <p class="small text-muted mb-0">Sprockets, gears, pulleys, and material handling solutions.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Rexnord</h5>
                                    <p class="small text-muted mb-0">Mounted bearings and couplings, engineered conveyor chain and industrial drives.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Leeson · Marathon · Techtop</h5>
                                    <p class="small text-muted mb-0">General-purpose, severe-duty and washdown AC motors.</p>
                                </div>
                            </div>
                            <div class="col-6 col-md-3">
                                <div class="p-3 border rounded text-center h-100 bg-light">
                                    <h5 class="fw-bold mb-1">Sealmaster</h5>
                                    <p class="small text-muted mb-0">Mounted bearings - high-performance mounted roller and ball bearings.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="p-4 rounded-3 bg-light border text-center">
                        <h3 class="h5 fw-bold mb-2">Inquire About Direct Supply or Becoming a Supplier Partner</h3>
                        <p class="text-muted small mb-3">Our sales and supply chain engineers are ready to assist with custom sourcing and vendor distribution agreements.</p>
                        <div class="d-flex justify-content-center gap-2">
                            <a href="/quote" class="btn btn-primary btn-sm">Request a Quote</a>
                            <a href="/contactus" class="btn btn-outline-danger btn-sm">Contact Corporate Team</a>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>
"""
        page.view_id.write({"arch_db": new_arch})
        page.write({
            "website_meta_title": "Brands We Represent | Liber Holdings",
            "website_meta_description": "Premier brands distributed by Liber Holdings, RBC Industrial, and Tooling Components.",
            "is_seo_optimized": True,
        })

    def _get_liber_mega_categories(self):
        return self.env["product.public.category"].search(
            [("parent_id", "=", False)],
            order="sequence, name",
            limit=16,
        )
