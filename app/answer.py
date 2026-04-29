"""
Structured-answer chain on top of the semantic-search retriever.

Pipeline:
  question  →  retrieve top-K chunks  →  format prompt  →  LLM  →  SupportAnswer

OpenAI: uses with_structured_output (native function calling → reliable JSON).
Ollama: uses a concrete JSON template in the prompt — small models understand
        "fill in this template" far better than "follow this schema".
"""

import json
import re
import time
from typing import cast

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.config import settings
from app.llm import get_llm
from app.retriever import get_vector_store


class Citation(BaseModel):
    source: str = Field(description="The file or document the citation is drawn from.")
    excerpt: str = Field(description="A short verbatim excerpt supporting the answer.")


class SupportAnswer(BaseModel):
    summary: str = Field(description="One-paragraph summary of the relevant policy.")
    recommended_response: str = Field(
        description="Empathetic, ready-to-send reply for the support rep to send to the customer."
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sources used. Each citation must reference a document from the provided context.",
    )
    needs_escalation: bool = Field(
        description="True when the case falls outside policy, customer is upset, or rep should not decide alone."
    )
    escalation_reason: str | None = Field(
        default=None,
        description="If needs_escalation is true, a one-line reason. Otherwise null.",
    )


_SYSTEM_BASE = """\
You are an empathetic Nirvana Cloud customer-support assistant helping a human
support representative answer a customer question.

Rules:
1. Use ONLY the provided context. If the context does not cover the case,
   set needs_escalation to true and explain why.
2. Always cite the source document(s) you used.
3. recommended_response is addressed to the customer — polite, clear, concise.
4. If the customer is past a deadline, outside a policy window, or visibly
   upset — set needs_escalation to true.
"""

# OpenAI understands schemas natively via function calling.
_SYSTEM_OPENAI = _SYSTEM_BASE + "Return your answer as a JSON object matching the SupportAnswer schema."

# Small local models respond much better to a concrete filled-in template
# than to an abstract schema description.
_SYSTEM_OLLAMA = _SYSTEM_BASE + """
Respond with ONLY a JSON object in exactly this format — no extra text, no markdown fences:
{
  "summary": "One paragraph summarising the relevant policy.",
  "recommended_response": "The full message to send to the customer.",
  "citations": [
    {"source": "filename.md", "excerpt": "Short verbatim quote from that source."}
  ],
  "needs_escalation": false,
  "escalation_reason": null
}
If escalation is needed set needs_escalation to true and fill in escalation_reason.
"""


def format_context(hits: list[tuple[Document, float]]) -> str:
    blocks: list[str] = []
    for i, (doc, score) in enumerate(hits, start=1):
        metadata: dict[str, object] = doc.metadata  # type: ignore[assignment]
        source = str(metadata.get("source", "unknown"))
        page_content: str = doc.page_content  # type: ignore[assignment]
        text = " ".join(page_content.split())
        blocks.append(f"[{i}] source={source} (score={score:.2f})\n{text}")
    return "\n\n".join(blocks)


def _build_messages(question: str, context: str) -> list[SystemMessage | HumanMessage]:
    system = _SYSTEM_OPENAI if settings.llm_provider == "openai" else _SYSTEM_OLLAMA
    user = f"Customer question / scenario:\n{question}\n\nContext:\n{context}"
    return [SystemMessage(content=system), HumanMessage(content=user)]


def _parse_json(raw: str, hits: list[tuple[Document, float]]) -> SupportAnswer:
    """Extract and validate JSON from a raw LLM string response."""
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

    # Try the whole cleaned string first, then the first {...} block
    for candidate in [cleaned, re.search(r"\{.*\}", cleaned, re.DOTALL)]:
        text = candidate if isinstance(candidate, str) else (candidate.group(0) if candidate else None)
        if not text:
            continue
        try:
            data = cast(object, json.loads(text))
            return SupportAnswer.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            pass

    # Last resort: build a minimal answer from the raw text + retrieved sources
    citations = [
        Citation(
            source=str(doc.metadata.get("source", "unknown")),  # type: ignore[union-attr]
            excerpt=" ".join(doc.page_content.split())[:200],  # type: ignore[union-attr]
        )
        for doc, _ in hits[:3]
    ]
    return SupportAnswer(
        summary=raw[:400].strip(),
        recommended_response=raw.strip(),
        citations=citations,
        needs_escalation=False,
    )


def answer(question: str) -> tuple[SupportAnswer, float]:
    """Run the full retrieve → generate → parse pipeline. Returns (answer, latency_ms)."""
    start = time.perf_counter()

    vector_store = get_vector_store()
    hits: list[tuple[Document, float]] = vector_store.similarity_search_with_score(
        query=question, k=settings.retriever_top_k
    )
    context = format_context(hits)
    messages = _build_messages(question, context)
    llm = get_llm()

    if settings.llm_provider == "openai":
        try:
            result = llm.with_structured_output(SupportAnswer).invoke(messages)
            parsed = result if isinstance(result, SupportAnswer) else SupportAnswer.model_validate(result)
        except Exception:
            raw_msg = llm.invoke(messages)
            raw_text = raw_msg.content if isinstance(raw_msg.content, str) else str(raw_msg.content)
            parsed = _parse_json(raw_text, hits)
    else:
        raw_msg = llm.invoke(messages)
        raw_text = raw_msg.content if isinstance(raw_msg.content, str) else str(raw_msg.content)
        parsed = _parse_json(raw_text, hits)

    latency_ms = (time.perf_counter() - start) * 1000
    return parsed, latency_ms
