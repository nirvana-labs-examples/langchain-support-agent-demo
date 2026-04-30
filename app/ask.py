"""
Interactive CLI for grounded answers over the support knowledge base.

  python -m app.ask                                # interactive REPL
  python -m app.ask "A customer wants a refund..." # one-shot

Uses the configured LLM (ollama by default, optionally OpenAI) to generate a
structured `SupportAnswer` from retrieved context.
"""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from app.answer import LatencyBreakdown, SupportAnswer, answer
from app.config import settings
from app.llm import llm_label
from app.retriever import get_vector_store

console = Console()


def _fmt_error(e: Exception) -> str:
    msg = str(e)
    if "Connection refused" in msg or "ConnectError" in msg:
        return (
            f"Cannot reach the LLM ({llm_label()}).\n"
            "If using Ollama: run [bold]docker compose up -d[/bold] and "
            "[bold]docker compose exec ollama ollama pull llama3.2:3b[/bold]"
        )
    return f"LLM error: {msg}"


def render(result: SupportAnswer, latency: LatencyBreakdown) -> None:
    console.print()
    console.print(Panel(result.summary, title="[bold]Policy summary[/bold]", border_style="cyan"))
    console.print(
        Panel(
            result.recommended_response,
            title="[bold]Recommended response[/bold]",
            border_style="green",
        )
    )

    if result.citations:
        cite_text = Text()
        for i, c in enumerate(result.citations, start=1):
            _ = cite_text.append(f"  {i}. ", style="bold cyan")
            _ = cite_text.append(f"{c.source}\n", style="yellow")
            excerpt = c.excerpt.strip().replace("\n", " ")
            if len(excerpt) > 200:
                excerpt = excerpt[:197] + "..."
            _ = cite_text.append(f"     {excerpt}\n", style="dim")
        console.print(Panel(cite_text, title="[bold]Citations[/bold]", border_style="yellow"))

    if result.needs_escalation:
        reason = result.escalation_reason or "(no reason provided)"
        console.print(Panel(f"[bold red]ESCALATE[/bold red] — {reason}", border_style="red"))
    else:
        console.print("[dim]No escalation needed.[/dim]")

    timing = (
        f"embed [cyan]{latency.embed_ms:.0f}ms[/cyan] · "
        f"search [cyan]{latency.search_ms:.0f}ms[/cyan] · "
        f"generate [cyan]{latency.generate_ms:.0f}ms[/cyan] · "
        f"total [cyan]{latency.total_ms:.0f}ms[/cyan]"
    )
    console.print(f"\n[dim]{timing} · {llm_label()}[/dim]\n")


def warm_up() -> None:
    console.print("[dim]Loading embedding model and LLM...[/dim]")
    _ = get_vector_store()
    console.print(
        f"[dim]Ready. Embeddings: {settings.embedding_model} · LLM: {llm_label()}[/dim]\n"
    )


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        if not question:
            console.print("[red]Empty question.[/red]")
            return
        warm_up()
        console.print(f"[bold green]>[/bold green] {question}")
        try:
            result, latency = answer(question)
        except Exception as e:
            console.print(f"[red]{_fmt_error(e)}[/red]")
            return
        render(result, latency)
        return

    console.print(
        "[bold magenta]Nirvana Support Ask[/bold magenta] — type a question, Ctrl+C or Ctrl+D to exit\n"
    )
    warm_up()

    while True:
        try:
            question = console.input("[bold green]>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            return

        if not question:
            continue

        try:
            result, latency = answer(question)
        except Exception as e:
            console.print(f"[red]{_fmt_error(e)}[/red]")
            continue

        render(result, latency)


if __name__ == "__main__":
    main()
