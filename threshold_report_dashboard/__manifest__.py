{
    "name": "Threshold Report - Dashboard",
    "version": "17.0.1.2.0",
    "category": "Accounting",
    "summary": "Interactive Financial Security Threshold dashboard: KPIs, waterfall, "
               "trends, gain-share and A/P allocation (frontend-importable)",
    "author": "Axiom World",
    "website": "https://axiomworld.net",
    "license": "LGPL-3",
    "depends": ["threshold_report", "threshold_report_ap_import"],
    "data": [
        "data/models.xml",
        "data/defaults.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/server_actions.xml",
        "views/views.xml",
        "data/cron.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "threshold_report_dashboard/static/src/dashboard.css",
            "threshold_report_dashboard/static/src/dashboard.xml",
            "threshold_report_dashboard/static/src/dashboard.js",
        ],
    },
    "installable": True,
    "application": False,
}
