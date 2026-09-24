# Liber Website Customizations

## Website translation editor fix

An Embed Code snippet must have a `.s_embed_code_embedded` container alongside
its `template.s_embed_code_saved`. The RBC Industrial homepage contained only
the saved contact-form template. Odoo's widget then failed in `destroy()` with
`Cannot read properties of null (reading 'replaceChildren')` when entering the
website editor or translation mode.

The frontend extension repairs missing containers before the standard widget
starts. It preserves existing unwrapped content or recovers the saved template
when no live content remains. Valid snippets are left intact, and Odoo still
removes embed scripts during editor cleanup while keeping their saved source.

Deploy this module and upgrade `liber_website_customizations` in the target
database, then reload the website to load the updated frontend assets:

```sh
odoo-bin -c /path/to/odoo.conf -d DATABASE -u liber_website_customizations --stop-after-init
```

Restart the Odoo service after the upgrade. Open the affected website, switch
to Spanish, enter translation mode, change a label, save, and reopen the page
to verify the translation and contact form.

Run the browser regression test on a test database:

The test requires Chrome/Chromium and the Python `websocket-client` package.

```sh
odoo-bin -c /path/to/odoo.conf -d TEST_DATABASE -u liber_website_customizations \
    --test-enable --test-tags /liber_website_customizations --stop-after-init
```
