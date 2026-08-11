/** @odoo-module */
// Liber Website Theme — Custom JavaScript
// Add interactive features for the industrial B2B site

import publicWidget from '@web/legacy/js/public/public_widget';

// ==== Blog: Smooth scroll to content on cover image click ====
// selector/events target real website_blog markup:
// - '#o_wblog_post_top' is the cover's own section (only exists on the post
//   detail page, so the widget only attaches there).
// - '.o_record_cover_image' is the actual background-image div rendered by
//   website.record_cover (there is no <img> and no '.o_blog_cover_image').
// - '#o_wblog_post_main' (the content section) is a SIBLING of the cover
//   section, not a descendant, so it can't be reached via this.el.querySelector
//   — it has to be looked up from the document.
publicWidget.registry.liberBlogScroll = publicWidget.Widget.extend({
    selector: '#o_wblog_post_top',
    events: {
        'click .o_record_cover_image': '_onCoverClick',
    },

    _onCoverClick: function (ev) {
        const content = document.querySelector('#o_wblog_post_main');
        if (content) {
            content.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    },
});

// ==== Reading Progress Indicator ====
publicWidget.registry.liberReadingProgress = publicWidget.Widget.extend({
    // '#o_wblog_post_main' only exists on the post detail page.
    selector: '#o_wblog_post_main',
    start: function () {
        this._progressBar = document.createElement('div');
        this._progressBar.className = 'liber-reading-progress';
        this._progressBar.style.cssText =
            'position:fixed;top:0;left:0;height:3px;background:#1a3c5e;z-index:9999;transition:width 0.1s ease;';
        document.body.prepend(this._progressBar);
        this._onScroll = this._updateProgress.bind(this);
        window.addEventListener('scroll', this._onScroll, { passive: true });
    },

    _updateProgress: function () {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight > 0) {
            this._progressBar.style.width = Math.min(100, (scrollTop / docHeight) * 100) + '%';
        }
    },

    destroy: function () {
        if (this._progressBar) this._progressBar.remove();
        if (this._onScroll) window.removeEventListener('scroll', this._onScroll);
        this._super.apply(this, arguments);
    },
});

export default publicWidget.registry;
