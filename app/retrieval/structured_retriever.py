from __future__ import annotations

from langchain_classic.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.models.response_models import Source
from app.stores.sql_store import SQLStore

# Extra instruction injected into every question so the chain always scopes by client
_CLIENT_HINT = (
    "IMPORTANT: Always filter results with WHERE client_id = '{client_id}'. "
    "Always SELECT * to return full rows, never use bare aggregates. "
    "To find max/min values use ORDER BY ... DESC/ASC with LIMIT 10.\n\n"
    "Question: {question}"
)


class StructuredRetriever:
    """
    Uses LangChain's create_sql_query_chain to translate natural language → SQL,
    executes against SQLite, and returns typed rows with sources.
    """

    def __init__(self, sql_store: SQLStore) -> None:
        self._sql_store = sql_store
        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
        )
        self._db = SQLDatabase.from_uri(
            settings.DATABASE_URL,
            include_tables=["product_specs"],
        )
        self._chain = create_sql_query_chain(self._llm, self._db)

    async def retrieve(
        self, question: str, client_id: str
    ) -> tuple[list[dict], list[Source]]:
        sql = await self._generate_sql(question, client_id)
        rows, sources = self._execute(sql, client_id)
        return rows, sources

    # ── internal ─────────────────────────────────────────────────────────────

    async def _generate_sql(self, question: str, client_id: str) -> str:
        scoped_question = _CLIENT_HINT.format(
            client_id=client_id,
            question=question,
        )
        sql: str = await self._chain.ainvoke({"question": scoped_question})
        sql = self._clean(sql)
        self._guard(sql, client_id)
        return sql

    def _clean(self, sql: str) -> str:
        """Strip markdown fences and chain label prefixes LangChain sometimes leaves in."""
        sql = sql.strip()
        # Strip "SQLQuery:" label the chain prepends
        if sql.lower().startswith("sqlquery:"):
            sql = sql[len("sqlquery:"):].strip()
        for fence in ("```sql", "```"):
            if sql.startswith(fence):
                sql = sql[len(fence):]
            if sql.endswith(fence):
                sql = sql[: -len(fence)]
        return sql.strip().rstrip(";")

    def _guard(self, sql: str, client_id: str) -> None:
        upper = sql.upper()
        for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"):
            if kw in upper:
                raise ValueError(f"Generated SQL contains forbidden keyword: {kw}")
        if client_id.lower() not in sql.lower():
            raise ValueError("Generated SQL missing client_id filter — blocked.")

    def _execute(self, sql: str, client_id: str) -> tuple[list[dict], list[Source]]:
        from sqlalchemy import text

        with self._sql_store.get_session() as session:
            result = session.execute(text(sql))
            keys = list(result.keys())
            rows = [dict(zip(keys, row)) for row in result.fetchall()]

        sources = [
            Source(
                store="sql",
                reference=f"product_specs id={row.get('id', i)}",
                snippet=(
                    f"{row.get('parameter')} = {row.get('numeric_value')} "
                    f"{row.get('unit', '')} [{row.get('region', '')}]"
                ).strip()
                if row.get("parameter")
                else ", ".join(f"{k}={v}" for k, v in row.items() if v is not None),
            )
            for i, row in enumerate(rows)
        ]
        return rows, sources
