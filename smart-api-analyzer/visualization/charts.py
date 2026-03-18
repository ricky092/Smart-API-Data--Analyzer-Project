"""Visualization layer — all Plotly chart builders with dark/light theme support."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def _template(dark: bool) -> str:
    return "plotly_dark" if dark else "plotly_white"


def _layout(dark: bool, **kwargs) -> dict:
    base = dict(
        template=_template(dark),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=20),
    )
    base.update(kwargs)
    return base


# ── GitHub Charts ─────────────────────────────────────────────────────────────

def language_pie(lang_series: pd.Series, dark: bool = True) -> go.Figure:
    top = lang_series.head(8)
    fig = px.pie(
        values=top.values, names=top.index,
        title="Language Distribution (by byte count)",
        hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold,
        template=_template(dark),
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(**_layout(dark, showlegend=True))
    return fig


def repo_language_bar(lang_series: pd.Series, dark: bool = True) -> go.Figure:
    top = lang_series.head(10)
    fig = px.bar(
        x=top.index, y=top.values,
        labels={"x": "Language", "y": "Repositories"},
        title="Most Used Languages (by repo count)",
        color=top.values, color_continuous_scale="Teal",
        template=_template(dark),
    )
    fig.update_layout(**_layout(dark, coloraxis_showscale=False))
    return fig


def commit_trend(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = px.area(
        df, x="week", y="commits",
        title="Weekly Commit Activity (last 52 weeks)",
        labels={"week": "Week", "commits": "Commits"},
        color_discrete_sequence=["#636EFA"],
        template=_template(dark),
    )
    fig.update_layout(**_layout(dark))
    return fig


def stars_scatter(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = px.scatter(
        df, x="forks_count", y="stargazers_count",
        size="stargazers_count", color="language",
        hover_name="name",
        title="Stars vs Forks by Repository",
        labels={"forks_count": "Forks", "stargazers_count": "Stars"},
        size_max=50, template=_template(dark),
    )
    fig.update_layout(**_layout(dark))
    return fig


def activity_bar(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = px.bar(
        df, x="activity_score", y="name", orientation="h",
        title="Top 10 Repos by Activity Score",
        labels={"activity_score": "Activity Score", "name": "Repository"},
        color="activity_score", color_continuous_scale="Viridis",
        template=_template(dark),
    )
    fig.update_layout(**_layout(dark, yaxis=dict(autorange="reversed"), coloraxis_showscale=False))
    return fig


# ── Weather Charts ────────────────────────────────────────────────────────────

def temperature_range_chart(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = go.Figure([
        go.Bar(name="Max Temp (°C)", x=df["day_label"], y=df["temp_max"], marker_color="#EF553B"),
        go.Bar(name="Min Temp (°C)", x=df["day_label"], y=df["temp_min"], marker_color="#636EFA"),
    ])
    fig.update_layout(
        **_layout(dark),
        barmode="group", title="7-Day Temperature Range",
        xaxis_title="Day", yaxis_title="Temperature (°C)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def precipitation_chart(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=df["day_label"], y=df["precipitation"],
                name="Precipitation (mm)", marker_color="#00CC96")
    if df["rain_chance"].notna().any():
        fig.add_scatter(
            x=df["day_label"], y=df["rain_chance"],
            name="Rain Chance (%)", yaxis="y2",
            mode="lines+markers", line=dict(color="#AB63FA", width=2),
        )
    fig.update_layout(
        **_layout(dark),
        title="Precipitation & Rain Probability",
        yaxis=dict(title="Precipitation (mm)"),
        yaxis2=dict(title="Probability (%)", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def hourly_temperature_chart(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    df48 = df.head(48)
    fig = go.Figure()
    fig.add_scatter(
        x=df48["time"], y=df48["temperature"],
        mode="lines", name="Temp (°C)",
        line=dict(color="#EF553B", width=2),
        fill="tozeroy", fillcolor="rgba(239,85,59,0.1)",
    )
    fig.add_scatter(
        x=df48["time"], y=df48["humidity"],
        mode="lines", name="Humidity (%)", yaxis="y2",
        line=dict(color="#636EFA", width=1.5, dash="dot"),
    )
    fig.update_layout(
        **_layout(dark),
        title="Hourly Temperature & Humidity (Next 48h)",
        xaxis_title="Time",
        yaxis=dict(title="Temperature (°C)"),
        yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def wind_chart(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = px.bar(
        df, x="day_label", y="wind_max",
        title="Max Wind Speed per Day (km/h)",
        labels={"day_label": "Day", "wind_max": "Wind Speed (km/h)"},
        color="wind_max", color_continuous_scale="Blues",
        template=_template(dark),
    )
    fig.update_layout(**_layout(dark, coloraxis_showscale=False))
    return fig


def uv_index_chart(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    colors = []
    for v in df["uv_index"]:
        if v is None:           colors.append("#aaa")
        elif v >= 11:           colors.append("#7B0000")
        elif v >= 8:            colors.append("#E53935")
        elif v >= 6:            colors.append("#FB8C00")
        elif v >= 3:            colors.append("#FDD835")
        else:                   colors.append("#43A047")

    fig = go.Figure(go.Bar(x=df["day_label"], y=df["uv_index"],
                           marker_color=colors, name="UV Index"))
    fig.update_layout(
        **_layout(dark),
        title="UV Index Forecast",
        xaxis_title="Day", yaxis_title="UV Index",
    )
    return fig


def historical_temp_trend(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=df["date"], y=df["temp_max"], mode="lines",
                    name="Max Temp", line=dict(color="#EF553B"))
    fig.add_scatter(x=df["date"], y=df["temp_min"], mode="lines",
                    name="Min Temp", line=dict(color="#636EFA"))
    fig.add_scatter(
        x=pd.concat([df["date"], df["date"][::-1]]),
        y=pd.concat([df["temp_max"], df["temp_min"][::-1]]),
        fill="toself", fillcolor="rgba(99,110,250,0.1)",
        line=dict(color="rgba(255,255,255,0)"), showlegend=False,
    )
    fig.update_layout(
        **_layout(dark),
        title="30-Day Historical Temperature Trend",
        xaxis_title="Date", yaxis_title="Temperature (°C)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
