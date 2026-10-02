import logging
import re

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

TARGET = "es_MX"
# Site vocabulary enforced after machine translation (Mexican industrial trade terms)
GLOSSARY = [
    (r"\bcojinetes\b", "rodamientos"), (r"\bCojinetes\b", "Rodamientos"),
    (r"\bcojinete\b", "rodamiento"), (r"\bCojinete\b", "Rodamiento"),
    (r"\bbloques de almohada\b", "chumaceras"), (r"\bbloque de almohada\b", "chumacera"),
    (r"\bpasadores eyectores\b", "botadores"), (r"\bpines eyectores\b", "botadores"),
    (r"\bpasador eyector\b", "botador"), (r"\bresortes de matriz\b", "resortes para troquel"),
    (r"\bjuegos de matrices\b", "portatroqueles"), (r"\bseguidores de leva\b", "rodillos de leva"),
    (r"\bcomponentes del molde\b", "componentes de molde"),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_es_auto_translated = fields.Boolean("Spanish auto-translated", copy=False,
        help="Set when the Spanish descriptions were produced automatically. "
             "Spanish text you edit yourself is never overwritten.")

    @api.model
    def _pat_translator(self):
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="es")

    @api.model
    def _pat_apply_glossary(self, text):
        for pattern, repl in GLOSSARY:
            text = re.sub(pattern, repl, text)
        return text

    @api.model
    def _pat_translate(self, translator, text):
        text = (text or "").strip()
        if not text or not re.search(r"[A-Za-z]{3}", text):
            return text
        out = translator.translate(text[:4800]) or text
        return self._pat_apply_glossary(out)

    def _pat_translate_one(self, translator):
        """Translate only fields whose Spanish value is still identical to English."""
        self.ensure_one()
        en = self.with_context(lang="en_US")
        es = self.with_context(lang=TARGET)
        done = False
        if en.description_sale and es.description_sale == en.description_sale:
            self.update_field_translations("description_sale", {TARGET: self._pat_translate(translator, en.description_sale)})
            done = True
        field = self._fields["description_ecommerce"]
        if en.description_ecommerce and callable(field.translate):
            terms = field.get_trans_terms(en.description_ecommerce)
            if terms and terms == field.get_trans_terms(es.description_ecommerce or ""):
                self.update_field_translations("description_ecommerce",
                                               {TARGET: {t: self._pat_translate(translator, t) for t in terms}})
                done = True
        if "seo_description" in self._fields and en.seo_description and es.seo_description == en.seo_description:
            self.update_field_translations("seo_description", {TARGET: self._pat_translate(translator, en.seo_description)})
            done = True
        if done:
            self.x_es_auto_translated = True
        return done

    @api.model
    def _cron_translate_descriptions(self, limit=150):
        if not self.env["res.lang"].search([("code", "=", TARGET), ("active", "=", True)], limit=1):
            return
        try:
            translator = self._pat_translator()
        except Exception as e:
            _logger.warning("Product auto-translate skipped: %s", e)
            return
        count = 0
        for product in self.search([("is_published", "=", True), ("sale_ok", "=", True)], order="write_date desc"):
            if count >= limit:
                break
            try:
                if product._pat_translate_one(translator):
                    count += 1
                    self.env.cr.commit()
            except Exception as e:
                _logger.warning("Product %s not translated: %s", product.display_name, e)
        _logger.info("Product auto-translate: %s products translated to %s", count, TARGET)

    def action_translate_to_spanish(self):
        translator = self._pat_translator()
        n = sum(1 for p in self if p._pat_translate_one(translator))
        return {"type": "ir.actions.client", "tag": "display_notification",
                "params": {"title": "Spanish translation", "message": "%s product(s) translated." % n, "type": "success"}}
