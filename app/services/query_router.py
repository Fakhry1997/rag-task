from __future__ import annotations

import re
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

RouteType = Literal["structured", "semantic", "hybrid"]

_SYSTEM_PROMPT = """You are a query routing assistant for a document retrieval system.

The system has two data stores:
1. **SQL (structured)** — product specification tables with columns:
   product_name, region, parameter, numeric_value, unit, limit_type, notes.
   Use this for questions about specific numbers, limits, thresholds, or comparisons.

2. **Vector (semantic)** — narrative regulatory/product brief text chunks.
   Use this for questions about explanations, context, policies, or descriptions.

Respond with EXACTLY one word — no punctuation, no explanation:
- "structured"  → answer requires querying the SQL table
- "semantic"    → answer requires reading narrative text
- "hybrid"      → answer needs both structured numbers AND textual context
"""

_STRUCTURED_KEYWORDS = {
    "value", "limit", "threshold", "maximum", "minimum", "how much",
    "how many", "what is the", "numeric", "number", "g/l", "%", "unit",
    "compare", "difference between", "higher", "lower",
}

_SEMANTIC_KEYWORDS = {
    "explain", "why", "what does", "describe", "tell me about",
    "what is", "how does", "policy", "regulation", "brief", "context",
    "overview", "what kind",
}


class QueryRouter:
    """
    Classifies a question as structured / semantic / hybrid using Gemini.
    Falls back to keyword heuristics if the LLM call fails.
    """

    def __init__(self) -> None:
        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
        )

    async def route(self, question: str) -> RouteType:
        # Fast path: keywords give a confident signal — no LLM call needed
        keyword_result = self._keyword_route(question)
        if keyword_result is not None:
            return keyword_result

        # Ambiguous — use LLM as tiebreaker
        try:
            response = await self._llm.ainvoke(
                [
                    ("system", _SYSTEM_PROMPT),
                    ("human", question),
                ]
            )
            label = re.sub(r"[^a-z]", "", response.content.strip().lower())
            if label in ("structured", "semantic", "hybrid"):
                return label  # type: ignore[return-value]
        except Exception:
            pass

        # Default fallback
        return "hybrid"

    def _keyword_route(self, question: str) -> RouteType | None:
        """
        Returns a route if keywords give a clear unambiguous signal, else None.
        Avoids an LLM call for the majority of questions.
        """
        q = question.lower()
        has_structured = any(kw in q for kw in _STRUCTURED_KEYWORDS)
        has_semantic = any(kw in q for kw in _SEMANTIC_KEYWORDS)

        if has_structured and not has_semantic:
            return "structured"
        if has_semantic and not has_structured:
            return "semantic"
        if has_structured and has_semantic:
            return "hybrid"
        # No signal — let LLM decide
        return None
