from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestEmbedCode(HttpCase):
    def test_embed_code_editor_lifecycle(self):
        self.browser_js(
            "/",
            r"""
            (async () => {
                await odoo.loader.modules.get('@web/core/l10n/translation').translationIsReady;
                const EmbedCodeWidget = odoo.loader.modules.get(
                    '@website/snippets/s_embed_code/000'
                )[Symbol.for('default')];
                const check = (condition, message) => {
                    if (!condition) {
                        throw new Error(message);
                    }
                };
                const mount = async (html, editableMode = false) => {
                    const snippet = document.createElement('section');
                    snippet.className = 's_embed_code';
                    snippet.innerHTML = html;
                    document.body.append(snippet);
                    const widget = new EmbedCodeWidget(null);
                    widget.editableMode = editableMode;
                    await widget.attachTo(snippet);
                    return {snippet, widget};
                };

                // Regression: RBC's contact form has a saved template only.
                // Core start succeeds but destroy used to call replaceChildren
                // on null as soon as the editor stopped the public widgets.
                const {snippet, widget} = await mount(`
                    <template class="s_embed_code_saved">
                        <div><iframe title="Contact Us" src="about:blank"></iframe>
                        <script type="application/json">{"form": "contact"}</script></div>
                    </template>
                `);
                const saved = snippet.querySelector('template');
                const savedHTML = saved.innerHTML;
                check(snippet.querySelector('.s_embed_code_embedded iframe'),
                    'The missing contact form container must be restored');
                check(snippet.querySelector('.s_embed_code_embedded script'),
                    'Visitor mode must retain the embed scripts');
                widget.destroy();
                check(snippet.querySelector('.s_embed_code_embedded iframe'),
                    'Entering the editor must preserve the contact form');
                check(!snippet.querySelector('.s_embed_code_embedded script'),
                    'Core cleanup must still remove scripts from the live embed');
                check(saved.innerHTML === savedHTML,
                    'Saved source, including scripts, must remain unchanged');
                const editorWidget = new EmbedCodeWidget(null);
                editorWidget.editableMode = true;
                await editorWidget.attachTo(snippet);
                editorWidget.destroy();
                check(snippet.querySelectorAll('.s_embed_code_embedded').length === 1,
                    'Repeated editor initialization must not duplicate containers');
                snippet.remove();

                // A valid snippet must keep its live DOM and translation text.
                const valid = await mount(`
                    <template class="s_embed_code_saved"><p>Original</p></template>
                    <div class="s_embed_code_embedded"><p>Traducido</p></div>
                `, true);
                check(valid.snippet.querySelector('p').textContent === 'Traducido',
                    'Valid translated content must not be overwritten');
                valid.widget.destroy();
                valid.snippet.remove();

                // Legacy unwrapped content must survive, even without a template.
                const legacy = await mount('<p>Existing contact details</p>');
                check(legacy.snippet.querySelector('.s_embed_code_embedded p'),
                    'Unwrapped content must be retained');
                check(legacy.snippet.querySelector('template').content.querySelector('p'),
                    'Core must still create the saved template for legacy content');
                legacy.widget.destroy();
                legacy.snippet.remove();

                // Recovering directly in edit mode must never run embed scripts.
                const editing = await mount(`
                    <template class="s_embed_code_saved">
                        <p>Contact Us</p><script>throw new Error('Embed script ran');</script>
                    </template>
                `, true);
                check(!editing.snippet.querySelector('.s_embed_code_embedded script'),
                    'Recovery in edit mode must omit scripts');
                check(editing.snippet.querySelector('template').content.querySelector('script'),
                    'Edit mode must retain scripts in the saved template');
                editing.widget.destroy();
                editing.snippet.remove();

                const empty = await mount('', true);
                check(empty.snippet.querySelector('.s_embed_code_placeholder'),
                    'Empty snippets must retain the standard editor placeholder');
                empty.widget.destroy();
                empty.snippet.remove();
                console.log('test successful');
            })().catch(error => { console.error(error); });
            """,
            ready="odoo.loader.modules.has('@liber_website_customizations/js/embed_code')",
        )
