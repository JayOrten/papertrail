# papertrail

Track academic papers you read. Generates a GitHub-style contribution heatmap and other visualizations for your GitHub profile.

![heatmap example](https://raw.githubusercontent.com/JayOrten/jayorten/main/images/heatmap.svg)

## Setup

Requires Python 3.11+.

### 1. Create a GitHub profile repo (if you don't have one)

A GitHub profile repo is a repo named **exactly** the same as your username (e.g., `yourname/yourname`). GitHub displays its `README.md` on your profile page.

```bash
# Create it on GitHub (via web UI or gh cli), then clone it:
git clone git@github.com:yourname/yourname.git ~/repos/yourname
```

### 2. Install papertrail

```bash
# Recommended: install globally with pipx
pipx install git+https://github.com/JayOrten/papertrail.git

# Or clone and install locally
git clone https://github.com/JayOrten/papertrail.git
cd papertrail
pipx install .
```

### 3. Initialize

```bash
papertrail init
```

This prompts for your GitHub username and the local path to your profile repo. It creates `data/`, `images/`, and copies the GitHub Action workflow + README template into the profile repo.

### 4. Configure the GitHub Action

In your profile repo on GitHub, go to **Settings > Actions > General** and set workflow permissions to **Read and write** so the Action can push generated SVGs.

## Usage

```bash
# Most common: add by ArXiv ID (fetches title, authors automatically)
papertrail add --arxiv 1706.03762
papertrail add --arxiv 2301.07041 --tags rlhf,alignment --rating 5

# Add by DOI
papertrail add --doi 10.1038/s41586-021-03819-2

# Add manually
papertrail add "Paper Title" --authors "Alice, Bob" --tags ml --rating 4

# Browse and search
papertrail list
papertrail list --year 2025 --tag ml
papertrail search "attention"
papertrail stats

# Push to GitHub (triggers Action to regenerate profile)
papertrail sync

# Remove a paper (ID shown in list/search output)
papertrail remove abc123
```

## What gets generated

The GitHub Action runs on every push to `data/papers.json` (and daily at 6am UTC) to produce:

| Visualization | File |
|---|---|
| Contribution heatmap | `images/heatmap.svg` |
| Current/longest streak | `images/streak.svg` |
| Monthly bar chart | `images/monthly.svg` |
| Cumulative line graph | `images/cumulative.svg` |
| Tag cloud | `images/tags.svg` |
| Top authors | `images/authors.svg` |
| Recent papers table | Rendered in `README.md` |

## Commands

| Command | Description |
|---|---|
| `papertrail init` | Configure username, profile repo path, install workflow |
| `papertrail add` | Add a paper (by title, `--arxiv` ID, or `--doi`) |
| `papertrail list` | List papers (`--year`, `--month`, `--tag`, `--rating-min`) |
| `papertrail search "query"` | Search titles, authors, notes, tags |
| `papertrail stats` | Totals, streaks, top tags, top authors |
| `papertrail remove ID` | Remove a paper by ID |
| `papertrail sync` | Commit + push papers.json |

## Development

```bash
git clone https://github.com/JayOrten/papertrail.git
cd papertrail
pip install -e ".[dev]"
pytest
```
