/** @odoo-module **/

import EmbedCodeWidget from "@website/snippets/s_embed_code/000";

EmbedCodeWidget.include({
    start() {
        // Older or manually edited snippets can retain the saved template but
        // lose the live container. Core expects it both here and in destroy(),
        // which runs when entering the website editor or translation mode.
        if (!this.el.querySelector(".s_embed_code_embedded")) {
            const template = this.el.querySelector("template.s_embed_code_saved");
            const container = this.el.ownerDocument.createElement("div");
            container.className = "s_embed_code_embedded container o_not_editable";

            const nodes = [...this.el.childNodes].filter(node => node !== template);
            const hasContent = nodes.some(node =>
                node.nodeType === Node.ELEMENT_NODE ||
                (node.nodeType === Node.TEXT_NODE && node.textContent.trim())
            );
            if (hasContent) {
                // Retain existing content and listeners when only its wrapper
                // is missing, including any already translated text.
                container.append(...nodes);
            } else if (template) {
                const content = template.content.cloneNode(true);
                if (this.editableMode) {
                    content.querySelectorAll("script").forEach(script => script.remove());
                }
                container.append(content);
            }
            this.el.append(container);
        }
        return this._super(...arguments);
    },
});
