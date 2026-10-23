# -*- coding: utf-8 -*-
{
    'name': 'Liber Login Aliases',
    'summary': 'Sign in with any of a user\'s company email addresses (alternative logins for the same user)',
    'description': """
        Lets an administrator give a user extra login addresses, for example one mailbox per group company
        (dale@mail.globelectric.com, dale@mail.rbcindustrial.com). Each alternative login signs in as the same user
        with the same password. Alternative logins are unique and can never match another user's login.
    """,
    'version': '17.0.1.0.0',
    'category': 'Hidden/Tools',
    'author': 'Liber / Axiom World',
    'website': 'https://axiomworld.net',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
}
