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
    if pg_type not in ("integer", "bigint", "smallint"):
        return
    cr.execute(
        """
        ALTER TABLE income_statement_budget
        ALTER COLUMN year TYPE timestamp without time zone
        USING CASE
            WHEN year IS NOT NULL
            THEN to_timestamp(year::text || '-01-01', 'YYYY-MM-DD')
            ELSE NULL
        END
        """
    )
