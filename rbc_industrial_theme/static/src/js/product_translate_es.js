/** @odoo-module */
// Translates product descriptions to Spanish (Mexico) from the admin's browser.
// Text is sent to Google's public translate endpoint, and only the Spanish version
// of each field is saved (English is never changed). Spanish text that already
// differs from English (e.g. reviewed by hand) is left untouched.
import { registry } from "@web/core/registry";

const LANG = "es_MX";
const GLOSSARY = [
    [/\bcojinetes\b/g, "rodamientos"], [/\bCojinetes\b/g, "Rodamientos"], [/\bcojinete\b/g, "rodamiento"], [/\bCojinete\b/g, "Rodamiento"],
    [/\bbloques de almohada\b/gi, "chumaceras"], [/\bbloque de almohada\b/gi, "chumacera"],
    [/\bpasadores eyectores\b/gi, "botadores"], [/\bpines eyectores\b/gi, "botadores"], [/\bpasador eyector\b/gi, "botador"],
    [/\bresortes de matriz\b/gi, "resortes para troquel"], [/\bjuegos de matrices\b/gi, "portatroqueles"],
    [/\bseguidores de leva\b/gi, "rodillos de leva"], [/\bcomponentes del molde\b/gi, "componentes de molde"],
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cache = new Map();

function decodeEntities(text) {
    const el = document.createElement("textarea");
    el.innerHTML = String(text || "");
    return el.value;
}

// Translation services, tried in order. If one fails (network block, throttling, outage) the next is used,
// and the one that works is remembered for the rest of the run.
const SERVICES = [
    (q) => ["https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + encodeURIComponent(q),
            (d) => (d && d[0] || []).map((part) => part[0]).join("")],
    (q) => ["https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl=es&q=" + encodeURIComponent(q),
            (d) => Array.isArray(d) ? (Array.isArray(d[0]) ? d[0][0] : d[0]) : (d && d.sentences || []).map((x) => x.trans).join("")],
];
let preferredService = 0;

async function callServices(q) {
    for (let round = 0; round < 3; round++) {
        for (let k = 0; k < SERVICES.length; k++) {
            const idx = (preferredService + k) % SERVICES.length;
            const [url, parse] = SERVICES[idx](q);
            try {
                const resp = await fetch(url);
                if (!resp.ok) { continue; }                       // busy / refused: try the next service
                const out = parse(await resp.json());
                if (out) { preferredService = idx; return out; }
            } catch (e) {
                // network error or throttling (browsers report both as "Failed to fetch"): next service
            }
        }
        await sleep(2000 * Math.pow(2, round));                    // all services refused: wait 2s, 4s, 8s
    }
    throw new Error("BLOCKED");
}

// split long text at sentence ends so every request stays small (some services limit request size)
function chunks(text, max) {
    if (text.length <= max) { return [text]; }
    const parts = text.match(/[^.!?]+[.!?]+\s*|[^.!?]+$/g) || [text];
    const out = [];
    let cur = "";
    for (const part of parts) {
        if ((cur + part).length > max && cur) { out.push(cur); cur = ""; }
        cur += part;
    }
    if (cur) { out.push(cur); }
    return out;
}

async function translateText(text) {
    text = decodeEntities(text);   // "&mdash;" stored as text becomes a real dash
    const t = (text || "").trim();
    if (!t || !/[A-Za-z]{3}/.test(t)) { return text; }
    if (cache.has(t)) { return cache.get(t); }
    const pieces = [];
    for (const piece of chunks(t, 450)) {
        pieces.push(await callServices(piece));
        await sleep(600);                                          // gentle pace: avoids being throttled
    }
    let out = pieces.join(" ").replace(/\s+/g, " ").trim() || t;
    for (const [re, rep] of GLOSSARY) { out = out.replace(re, rep); }
    cache.set(t, out);
    return out;
}

async function translateHtml(html) {
    const doc = new DOMParser().parseFromString("<div id='x'>" + html + "</div>", "text/html");
    const root = doc.getElementById("x");
    const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) { if (/[A-Za-z]{3}/.test(walker.currentNode.nodeValue)) { nodes.push(walker.currentNode); } }
    for (const n of nodes) {
        const lead = n.nodeValue.match(/^\s*/)[0], trail = n.nodeValue.match(/\s*$/)[0];
        n.nodeValue = lead + (await translateText(n.nodeValue)) + trail;
    }
    return root.innerHTML;
}

// Product names are often part numbers ("6205-2RS1", "XH04-010"): translate a name only when it reads as words.
function isProse(text) {
    const words = String(text || "").split(/\s+/).filter((w) => /^[A-Za-z][a-z]{2,}[,.]?$/.test(w));
    return words.length >= 2;
}
// Attribute values / names / categories: skip numbers, sizes and codes ("3/8", "25 mm", "2RS").
function isWordy(text) {
    const t = String(text || "").trim();
    return /[A-Za-z]{3}/.test(t) && !/\d/.test(t);
}

async function translateRecords(orm, model, ids, fields, htmlFields, filters, onProgress) {
    filters = filters || {};
    let blockedRun = 0;
    let seen = 0;
    let done = 0, failed = 0;
    for (const id of ids) {
        try {
            const [en] = await orm.read(model, [id], fields, { context: { lang: "en_US" } });
            const [es] = await orm.read(model, [id], fields, { context: { lang: LANG } });
            const vals = {};
            let changed = false;
            for (const f of fields) {
                if (!(en[f] && en[f] === es[f])) { continue; }          // missing, or Spanish already differs (reviewed)
                if (filters[f] && !filters[f](en[f])) { continue; }     // e.g. a part-number product name
                if (htmlFields.includes(f)) {
                    // formatted fields are stored phrase by phrase: translate Odoo's own phrases
                    // and save them as the Spanish translation only (English stays as it is)
                    const res = await orm.call(model, "get_field_translations", [[id], f], { langs: [LANG] });
                    const terms = (res && res[0]) || [];
                    const mapping = {};
                    for (const term of terms) {
                        if (term.source && (!term.value || term.value === term.source)) {
                            mapping[term.source] = await translateHtml(term.source);
                        }
                    }
                    if (Object.keys(mapping).length) {
                        await orm.call(model, "update_field_translations", [[id], f, { [LANG]: mapping }]);
                        changed = true;
                    }
                } else {
                    vals[f] = await translateText(en[f]);
                }
            }
            if (Object.keys(vals).length) {
                await orm.write(model, [id], vals, { context: { lang: LANG } });
                changed = true;
            }
            blockedRun = 0;
            if (changed) { done++; }
            seen++;
            if (onProgress && seen % 10 === 0) { onProgress(seen, ids.length); }
        } catch (e) {
            failed++;
            console.warn("Spanish translation skipped for", model, id, e);
            if (String(e).includes("BLOCKED")) {
                blockedRun++;
                if (blockedRun >= 3) { throw new Error("BLOCKED"); }   // 3 in a row: the browser really cannot reach any service
                continue;
            }
        }
    }
    return { done, failed };
}

async function translateBlogPosts(env, ids) {
    const orm = env.services.orm;
    const notify = env.services.notification;
    const f = await orm.call("blog.post", "fields_get", [], { attributes: ["type"] });
    const fields = ["name", "subtitle", "content", "website_meta_title", "website_meta_description", "website_meta_keywords"].filter((x) => f[x]);
    const htmlFields = fields.filter((x) => f[x].type === "html");
    notify.add("Translating " + ids.length + " blog post(s) to Spanish... keep this tab open.", { type: "info" });
    try {
        const progress = (n, total) => notify.add("Translated " + n + " of " + total + " blog posts...", { type: "info" });
        const p = await translateRecords(orm, "blog.post", ids, fields, htmlFields, {}, progress);
        const posts = await orm.read("blog.post", ids, ["tag_ids", "blog_id"]);
        const tagIds = [...new Set(posts.flatMap((r) => r.tag_ids))];
        const blogIds = [...new Set(posts.map((r) => r.blog_id && r.blog_id[0]).filter(Boolean))];
        const tg = await translateRecords(orm, "blog.tag", tagIds, ["name"], [], { name: isWordy });
        const bl = await translateRecords(orm, "blog.blog", blogIds, ["name", "subtitle"].filter((x) => x), [], {});
        const failed = p.failed + tg.failed + bl.failed;
        notify.add(p.done + " blog post(s) and " + tg.done + " tag(s) translated" + (failed ? ", " + failed + " skipped (run again later)" : "") + ".",
                   { type: failed ? "warning" : "success", sticky: true });
    } catch (e) {
        notify.add(String(e).includes("BLOCKED")
            ? "Could not reach Google Translate. Usually Google is limiting requests for a while: wait 15-30 minutes and run Translate ALL again - it continues where it stopped. If it persists, try another network or turn off ad-blocking extensions for this page."
            : String(e), { type: "danger", sticky: true });
    }
}

async function runTranslation(env, action) {
    const params = action.params || {};
    if (params.all) {
        // "Translate ALL": every record, on every website, whatever is selected or filtered in the list
        const domain = params.model === "blog.post" ? [] : [["sale_ok", "=", true]];
        params.ids = await env.services.orm.search(params.model === "blog.post" ? "blog.post" : "product.template", domain,
                                                   { context: { active_test: false } });
    }
    if (params.model === "blog.post") {
        return translateBlogPosts(env, params.ids || []);
    }
    const orm = env.services.orm;
    const notify = env.services.notification;
    const ids = params.ids || [];
    if (!ids.length) { return; }
    const langs = await orm.searchRead("res.lang", [["code", "=", LANG], ["active", "=", true]], ["id"]);
    if (!langs.length) { notify.add("Activate Spanish (Mexico) first: Settings > Languages.", { type: "warning" }); return; }
    const tmplFields = await orm.call("product.template", "fields_get", [], { attributes: ["type"] });
    // everything a product shows on the website
    const fields = ["name", "description_sale", "description_ecommerce",
                    "website_meta_title", "website_meta_description", "website_meta_keywords"].filter((f) => tmplFields[f]);
    const htmlFields = fields.filter((f) => tmplFields[f].type === "html");
    notify.add("Translating " + ids.length + " product(s) to Spanish... keep this tab open.", { type: "info" });
    try {
        const progress = (n, total) => notify.add("Translated " + n + " of " + total + " products...", { type: "info" });
        const t = await translateRecords(orm, "product.template", ids, fields, htmlFields, { name: isProse }, progress);
        let v = { done: 0, failed: 0 };
        const varFields = await orm.call("product.product", "fields_get", [], { attributes: ["type"] });
        if (varFields.x_variant_description) {
            const variantIds = await orm.search("product.product", [["product_tmpl_id", "in", ids]]);
            v = await translateRecords(orm, "product.product", variantIds, ["x_variant_description"], []);
        }
        // attribute names and values used by these products (spec table, variant picker, filters)
        const lines = await orm.searchRead("product.template.attribute.line", [["product_tmpl_id", "in", ids]], ["attribute_id", "value_ids"]);
        const attrIds = [...new Set(lines.map((l) => l.attribute_id[0]))];
        const valueIds = [...new Set(lines.flatMap((l) => l.value_ids))];
        const at = await translateRecords(orm, "product.attribute", attrIds, ["name"], [], { name: isWordy });
        const av = await translateRecords(orm, "product.attribute.value", valueIds, ["name"], [], { name: isWordy });
        // website categories of these products
        let c = { done: 0, failed: 0 };
        if (tmplFields.public_categ_ids) {
            const prods = await orm.read("product.template", ids, ["public_categ_ids"]);
            const catIds = [...new Set(prods.flatMap((r) => r.public_categ_ids))];
            c = await translateRecords(orm, "product.public.category", catIds, ["name"], [], { name: isWordy });
        }
        const failed = t.failed + v.failed + at.failed + av.failed + c.failed;
        notify.add(t.done + " product(s), " + v.done + " variant(s), " + (at.done + av.done) + " attribute name(s)/value(s) and " + c.done +
                   " categor" + (c.done === 1 ? "y" : "ies") + " translated" + (failed ? ", " + failed + " skipped (run again later)" : "") + ".",
                   { type: failed ? "warning" : "success", sticky: true });
    } catch (e) {
        notify.add(String(e).includes("BLOCKED")
            ? "Could not reach Google Translate. Usually Google is limiting requests for a while: wait 15-30 minutes and run Translate ALL again - it continues where it stopped. If it persists, try another network or turn off ad-blocking extensions for this page."
            : String(e), { type: "danger", sticky: true });
    }
}

// own action name, so an older separate translator module can never shadow this one
if (!registry.category("actions").contains("rbc_tc_translate_es")) {
    registry.category("actions").add("rbc_tc_translate_es", runTranslation);
}
