def post_init_hook(cr, registry):
    cr.execute(
        """
        UPDATE income_statement_budget
        SET company_id = (SELECT id FROM res_company ORDER BY id LIMIT 1)
        WHERE company_id IS NULL
        """
    )
