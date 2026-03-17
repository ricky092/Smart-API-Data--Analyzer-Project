"""Data processing layer — cleans raw API data and computes insights."""

import pandas as pd
from datetime import datetime, timezone


def process_repos(raw_repos: list[dict]) -> pd.DataFrame:
    if not raw_repos:
        return pd.DataFrame()

    fields = [
        "name", "description", "language", "stargazers_count",
        "forks_count", "open_issues_count", "size", "created_at",
        "updated_at", "pushed_at", "fork", "topics",
    ]
    df = pd.DataFrame(raw_repos)[fields]
    df = df[df["fork"] == False].copy()  # exclude forks for cleaner analysis

    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df["updated_at"] = pd.to_datetime(df["updated_at"], utc=True)
    df["pushed_at"] = pd.to_datetime(df["pushed_at"], utc=True)
    df["description"] = df["description"].fillna("No description")
    df["language"] = df["language"].fillna("Unknown")
    df["topics"] = df["topics"].apply(lambda x: x if isinstance(x, list) else [])

    now = datetime.now(timezone.utc)
    df["days_since_push"] = (now - df["pushed_at"]).dt.days

    return df.reset_index(drop=True)


def language_breakdown(df: pd.DataFrame) -> pd.Series:
    return df["language"].value_counts()


def top_repos(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return df.nlargest(n, "stargazers_count")[
        ["name", "language", "stargazers_count", "forks_count", "description"]
    ]


def activity_score(df: pd.DataFrame) -> pd.DataFrame:
    """Composite score: stars + forks*2 - staleness penalty."""
    df = df.copy()
    df["activity_score"] = (
        df["stargazers_count"]
        + df["forks_count"] * 2
        - (df["days_since_push"] / 30).clip(upper=12)
    )
    return df.nlargest(10, "activity_score")[["name", "activity_score", "stargazers_count", "forks_count", "days_since_push"]]


def process_commit_activity(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    rows = []
    for week in raw:
        dt = datetime.fromtimestamp(week["week"], tz=timezone.utc)
        rows.append({"week": dt, "commits": week["total"]})
    return pd.DataFrame(rows)


def aggregate_languages(lang_maps: list[dict]) -> pd.Series:
    """Merge language byte counts across multiple repos."""
    combined: dict = {}
    for lmap in lang_maps:
        for lang, bytes_ in lmap.items():
            combined[lang] = combined.get(lang, 0) + bytes_
    return pd.Series(combined).sort_values(ascending=False)


def generate_insight_summary(user: dict, df: pd.DataFrame) -> str:
    if df.empty:
        return "No repository data available to analyze."

    total = len(df)
    top_lang = df["language"].value_counts().idxmax() if total else "N/A"
    total_stars = int(df["stargazers_count"].sum())
    total_forks = int(df["forks_count"].sum())
    most_starred = df.loc[df["stargazers_count"].idxmax(), "name"] if total else "N/A"
    active_repos = int((df["days_since_push"] <= 30).sum())
    avg_stars = round(df["stargazers_count"].mean(), 1)

    lines = [
        f"**{user.get('name') or user.get('login')}** has {total} original repositories on GitHub.",
        f"Their most-used language is **{top_lang}**, reflecting a clear technical focus.",
        f"Across all repos, they've accumulated **{total_stars} stars** and **{total_forks} forks**.",
        f"The most starred project is **{most_starred}** — a standout in their portfolio.",
        f"**{active_repos}** repos were pushed to in the last 30 days, showing {'strong' if active_repos > 3 else 'moderate'} recent activity.",
        f"Average stars per repo: **{avg_stars}** — {'above average for open source' if avg_stars > 10 else 'typical for personal projects'}.",
    ]
    return "\n\n".join(lines)
