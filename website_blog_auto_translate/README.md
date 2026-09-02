# Website Blog Auto Translate

Translates website blog content on the fly when a visitor switches the site
language, and translates it again whenever an author edits it.

**Free.** No account, no API key, no paid service: translation goes through
[`deep-translator`](https://pypi.org/project/deep-translator/) against the
public Google endpoint it wraps. A self-hosted LibreTranslate instance can be
used instead if you want a provider with no rate limit at all.

## How it works

Nothing is generated in advance. When a blog page is about to be rendered in a
language other than `en_US`, the controller asks the records on that page for
their translation:

1. Every translatable field is fingerprinted (SHA-1 of the source value) and
   compared with the fingerprint stored on the record for that language.
2. Fields with no fingerprint, or with one that no longer matches, are collected
   across the whole page, deduplicated, and sent to the translator.
3. The answers are written into Odoo's own translation columns with
   `update_field_translations`, and the new fingerprints are stored.

Because the translation lands in the regular translation columns, the website
renders it with no template change, and you can correct any of it afterwards
from the standard Odoo translation dialog.

### Why the terms are packed into `<p>` blocks

The free endpoint takes its text in a **GET query string** and answers **one
request at a time**. Sent naively that is one HTTP round trip per sentence —
hundreds for a single page. So terms are packed into one request as
`<p>term</p><p>term</p>…`: the block boundaries survive translation and give an
unambiguous way to split the answer back apart. Measured on real posts, a whole
blog post travels in about two requests instead of twenty-five.

Two guards keep that safe:

* if the answer does not contain exactly as many blocks as were sent, the whole
  batch is discarded and the source text is kept;
* if a translated term does not carry exactly the same tags as its source, that
  term is discarded. Markup can never be corrupted, only left untranslated.

### Limits, and what happens when they bite

| Constant (`tools.py`) | Value | Why |
| --- | --- | --- |
| `MAX_CHARS_PER_REQUEST` | 2000 | Measured: at 2000 chars 10/10 requests came back complete, at 3000 only 6/10, at 3800 only 4/10. Past that the query string is too long and the endpoint answers with nothing. |
| `MAX_CHARS_PER_RENDER` | 8000 | How much one page render may translate, at a measured ~1500 chars/second — so about 5 seconds worst case. Raise for completeness, lower for speed. |

Titles and subtitles are sent **before** bodies, so every headline on a listing
is translated first and the budget is spent on bodies with what is left. What
does not fit keeps its source text and is picked up on a later visit, so a busy
listing converges over a few views rather than making one visitor wait for all
of it.

A field is only fingerprinted once **every** one of its terms came back, so a
page translated in part is finished off later instead of being remembered as
done.

## Translated records and fields

| Record | Fields |
| --- | --- |
| `blog.post` | `name`, `subtitle`, `content`, `website_meta_title`, `website_meta_description`, `website_meta_keywords` |
| `blog.blog` | `name`, `subtitle`, `content`, `website_meta_title`, `website_meta_description`, `website_meta_keywords` |
| `blog.tag` | `name` |
| `blog.tag.category` | `name` |

## Requirements

```
pip install deep-translator
```

That is all. No key, no account.

## Configuration

**Website → Configuration → Settings → Blog Translation**:

* **Provider** — *Google (free, no account)* is the default and needs nothing.
  *LibreTranslate (self-hosted)* is there for when you would rather not depend
  on a public endpoint; it needs the URL of your own instance.
* Add the languages you want to serve under **Website Info → Languages**.

Odoo language codes are mapped to the closest code the provider accepts, from
the library's own offline list — `es_MX` is sent as `es`, `zh_CN` stays
`zh-CN`. A language the provider does not know is skipped and logged.

## Freezing a translation

Untick **Auto Translate** on a blog post or blog (form view, or the optional
column in the Blog Posts list for a bulk change) and the module stops
overwriting it, which is what you want after correcting a translation by hand.
Editing one field only invalidates that field, so a title you fixed is not lost
when somebody edits the body.

## What it does not disturb

The fingerprints are written in SQL rather than through `write()`, so a visitor
who happens to trigger a translation never ends up stamped on the post as
*Last Contributor*, and *Last Updated on* keeps showing the real last edit.
`update_field_translations` writes the translations the same way, so the source
language values are never rewritten either.

## Behaviour when the provider is unavailable

The public endpoint is generous but not contractual: it throttles, and it
occasionally answers with nothing. Every failure is logged at INFO and the page
renders in its source language. A batch is retried once immediately, and since
no fingerprint is stored for a field that did not come back whole, the next
visit tries again. Nothing ever raises out of a page render.

If throttling becomes a habit, switch the provider to a LibreTranslate instance
of your own — same module, one setting.

## Tests

```
odoo-bin -c config/liber.cfg -d <db> -u website_blog_auto_translate \
         --test-enable --test-tags /website_blog_auto_translate --stop-after-init
```

The suite stubs the provider, so it runs without network.
