"""Free machine translation through `deep-translator`.

No account and no API key: the default provider is the public Google endpoint
that `deep-translator` wraps. That endpoint is generous but not contractual, so
everything here is written to degrade instead of fail — a refused request means
the page renders in its source language and is translated on a later visit.

Two properties of that endpoint shape the code:

* it takes the text in a GET query string, so an oversized request comes back
  empty rather than translated;
* it answers one request at a time, so sending one term per request would mean
  hundreds of round trips for a single page.

Both are solved by packing many terms into one request as ``<p>`` blocks: the
block boundaries survive translation and give an unambiguous way to split the
answer back apart.
"""

import hashlib
import html
import logging
import re

from lxml import etree
from lxml import html as lxml_html

_logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator, LibreTranslator
except ImportError:
    GoogleTranslator = LibreTranslator = None
    _logger.info(
        "`deep-translator` is not installed, blog auto-translation is disabled"
    )

# Measured against real posts: at 2000 characters a request 10 out of 10 came
# back complete, at 3000 only 6 and at 3800 only 4 -- past that size the query
# string gets too long and the endpoint answers with nothing at all.
MAX_CHARS_PER_REQUEST = 2000

# How much one page render may translate, at a measured ~1500 characters per
# second. Whatever does not fit keeps its source text and is picked up on a
# later visit, which bounds both the time a visitor waits (~5s worst case) and
# how hard a free endpoint is hit. Raise it for completeness, lower it for
# speed.
MAX_CHARS_PER_RENDER = 8000

# A term holding a block tag would break the <p> packing, so it goes alone.
BLOCK_TAG = re.compile(
    r"<\s*(p|div|section|ul|ol|li|h[1-6]|table|tr|td|blockquote)\b", re.I
)

PROVIDERS = ("google", "libre")


def source_digest(value):
    """Fingerprint of a source value, used to detect an edited record.

    Not a security primitive: it only answers "did this text change since we
    translated it", so the digest is declared as such rather than reached for
    as a hash of record.
    """
    return hashlib.sha1(value.encode(), usedforsecurity=False).hexdigest()


def supported_languages():
    """Language codes the provider accepts, as a frozenset. Read offline."""
    if GoogleTranslator is None:
        return frozenset()
    return frozenset(GoogleTranslator().get_supported_languages(as_dict=True).values())


def build_translator(provider, source, target, libre_url=None):
    """Build a deep-translator instance, or ``None`` if it cannot be built."""
    if GoogleTranslator is None:
        return None
    try:
        if provider == "libre":
            return LibreTranslator(
                source=source, target=target, custom_url=libre_url or None
            )
        return GoogleTranslator(source=source, target=target)
    except Exception:
        _logger.exception("Cannot build a %s translator", provider)
        return None


def _inner_html(element):
    """Serialize the content of an element, without the element itself."""
    return (element.text or "") + "".join(
        etree.tostring(child, encoding="unicode", method="html") for child in element
    )


def _tag_signature(fragment):
    """Tags found in an HTML fragment, or ``None`` if it does not parse."""
    try:
        root = lxml_html.fromstring("<div>%s</div>" % fragment)
    except (etree.ParserError, etree.XMLSyntaxError, ValueError):
        return None
    return sorted(element.tag for element in root.iter() if element is not root)


def _chunks(work):
    """Group ``(term, is_html)`` pairs into request-sized batches."""
    batch, size = [], 0
    for item in work:
        length = len(item[0]) + 7  # the <p></p> wrapper
        if batch and size + length > MAX_CHARS_PER_REQUEST:
            yield batch
            batch, size = [], 0
        batch.append(item)
        size += length
    if batch:
        yield batch


def _send(translator, batch):
    """Translate one batch, returning the answers in order or ``None``."""
    payload = "".join(
        "<p>%s</p>" % (term if is_html else html.escape(term))
        for term, is_html in batch
    )
    try:
        answer = translator.translate(payload)
    except Exception as error:
        _logger.info("Translation request refused (%s), keeping the source text", error)
        return None
    if not answer:
        return None
    try:
        blocks = lxml_html.fromstring("<div>%s</div>" % answer).findall("p")
    except (etree.ParserError, etree.XMLSyntaxError, ValueError):
        return None
    if len(blocks) != len(batch):
        _logger.info(
            "Translator returned %s block(s) for %s term(s), keeping the source text",
            len(blocks), len(batch),
        )
        return None
    return blocks


def translate_terms(translator, text_terms, html_terms):
    """Translate what fits in one render budget.

    Char and Text values are sent first: they are the short, most visible
    strings on a page. A term the provider refused, mangled, or that did not fit
    in the budget is simply absent from the result, so the caller keeps its
    source text and tries again on the next visit.

    :return: ``(text translations, html translations)``, both ``{term: value}``
    """
    text_result, html_result = {}, {}
    if not translator:
        return text_result, html_result

    work, budget = [], MAX_CHARS_PER_RENDER
    for terms, is_html in ((sorted(text_terms), False), (sorted(html_terms), True)):
        for term in terms:
            if len(term) > budget:
                continue
            budget -= len(term)
            work.append((term, is_html))

    for batch in _chunks(work):
        blocks = _send(translator, batch)
        if blocks is None:
            blocks = _send(translator, batch)  # the endpoint is flaky, try once more
        if blocks is None:
            continue
        for (term, is_html), block in zip(batch, blocks):
            translation = _inner_html(block) if is_html else block.text_content()
            if not translation.strip():
                continue
            if is_html and _tag_signature(translation) != _tag_signature(term):
                _logger.info("Translation changed the markup of a term, keeping it as is")
                continue
            # the provider trims, but the surrounding spaces belong to the text
            translation = "%s%s%s" % (
                term[:len(term) - len(term.lstrip())],
                translation.strip(),
                term[len(term.rstrip()):],
            )
            (html_result if is_html else text_result)[term] = translation
    return text_result, html_result
