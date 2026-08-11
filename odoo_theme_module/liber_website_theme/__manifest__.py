{
    'name': 'Liber Website Theme',
    'description': 'Custom B2B/industrial website theme for Liber Holdings — SCSS variables, blog template overrides, and custom snippets for ToolingComponents and RBC Industrial.',
    'category': 'Website/Theme',
    'version': '17.0.1.0.0',
    'author': 'Liber Holdings',
    'license': 'LGPL-3',
    'depends': ['website', 'website_blog'],
    'data': [
        'views/blog_list_template.xml',
        'views/blog_post_template.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'liber_website_theme/static/src/scss/primary_variables.scss',
        ],
        'web._assets_frontend_helpers': [
            'liber_website_theme/static/src/scss/bootstrap_overridden.scss',
        ],
        'web.assets_frontend': [
            'liber_website_theme/static/src/scss/_typography.scss',
            'liber_website_theme/static/src/scss/_blog.scss',
            'liber_website_theme/static/src/scss/_components.scss',
            'liber_website_theme/static/src/scss/style.scss',
            'liber_website_theme/static/src/js/theme.js',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
