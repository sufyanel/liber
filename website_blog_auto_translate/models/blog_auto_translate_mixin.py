import logging

from psycopg2.extras import Json

from odoo import api, fields, models, tools
from odoo.tools import SQL

from .. import tools as translate_tools

_logger = logging.getLogger(__name__)

PROVIDER_PARAM = "website_blog_auto_translate.provider"
LIBRE_URL_PARAM = "website_blog_auto_translate.libre_url"


class BlogAutoTranslateMixin(models.AbstractModel):
    """Fills the regular translation columns on demand, at render time.

    Nothing is generated up front: the first visitor asking for a language pays
    for the translation, it lands in the field's own jsonb column, and every
    later request is served from there. Each translated field also keeps a
    digest of the source it was made from, so editing a post makes its
    translations stale and they are produced again on the next visit.
    """

    _name = "blog.auto.translate.mixin"
    _description = "Blog Auto Translation"

    # Translatable fields the auto-translator keeps in sync, set per model.
    _auto_translate_fields = ()

    auto_translate = fields.Boolean(
        default=True,
        help="Machine-translate this record when a visitor browses the website "
             "in another language. Untick it to freeze translations you have "
             "corrected by hand.",
    )
    auto_translate_source = fields.Json(
        readonly=True,
        copy=False,
        help="Digest of the source values the stored machine translations were "
             "made from, per language. A mismatch means the record was edited "
             "and has to be translated again.",
    )

    @api.model
    def _blog_translator(self, source_code, target_code):
        params = self.env["ir.config_parameter"].sudo()
        return translate_tools.build_translator(
            params.get_param(PROVIDER_PARAM, "google"),
            source_code,
            target_code,
            params.get_param(LIBRE_URL_PARAM),
        )

    @api.model
    @tools.ormcache()
    def _translate_supported_languages(self):
        return translate_tools.supported_languages()

    @api.model
    @tools.ormcache("lang_code")
    def _translate_language_code(self, lang_code):
        """Closest language code the translator accepts for an Odoo language."""
        candidate = lang_code.replace("_", "-")
        supported = self._translate_supported_languages()
        if not supported:
            # the library is missing; the caller stops before using this anyway
            return candidate.split("-")[0]
        if candidate in supported:
            return candidate
        base = candidate.split("-")[0]
        return base if base in supported else False

    def _auto_translate(self, fnames=None):
        """Translate the missing or outdated values for the context language.

        :param fnames: restrict the work to these fields, so that rendering a
            title does not pay for a whole ``content`` that is not shown yet.
        """
        records = self.filtered("auto_translate")
        lang = self.env.context.get("lang")
        if not records or not lang:
            return
        source_lang = records[:1]._get_base_lang()
        if lang == source_lang:
            return

        fnames = [
            fname for fname in (fnames or self._auto_translate_fields)
            if fname in self._auto_translate_fields
        ]
        if not fnames:
            return

        helper = self.env["blog.auto.translate.mixin"]
        target_code = helper._translate_language_code(lang)
        source_code = helper._translate_language_code(source_lang)
        if not target_code or not source_code or target_code == source_code:
            _logger.info("No translation available from %s to %s", source_lang, lang)
            return

        pending, text_terms, html_terms = self._auto_translate_pending(
            records, fnames, lang, source_lang
        )
        if not pending:
            return

        translator = helper._blog_translator(source_code, target_code)
        text_translations, html_translations = translate_tools.translate_terms(
            translator, text_terms, html_terms
        )
        if not text_translations and not html_translations:
            return

        self._auto_translate_store(
            pending, lang, source_lang, text_translations, html_translations
        )

    def _auto_translate_pending(self, records, fnames, lang, source_lang):
        """Collect the source values whose translation is missing or stale.

        :return: ``({record id: {fname: source value}}, text terms, html terms)``
        """
        pending, text_terms, html_terms = {}, set(), set()
        for record in records.with_context(lang=source_lang):
            digests = (record.auto_translate_source or {}).get(lang, {})
            todo = {}
            for fname in fnames:
                field = self._fields[fname]
                value = record[fname]
                if not value or digests.get(fname) == translate_tools.source_digest(value):
                    continue
                todo[fname] = value
                terms = html_terms if callable(field.translate) else text_terms
                terms.update(field.get_trans_terms(value))
            if todo:
                pending[record.id] = todo
        return pending, text_terms, html_terms

    def _auto_translate_store(self, pending, lang, source_lang, text_translations,
                              html_translations):
        """Write the translations and refresh the source digests.

        A field is only fingerprinted once every one of its terms came back, so
        a page that was translated in part is finished off on a later visit
        instead of being remembered as done.
        """
        for record in self.browse(list(pending)).sudo().with_context(lang=source_lang):
            # read before writing: update_field_translations invalidates the
            # record, and re-reading per record would be one query each
            digests = dict(record.auto_translate_source or {})
            digested = {}
            for fname, value in pending[record.id].items():
                field = self._fields[fname]
                if callable(field.translate):
                    source_terms = set(field.get_trans_terms(value))
                    terms = {
                        term: html_translations[term]
                        for term in source_terms
                        if html_translations.get(term)
                    }
                    if not terms:
                        continue
                    record.update_field_translations(fname, {lang: terms})
                    if len(terms) < len(source_terms):
                        continue
                else:
                    translation = text_translations.get(value)
                    if not translation:
                        continue
                    record.update_field_translations(fname, {lang: translation})
                digested[fname] = translate_tools.source_digest(value)
            if not digested:
                continue
            digests[lang] = {**digests.get(lang, {}), **digested}
            # written in SQL on purpose: an ORM write would stamp write_uid and
            # write_date with the visitor who happened to trigger the call
            self.env.cr.execute(SQL(
                "UPDATE %s SET auto_translate_source = %s WHERE id = %s",
                SQL.identifier(self._table),
                Json(digests),
                record.id,
            ))
            record.invalidate_recordset(["auto_translate_source"])
