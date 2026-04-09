def post_init_hook(env):
    icp = env["ir.config_parameter"].sudo()
    defaults = {
        "mail.mail.queue.batch.size": "40",
        "mail.session.batch.size": "50",
        "mail.batch_size": "40",
        "mail.mail.force.send.limit": "80",
    }
    for key, value in defaults.items():
        if not icp.search_count([("key", "=", key)]):
            icp.set_param(key, value)
