from __future__ import annotations

import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from papertrail.config import (
    get_papers_path,
    get_profile_repo_path,
    load_config,
    save_config,
)
from papertrail.store import Paper, PaperStore

app = typer.Typer(
    help="Track academic papers you read and visualize them on your GitHub profile.",
    epilog="Config: ~/.config/papertrail/config.toml | Run 'papertrail init' to get started.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()


def _store() -> PaperStore:
    return PaperStore(get_papers_path())


@app.command()
def init() -> None:
    """Set up config: GitHub username, profile repo path, and copy workflow files."""
    config = load_config()
    username = typer.prompt(
        "GitHub username", default=config.get("github_username", "")
    )
    default_repo = config.get(
        "profile_repo_path", str(Path.home() / "repos" / username)
    )
    repo_path = typer.prompt("Profile repo path", default=default_repo)
    save_config(
        {"github_username": username, "profile_repo_path": repo_path}
    )
    repo = Path(repo_path)
    if not repo.exists():
        typer.confirm(
            f"Repo directory {repo} does not exist. Create it?", abort=True
        )
        repo.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=repo, check=True)

    # Ensure data directory exists
    (repo / "data").mkdir(exist_ok=True)
    (repo / "images").mkdir(exist_ok=True)

    # Copy workflow + template if not present
    _install_profile_files(repo)

    console.print(f"[green]Configured.[/green] Repo: {repo}")


def _install_profile_files(repo: Path) -> None:
    """Copy GitHub Action and template files into the profile repo."""
    src = Path(__file__).parent.parent / "profile"
    workflow_dir = repo / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Copy workflow
    src_workflow = Path(__file__).parent.parent / ".github" / "workflows" / "generate.yml"
    if src_workflow.exists():
        (workflow_dir / "generate.yml").write_text(src_workflow.read_text())

    # Copy template
    template_dir = repo / "profile"
    template_dir.mkdir(exist_ok=True)
    if src.exists():
        for f in src.iterdir():
            dest = template_dir / f.name
            if not dest.exists():
                dest.write_text(f.read_text())

    # Copy generate.py to repo root for convenience
    gen_src = src / "generate.py" if src.exists() else None
    if gen_src and gen_src.exists():
        dest = repo / "profile" / "generate.py"
        dest.write_text(gen_src.read_text())


@app.command()
def add(
    title: Optional[str] = typer.Argument(None),
    authors: Optional[str] = typer.Option(None, help="Comma-separated authors"),
    url: Optional[str] = typer.Option(None),
    tags: Optional[str] = typer.Option(None, help="Comma-separated tags"),
    rating: Optional[int] = typer.Option(None, min=1, max=5),
    notes: Optional[str] = typer.Option(None),
    date_read: Optional[str] = typer.Option(None, "--date", help="ISO date (YYYY-MM-DD)"),
    arxiv_id: Optional[str] = typer.Option(None, "--arxiv", help="ArXiv paper ID"),
    doi: Optional[str] = typer.Option(None, "--doi", help="DOI identifier"),
) -> None:
    """Add a paper manually, from ArXiv, or from DOI.

    [dim]Examples:[/dim]
      papertrail add "Attention Is All You Need" --tags nlp --rating 5
      papertrail add --arxiv 1706.03762
      papertrail add --doi 10.1038/s41586-021-03819-2
    """
    store = _store()

    if arxiv_id:
        from papertrail.fetchers import fetch_arxiv

        paper = fetch_arxiv(arxiv_id)
    elif doi:
        from papertrail.fetchers import fetch_doi

        paper = fetch_doi(doi)
    elif title:
        paper = Paper(
            title=title,
            authors=[a.strip() for a in authors.split(",")] if authors else [],
            url=url,
            tags=[t.strip() for t in tags.split(",")] if tags else [],
            rating=rating,
            notes=notes,
            date_read=date_read or date.today().isoformat(),
            source="manual",
        )
    else:
        raise typer.BadParameter("Provide a title, --arxiv ID, or --doi.")

    # Apply overrides from flags for fetched papers
    if arxiv_id or doi:
        if tags:
            paper.tags = [t.strip() for t in tags.split(",")]
        if rating is not None:
            paper.rating = rating
        if notes:
            paper.notes = notes
        if date_read:
            paper.date_read = date_read

    store.add(paper)
    console.print(f"[green]Added:[/green] {paper.title} [{paper.id}]")


@app.command("list")
def list_papers(
    year: Optional[int] = typer.Option(None),
    month: Optional[int] = typer.Option(None),
    tag: Optional[str] = typer.Option(None),
    rating_min: Optional[int] = typer.Option(None, "--rating-min"),
) -> None:
    """List papers, optionally filtered by year, month, tag, or minimum rating."""
    papers = _store().load()

    if year:
        papers = [p for p in papers if p.date_read.startswith(str(year))]
    if month and year:
        prefix = f"{year}-{month:02d}"
        papers = [p for p in papers if p.date_read.startswith(prefix)]
    if tag:
        papers = [p for p in papers if tag.lower() in [t.lower() for t in p.tags]]
    if rating_min is not None:
        papers = [p for p in papers if p.rating and p.rating >= rating_min]

    if not papers:
        console.print("No papers found.")
        return

    table = Table(title="Papers")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Date")
    table.add_column("Title", max_width=50)
    table.add_column("Rating")
    table.add_column("Tags")

    for p in sorted(papers, key=lambda x: x.date_read, reverse=True):
        stars = ("*" * p.rating) if p.rating else ""
        table.add_row(p.id, p.date_read, p.title, stars, ", ".join(p.tags))

    console.print(table)


@app.command()
def search(query: str) -> None:
    """Search papers by title, authors, notes, or tags."""
    papers = _store().load()
    q = query.lower()
    matches = []
    for p in papers:
        searchable = " ".join(
            [p.title, " ".join(p.authors), p.notes or "", " ".join(p.tags)]
        ).lower()
        if q in searchable:
            matches.append(p)

    if not matches:
        console.print("No matches.")
        return

    table = Table(title=f'Search: "{query}"')
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Date")
    table.add_column("Title", max_width=50)
    table.add_column("Authors", max_width=30)

    for p in matches:
        table.add_row(
            p.id, p.date_read, p.title, ", ".join(p.authors[:3])
        )

    console.print(table)


@app.command()
def stats() -> None:
    """Show reading stats: totals, streaks, top tags, top authors."""
    papers = _store().load()
    if not papers:
        console.print("No papers yet.")
        return

    today = date.today()
    this_year = [p for p in papers if p.date_read.startswith(str(today.year))]

    # Streak calculation
    dates_read = sorted({p.date_read for p in papers}, reverse=True)
    current_streak = 0
    check = today
    for _ in range(len(dates_read) + 1):
        if check.isoformat() in dates_read:
            current_streak += 1
            check -= timedelta(days=1)
        elif check == today:
            # Today might not have a paper yet, check yesterday
            check -= timedelta(days=1)
        else:
            break

    # Longest streak
    all_dates = sorted({date.fromisoformat(d) for d in dates_read})
    longest = 0
    run = 1
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i - 1]).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run) if all_dates else 0

    # Top tags
    tag_counts: dict[str, int] = {}
    for p in papers:
        for t in p.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Top authors
    author_counts: dict[str, int] = {}
    for p in papers:
        for a in p.authors:
            author_counts[a] = author_counts.get(a, 0) + 1
    top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    console.print(f"[bold]Total papers:[/bold] {len(papers)}")
    console.print(f"[bold]This year:[/bold] {len(this_year)}")
    console.print(f"[bold]Current streak:[/bold] {current_streak} days")
    console.print(f"[bold]Longest streak:[/bold] {longest} days")
    if top_tags:
        console.print(
            f"[bold]Top tags:[/bold] "
            + ", ".join(f"{t} ({c})" for t, c in top_tags)
        )
    if top_authors:
        console.print(
            f"[bold]Top authors:[/bold] "
            + ", ".join(f"{a} ({c})" for a, c in top_authors)
        )


@app.command()
def remove(paper_id: str) -> None:
    """Remove a paper by its ID (shown in 'list' and 'search' output)."""
    store = _store()
    paper = store.find(paper_id)
    if not paper:
        console.print(f"[red]No paper found with ID: {paper_id}[/red]")
        raise typer.Exit(1)

    console.print(f"Paper: {paper.title} ({paper.date_read})")
    typer.confirm("Remove this paper?", abort=True)

    store.remove(paper_id)
    console.print("[green]Removed.[/green]")


@app.command()
def sync() -> None:
    """Commit and push papers.json to your GitHub profile repo."""
    repo = get_profile_repo_path()
    papers_path = get_papers_path()

    if not papers_path.exists():
        console.print("[red]No papers.json found.[/red]")
        raise typer.Exit(1)

    subprocess.run(
        ["git", "add", "data/papers.json"],
        cwd=repo,
        check=True,
    )

    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo,
    )
    if result.returncode == 0:
        console.print("Nothing to sync — papers.json unchanged.")
        return

    subprocess.run(
        ["git", "commit", "-m", "Update papers.json"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "push"], cwd=repo, check=True)
    console.print("[green]Synced.[/green]")


if __name__ == "__main__":
    app()
