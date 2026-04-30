"""
Interactive CLI for semantic search over the support knowledge base.

Run:
  python -m app.search
"""

import time
import textwrap

from langchain_core.documents import Document
from rich.console import Console

from app.config import settings
from app.retriever import get_embeddings, get_qdrant_client, search_by_vector

console = Console()


def format_excerpt(text: str, width: int = 70, max_lines: int = 4) -> str:
    """Wrap and truncate a chunk for clean display."""
    text = " ".join(text.split())  # collapse whitespace
    wrapped = textwrap.wrap(text, width=width)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(".") + "..."
    return "\n     ".join(wrapped)


def print_results(_query: str, hits: list[tuple[Document, float]], embed_ms: float, search_ms: float, _top_k: int) -> None:
    n = len(hits)
    timing = f"embed [cyan]{embed_ms:.0f}ms[/cyan] · search [cyan]{search_ms:.0f}ms[/cyan] · total [cyan]{embed_ms + search_ms:.0f}ms[/cyan]"
    console.print(f"\n  [bold]Results ({n})[/bold]  [dim]{timing}[/dim]\n")
    for i, (doc, score) in enumerate(hits, start=1):
        metadata: dict[str, object] = doc.metadata  # type: ignore[assignment]
        source = str(metadata.get("source", "unknown"))
        ticket_id = metadata.get("ticket_id")
        label = f"{source} ({ticket_id})" if ticket_id else source
        console.print(f"  [bold cyan]{i}.[/bold cyan] [yellow]{label:<48}[/yellow] score [green]{score:.2f}[/green]")
        page_content: str = doc.page_content  # type: ignore[assignment]
        console.print(f"     [dim]{format_excerpt(page_content)}[/dim]\n")


def main():
    console.print("[bold magenta]Nirvana Support Search[/bold magenta] — type a question, Ctrl+C or Ctrl+D to exit\n")
    console.print("[dim]Loading embedding model and connecting to Qdrant...[/dim]")
    _ = get_embeddings()
    _ = get_qdrant_client()
    console.print(
        f"[dim]Ready. Model: {settings.embedding_model} ({settings.embedding_dimensions} dims).[/dim]\n"
    )

    while True:
        try:
            query = console.input("[bold green]>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            return

        if not query:
            continue

        t0 = time.perf_counter()
        vec = get_embeddings().embed_query(query)
        embed_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        hits = search_by_vector(vec, settings.retriever_top_k)
        search_ms = (time.perf_counter() - t1) * 1000

        print_results(query, hits, embed_ms, search_ms, settings.retriever_top_k)


if __name__ == "__main__":
    main()
