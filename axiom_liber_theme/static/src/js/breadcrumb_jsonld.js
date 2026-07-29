/*
 * Liber Web Design Layer — Breadcrumb rich-result schema.
 *
 * Emits a schema.org BreadcrumbList JSON-LD block built from the breadcrumb
 * already rendered on the page. Reading the DOM (rather than overriding the
 * server-side breadcrumb template) keeps this 100% version-tolerant and means
 * it can never break page rendering: if there is no breadcrumb, it does nothing.
 *
 * Google executes on-page JS and reads JSON-LD injected this way. If you later
 * want server-rendered breadcrumb schema (marginally preferred), this can be
 * moved into a QWeb template — but this approach is the zero-risk default.
 */
(function () {
    "use strict";

    function buildBreadcrumbSchema() {
        try {
            if (document.getElementById("liber_breadcrumb_jsonld")) {
                return; // already injected
            }

            // Find the first Bootstrap breadcrumb on the page.
            var crumb = document.querySelector("ol.breadcrumb, .breadcrumb");
            if (!crumb) {
                return;
            }

            var items = crumb.querySelectorAll("li, .breadcrumb-item");
            if (!items || items.length < 2) {
                return; // a single crumb is not worth marking up
            }

            var elements = [];
            var position = 1;

            items.forEach(function (li) {
                var label = (li.textContent || "").replace(/\s+/g, " ").trim();
                if (!label) {
                    return;
                }
                var entry = {
                    "@type": "ListItem",
                    position: position,
                    name: label,
                };
                var link = li.querySelector("a[href]");
                if (link && link.href) {
                    entry.item = link.href;
                }
                elements.push(entry);
                position += 1;
            });

            if (elements.length < 2) {
                return;
            }

            var schema = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                itemListElement: elements,
            };

            var script = document.createElement("script");
            script.type = "application/ld+json";
            script.id = "liber_breadcrumb_jsonld";
            script.text = JSON.stringify(schema);
            document.head.appendChild(script);
        } catch (e) {
            // Never let SEO markup throw on the public site.
            if (window.console && window.console.debug) {
                window.console.debug("Liber breadcrumb schema skipped:", e);
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", buildBreadcrumbSchema);
    } else {
        buildBreadcrumbSchema();
    }
})();
