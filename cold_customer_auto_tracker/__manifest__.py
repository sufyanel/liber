{
    'name': 'Cold Customer Auto Tracker',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Automatically track cold customers based on invoice activity',
    'depends': ['contacts', 'account'],
    'author' : 'Muhammad Ahsan',
    'website' : 'https://theaxiomworld.com/',
    'data': [
        'data/ir_cron.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
