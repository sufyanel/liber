def migrate(cr, version):
    cr.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'income_statement_budget'
          AND column_name = 'year'
        """
    )
    row = cr.fetchone()
    if not row:
        return
    pg_type = row[0]
    if pg_type in ("character varying", "text"):
        return
    if pg_type in ("timestamp without time zone", "timestamp with time zone"):
        cr.execute(
            """
            ALTER TABLE income_statement_budget
            ALTER COLUMN year TYPE varchar
            USING EXTRACT(YEAR FROM year)::text
            """
        )
        return
    if pg_type in ("integer", "bigint", "smallint"):
        cr.execute(
            """
            ALTER TABLE income_statement_budget
            ALTER COLUMN year TYPE varchar
            USING year::text
            """
        )
