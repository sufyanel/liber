{
    "name": "Mass mailing SMTP throttling and ESP defaults",
    "version": "17.0.1.0.0",
    "category": "Marketing/Email",
    "author": "Liber",
    "license": "LGPL-3",
    "depends": ["mass_mailing", "mail"],
    "data": [
        "data/ir_cron_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "summary": "Throttle outgoing mail batches, tighten mail crons, surface ESP and DNS guidance for mass mailings.",
}
