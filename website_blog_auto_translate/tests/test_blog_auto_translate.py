import re
from datetime import timedelta
from unittest.mock import patch

from lxml import html as lxml_html

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase

from .. import tools as translate_tools
from ..models import blog_auto_translate_mixin as mixin_module


class FakeTranslator:
    """Stands in for the endpoint: takes packed HTML, gives packed HTML back."""

    def __init__(self, drop_markup=False, answer=None):
        self.payloads = []
        self.drop_markup = drop_markup
        self.answer = answer

    def translate(self, payload):
        self.payloads.append(payload)
        if self.answer is not None:
            return self.answer
        blocks = lxml_html.fromstring("<div>%s</div>" % payload).findall("p")
        out = []
        for block in blocks:
            inner = translate_tools._inner_html(block)
            if self.drop_markup:
                inner = re.sub(r"<[^>]+>", "", inner)
            out.append("<p>[es] %s</p>" % inner)
        return "".join(out)


class TestTranslateTerms(TransactionCase):
    """The packing is what keeps this usable on a free, one-at-a-time endpoint."""

    def test_many_terms_travel_in_one_request(self):
        translator = FakeTranslator()
        terms = {"Ejector Pins", "Return Pins", "Mold Bases"}
        text, html = translate_tools.translate_terms(translator, terms, set())
        self.assertEqual(len(translator.payloads), 1, "one request for all of them")
        self.assertEqual(set(text), terms)
        self.assertEqual(text["Ejector Pins"], "[es] Ejector Pins")
        self.assertFalse(html)

    def test_inline_markup_comes_back_in_place(self):
        translator = FakeTranslator()
        term = "Shoulder <strong>ejector</strong> pins"
        _text, html = translate_tools.translate_terms(translator, set(), {term})
        self.assertEqual(html[term], "[es] Shoulder <strong>ejector</strong> pins")

    def test_a_translation_that_loses_markup_is_refused(self):
        translator = FakeTranslator(drop_markup=True)
        term = "Shoulder <strong>ejector</strong> pins"
        _text, html = translate_tools.translate_terms(translator, set(), {term})
        self.assertFalse(html, "a term that came back without its tags must be dropped")

    def test_a_mismatched_answer_is_refused(self):
        translator = FakeTranslator(answer="<p>only one block</p>")
        text, _html = translate_tools.translate_terms(
            translator, {"Ejector Pins", "Return Pins"}, set()
        )
        self.assertFalse(text)
        self.assertEqual(len(translator.payloads), 2, "it retries once before giving up")

    def test_surrounding_spaces_are_kept(self):
        translator = FakeTranslator()
        term = "  with more than "
        _text, html = translate_tools.translate_terms(translator, set(), {term})
        self.assertTrue(html[term].startswith("  "))
        self.assertTrue(html[term].endswith(" "), "or the next word would stick to it")

    def test_long_pages_are_split_into_several_requests(self):
        translator = FakeTranslator()
        terms = {"term number %03d %s" % (i, "x" * 60) for i in range(40)}
        translate_tools.translate_terms(translator, terms, set())
        self.assertGreater(len(translator.payloads), 1)
        for payload in translator.payloads:
            self.assertLessEqual(len(payload), translate_tools.MAX_CHARS_PER_REQUEST + 400)

    def test_a_render_only_translates_what_its_budget_allows(self):
        translator = FakeTranslator()
        terms = {"term %04d %s" % (i, "y" * 400) for i in range(80)}
        text, _html = translate_tools.translate_terms(translator, terms, set())
        self.assertTrue(text, "it still translates what fits")
        self.assertLess(len(text), len(terms), "and leaves the rest for a later visit")


def fake_translate_terms(translator, text_terms, html_terms):
    """Stand-in for the whole provider call."""
    if not text_terms and not html_terms:
        return {}, {}
    fake_translate_terms.calls.append((sorted(text_terms), sorted(html_terms)))
    return (
        {term: "[es] %s" % term for term in text_terms},
        {term: "[es] %s" % term for term in html_terms},
    )


class TestBlogAutoTranslate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("es_MX")
        cls.blog = cls.env["blog.blog"].create({"name": "Tooling"})
        cls.post = cls.env["blog.post"].create({
            "blog_id": cls.blog.id,
            "name": "Ejector Pins",
            "subtitle": "Alignment and repair",
            "content": "<p>Shoulder pins</p><p>Oversize <b>repair</b></p>",
        })

    def setUp(self):
        super().setUp()
        # _translate_language_code and the language list are ormcached
        self.env.registry.clear_cache()
        fake_translate_terms.calls = []
        patcher = patch.multiple(
            mixin_module.translate_tools,
            build_translator=lambda *args, **kwargs: object(),
            translate_terms=fake_translate_terms,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _translate(self, records=None, **kwargs):
        (records or self.post).with_context(lang="es_MX")._auto_translate(**kwargs)

    def test_translates_char_and_html_fields(self):
        self._translate()
        translated = self.post.with_context(lang="es_MX")
        self.assertEqual(translated.name, "[es] Ejector Pins")
        self.assertEqual(translated.subtitle, "[es] Alignment and repair")
        # the markup has to survive: only the text nodes are replaced
        self.assertIn("<b>", translated.content)
        self.assertIn("[es]", translated.content)
        self.assertEqual(self.post.name, "Ejector Pins", "the source must not change")

    def test_maps_odoo_lang_to_a_code_the_translator_accepts(self):
        # es_MX is not a target the provider knows, es is
        self.assertEqual(self.env["blog.post"]._translate_language_code("es_MX"), "es")
        self.assertEqual(self.env["blog.post"]._translate_language_code("fr_BE"), "fr")
        self.assertFalse(self.env["blog.post"]._translate_language_code("xx_XX"))

    def test_already_translated_records_are_not_sent_again(self):
        self._translate()
        first_pass = len(fake_translate_terms.calls)
        self.assertTrue(first_pass)
        self._translate()
        self.assertEqual(
            len(fake_translate_terms.calls), first_pass,
            "an unchanged post must be served from the stored translation",
        )

    def test_edited_content_is_translated_again(self):
        self._translate()
        fake_translate_terms.calls = []
        self.post.content = "<p>Return pins</p>"
        self._translate()
        self.assertTrue(fake_translate_terms.calls, "an edited post must be re-sent")
        self.assertIn("[es] Return pins", self.post.with_context(lang="es_MX").content)

    def test_a_partly_translated_field_is_finished_later(self):
        def only_the_first_term(translator, text_terms, html_terms):
            fake_translate_terms.calls.append((sorted(text_terms), sorted(html_terms)))
            first = sorted(html_terms)[:1]
            return {}, {term: "[es] %s" % term for term in first}

        with patch.object(mixin_module.translate_tools, "translate_terms",
                          only_the_first_term):
            self._translate(fnames=["content"])
        self.assertFalse(
            (self.post.auto_translate_source or {}).get("es_MX", {}).get("content"),
            "a field that only came back in part must not be recorded as done",
        )
        fake_translate_terms.calls = []
        self._translate(fnames=["content"])
        self.assertTrue(fake_translate_terms.calls, "so the rest is fetched later")
        self.assertTrue(
            (self.post.auto_translate_source or {}).get("es_MX", {}).get("content")
        )

    def test_only_the_requested_fields_are_translated(self):
        self._translate(fnames=["name"])
        translated = self.post.with_context(lang="es_MX")
        self.assertEqual(translated.name, "[es] Ejector Pins")
        self.assertEqual(translated.subtitle, "Alignment and repair")

    def test_source_language_is_left_alone(self):
        self.post.with_context(lang="en_US")._auto_translate()
        self.assertFalse(fake_translate_terms.calls)

    def test_records_opted_out_are_skipped(self):
        self.post.auto_translate = False
        self._translate()
        self.assertFalse(fake_translate_terms.calls)
        self.assertEqual(self.post.with_context(lang="es_MX").name, "Ejector Pins")

    def test_a_failing_provider_keeps_the_source_text(self):
        with patch.object(mixin_module.translate_tools, "translate_terms",
                          lambda *args, **kwargs: ({}, {})):
            self._translate()
        self.assertEqual(self.post.with_context(lang="es_MX").name, "Ejector Pins")
        self.assertFalse(self.post.auto_translate_source,
                         "a failed call must not be recorded as done")
        # and the next visit tries again
        self._translate()
        self.assertEqual(self.post.with_context(lang="es_MX").name, "[es] Ejector Pins")

    def test_translating_does_not_touch_the_audit_fields(self):
        before = (self.post.write_uid, self.post.write_date)
        self._translate()
        self.post.invalidate_recordset()
        self.assertEqual(
            (self.post.write_uid, self.post.write_date), before,
            "a visitor triggering a translation must not show up as last contributor",
        )
        self.assertTrue(self.post.auto_translate_source, "the digest is still stored")

    def test_translates_a_whole_recordset_in_one_batch(self):
        other = self.env["blog.post"].create({
            "blog_id": self.blog.id,
            "name": "Return Pins",
            "content": "<p>Thin wall ejection</p>",
        })
        self._translate(records=self.post | other)
        self.assertEqual(len(fake_translate_terms.calls), 1,
                         "both posts go to the provider together")
        self.assertEqual(other.with_context(lang="es_MX").name, "[es] Return Pins")
        self.assertEqual(self.post.with_context(lang="es_MX").name, "[es] Ejector Pins")


@tagged("post_install", "-at_install")
class TestBlogAutoTranslateRendering(HttpCase):
    """The pages themselves have to come out translated, not just the records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lang = cls.env["res.lang"]._activate_lang("es_MX")
        cls.website = cls.env["website"].search([], limit=1)
        cls.website.language_ids = [(4, cls.lang.id)]
        cls.blog = cls.env["blog.blog"].create({"name": "Tooling", "website_id": False})
        cls.post = cls.env["blog.post"].create({
            "blog_id": cls.blog.id,
            "name": "Ejector Pins",
            "content": "<p>Shoulder pins</p>",
            "is_published": True,
            "post_date": fields.Datetime.now() - timedelta(hours=1),
        })

    def setUp(self):
        super().setUp()
        self.env.registry.clear_cache()
        fake_translate_terms.calls = []
        patcher = patch.multiple(
            mixin_module.translate_tools,
            build_translator=lambda *args, **kwargs: object(),
            translate_terms=fake_translate_terms,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_blog_index_renders_translated(self):
        response = self.url_open("/%s/blog" % self.lang.url_code)
        self.assertEqual(response.status_code, 200)
        self.assertIn("[es] Ejector Pins", response.text)
        self.assertIn("[es] Tooling", response.text, "the blog name too")

    def test_blog_post_renders_translated(self):
        response = self.url_open("/%s%s" % (self.lang.url_code, self.post.website_url))
        self.assertEqual(response.status_code, 200)
        self.assertIn("[es] Ejector Pins", response.text)
        self.assertIn("[es] Shoulder pins", response.text)

    def test_source_language_page_is_untouched(self):
        response = self.url_open(self.post.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ejector Pins", response.text)
        self.assertNotIn("[es]", response.text)
