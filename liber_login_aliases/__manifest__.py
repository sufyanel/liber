# -*- coding: utf-8 -*-
{
    'name': 'Liber Login Aliases',
    'summary': 'Sign in with any of a user\'s company email addresses - same user, same password (importable)',
    'description': """
        Lets an administrator give a user alternative login addresses, for example one company mailbox per website
        (dale@mail.globelectric.com, dale@mail.rbcindustrial.com). The address typed is translated into the user's real login on the server only,
        so the real login is never shown in the browser; Odoo then checks the password as usual.
        Data only (no Python), so it installs through Apps > Import Module.
    """,
    'version': '17.0.2.5.0',
    'category': 'Hidden/Tools',
    'author': 'Liber / Axiom World',
    'website': 'https://axiomworld.net',
    'license': 'LGPL-3',
    'depends': ['web', 'website'],
    'data': [
        'data/model.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/login.xml',
        'data/attach_to_site_copies.xml',
        'data/diagnose.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'liber_login_aliases/static/src/js/login_alias.js',
        ],
    },
    'installable': True,
    'application': False,
}
