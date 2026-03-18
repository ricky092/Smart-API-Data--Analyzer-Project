"""Smart API Data Analyzer — Streamlit entry point."""

import streamlit as st
import time
from datetime import datetime, timedelta

from api.github_client import fetch_user, fetch_repos, fetch_commit_activity, fetch_languages
from api.weather_client import geocode, fetch_forecast, fetch_historical
from processing.data_processor import (
    process_repos, language_breakdown, top_repos,
    activity_score, process_commit_activity, aggregate_languages,
    generate_insight_summary,
)
from processing.weather_processor import (
    process_daily, process_hourly, process_historical,
    generate_weather_insight,
)
from visualization.charts import (
    language_pie, repo_language_bar, commit_trend, stars_scatter, activity_bar,
    temperature_range_chart, precipitation_chart, hourly_temperature_chart,
    wind_chart, uv_index_chart, historical_temp_trend,
)
from utils.cache import ttl_cache, clear_cache

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart API Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme toggle ──────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK_CSS = """
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background-color: #0E1117 !important;
        color: #FAFAFA !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1A1D27 !important;
    }
    [data-testid="stMetric"] {
        background-color: #1A1D27 !important;
        border-radius: 8px;
        padding: 12px;
    }
    .stDataFrame, [data-testid="stTable"] {
        background-color: #1A1D27 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #AAAAAA !important;
    }
    .stTabs [aria-selected="true"] {
        color: #636EFA !important;
        border-bottom: 2px solid #636EFA !important;
    }
    div[data-testid="stExpander"] {
        background-color: #1A1D27 !important;
        border-radius: 8px;
    }
</style>
"""

LIGHT_CSS = """
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background-color: #FFFFFF !important;
        color: #0E1117 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #F0F2F6 !important;
    }
    [data-testid="stMetric"] {
        background-color: #F0F2F6 !important;
        border-radius: 8px;
        padding: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #555555 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #636EFA !important;
        border-bottom: 2px solid #636EFA !important;
    }
    div[data-testid="stExpander"] {
        background-color: #F0F2F6 !important;
        border-radius: 8px;
    }
</style>
"""

st.markdown(DARK_CSS if st.session_state.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# ── Cached API wrappers ───────────────────────────────────────────────────────
@ttl_cache(seconds=300)
def cached_fetch_user(username, token):
    return fetch_user(username, token or None)

@ttl_cache(seconds=300)
def cached_fetch_repos(username, token):
    return fetch_repos(username, token or None)

@ttl_cache(seconds=300)
def cached_fetch_languages(owner, repo, token):
    return fetch_languages(owner, repo, token or None)

@ttl_cache(seconds=300)
def cached_fetch_commits(owner, repo, token):
    return fetch_commit_activity(owner, repo, token or None)

@ttl_cache(seconds=600)
def cached_geocode(city):
    return geocode(city)

@ttl_cache(seconds=600)
def cached_forecast(lat, lon, timezone):
    return fetch_forecast(lat, lon, timezone)

@ttl_cache(seconds=600)
def cached_historical(lat, lon, start, end, timezone):
    return fetch_historical(lat, lon, start, end, timezone)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Smart API Analyzer")

    # Dark / Light toggle
    theme_label = "☀️ Light Mode" if st.session_state.dark_mode else "🌙 Dark Mode"
    if st.button(theme_label, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.divider()

    mode = st.radio("Select Mode", ["🐙 GitHub Analysis", "🌤️ Weather Forecast"], label_visibility="collapsed")
    st.divider()

    if mode == "🐙 GitHub Analysis":
        st.caption("GitHub Profile Intelligence")
        username = st.text_input("GitHub Username", placeholder="e.g. torvalds")
        token = st.text_input("GitHub Token (optional)", type="password",
                              help="Increases rate limit from 60 → 5,000 req/hr")
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True)
    else:
        st.caption("7-Day Forecast · No API key needed")
        city_input = st.text_input("City Name", placeholder="e.g. London, Tokyo, Lagos")
        analyze_btn = st.button("Get Forecast", type="primary", use_container_width=True)

    if st.button("Clear Cache", use_container_width=True):
        clear_cache()
        st.success("Cache cleared.")

    st.divider()
    st.caption("Data cached for 5–10 minutes.")

# ── Main header ───────────────────────────────────────────────────────────────
st.title("Smart API Data Analyzer")
st.caption("Fetch · Process · Visualize · Understand")

# ══════════════════════════════════════════════════════════════════════════════
# GITHUB MODE
# ══════════════════════════════════════════════════════════════════════════════
if mode == "🐙 GitHub Analysis":
    if not analyze_btn or not username.strip():
        st.info("Enter a GitHub username in the sidebar and click **Analyze**.")
        st.stop()

    username = username.strip()

    with st.spinner(f"Fetching GitHub data for **{username}**..."):
        try:
            user = cached_fetch_user(username, token)
            raw_repos = cached_fetch_repos(username, token)
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

    df = process_repos(raw_repos)
    if df.empty:
        st.warning("No original repositories found for this user.")
        st.stop()

    # Profile strip
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Public Repos", user.get("public_repos", 0))
    col2.metric("Followers", user.get("followers", 0))
    col3.metric("Following", user.get("following", 0))
    col4.metric("Total Stars", int(df["stargazers_count"].sum()))
    col5.metric("Total Forks", int(df["forks_count"].sum()))

    with st.expander("Profile Details", expanded=False):
        c1, c2 = st.columns([1, 3])
        if user.get("avatar_url"):
            c1.image(user["avatar_url"], width=120)
        with c2:
            st.markdown(f"### {user.get('name') or username}")
            if user.get("bio"):        st.write(user["bio"])
            if user.get("company"):    st.write(f"🏢 {user['company']}")
            if user.get("location"):   st.write(f"📍 {user['location']}")
            if user.get("blog"):       st.write(f"🔗 {user['blog']}")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🌐 Languages", "📈 Commits", "💡 Insights"])

    with tab1:
        st.subheader("Top Repositories by Stars")
        st.dataframe(top_repos(df), use_container_width=True, hide_index=True)
        st.subheader("Stars vs Forks")
        st.plotly_chart(stars_scatter(df, st.session_state.dark_mode), use_container_width=True)
        st.subheader("Activity Score — Top 10")
        st.plotly_chart(activity_bar(activity_score(df), st.session_state.dark_mode), use_container_width=True)

    with tab2:
        st.subheader("Language Breakdown")
        repo_lang = language_breakdown(df)
        c1, c2 = st.columns(2)
        c1.plotly_chart(repo_language_bar(repo_lang, st.session_state.dark_mode), use_container_width=True)
        with st.spinner("Loading language byte data..."):
            lang_maps = []
            for repo_name in df.nlargest(10, "stargazers_count")["name"].tolist():
                lmap = cached_fetch_languages(username, repo_name, token)
                if lmap:
                    lang_maps.append(lmap)
                time.sleep(0.05)
        if lang_maps:
            c2.plotly_chart(language_pie(aggregate_languages(lang_maps), st.session_state.dark_mode), use_container_width=True)
        else:
            c2.info("No language byte data available.")

    with tab3:
        st.subheader("Commit Activity")
        most_active_repo = df.loc[df["stargazers_count"].idxmax(), "name"]
        selected_repo = st.selectbox(
            "Select repository", options=df["name"].tolist(),
            index=df["name"].tolist().index(most_active_repo),
        )
        with st.spinner("Loading commit history..."):
            raw_commits = cached_fetch_commits(username, selected_repo, token)
        commit_df = process_commit_activity(raw_commits)
        if not commit_df.empty and commit_df["commits"].sum() > 0:
            st.plotly_chart(commit_trend(commit_df, st.session_state.dark_mode), use_container_width=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Commits (52w)", int(commit_df["commits"].sum()))
            m2.metric("Peak Week", commit_df.loc[commit_df["commits"].idxmax(), "week"].strftime("%b %d, %Y"))
            m3.metric("Peak Commits", int(commit_df["commits"].max()))
        else:
            st.info("No commit data available. GitHub may still be computing stats — try again shortly.")

    with tab4:
        st.subheader("AI-Style Insight Summary")
        st.markdown(generate_insight_summary(user, df))
        st.divider()
        st.subheader("Repository Health Overview")
        health_cols = ["name", "language", "stargazers_count", "forks_count", "open_issues_count", "days_since_push"]
        st.dataframe(df[health_cols].sort_values("stargazers_count", ascending=False).head(20),
                     use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# WEATHER MODE
# ══════════════════════════════════════════════════════════════════════════════
else:
    if not analyze_btn or not city_input.strip():
        st.info("Enter a city name in the sidebar and click **Get Forecast**.")
        st.stop()

    city_input = city_input.strip()

    with st.spinner(f"Locating **{city_input}**..."):
        location = cached_geocode(city_input)

    if not location:
        st.error(f"Could not find '{city_input}'. Try a different spelling or a nearby major city.")
        st.stop()

    lat = location["latitude"]
    lon = location["longitude"]
    tz  = location.get("timezone", "auto")
    city_label = f"{location['name']}, {location.get('admin1', '')}, {location.get('country', '')}"

    with st.spinner("Fetching forecast data..."):
        try:
            forecast = cached_forecast(lat, lon, tz)
            end_date   = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            historical = cached_historical(lat, lon, start_date, end_date, tz)
        except Exception as e:
            st.error(f"Failed to fetch weather data: {e}")
            st.stop()

    daily_df   = process_daily(forecast)
    hourly_df  = process_hourly(forecast)
    hist_df    = process_historical(historical)
    current    = forecast.get("current_weather", {})

    # Current conditions strip
    st.subheader(f"📍 {city_label}")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Temperature", f"{current.get('temperature', 'N/A')}°C")
    m2.metric("Wind Speed",  f"{current.get('windspeed', 'N/A')} km/h")
    m3.metric("7-Day High",  f"{daily_df['temp_max'].max():.1f}°C")
    m4.metric("7-Day Low",   f"{daily_df['temp_min'].min():.1f}°C")
    m5.metric("Total Rain",  f"{daily_df['precipitation'].sum():.1f} mm")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Forecast", "🌧️ Precipitation", "💨 Wind & UV", "💡 Insights"])

    with tab1:
        st.subheader("7-Day Temperature Forecast")
        st.plotly_chart(temperature_range_chart(daily_df, st.session_state.dark_mode), use_container_width=True)

        st.subheader("Hourly Temperature & Humidity")
        st.plotly_chart(hourly_temperature_chart(hourly_df, st.session_state.dark_mode), use_container_width=True)

        if not hist_df.empty:
            st.subheader("30-Day Historical Trend")
            st.plotly_chart(historical_temp_trend(hist_df, st.session_state.dark_mode), use_container_width=True)

    with tab2:
        st.subheader("Precipitation Forecast")
        st.plotly_chart(precipitation_chart(daily_df, st.session_state.dark_mode), use_container_width=True)

        st.subheader("Daily Breakdown")
        display_cols = ["day_label", "condition", "temp_max", "temp_min", "precipitation", "rain_chance"]
        st.dataframe(
            daily_df[display_cols].rename(columns={
                "day_label": "Day", "condition": "Condition",
                "temp_max": "High (°C)", "temp_min": "Low (°C)",
                "precipitation": "Rain (mm)", "rain_chance": "Rain Chance (%)",
            }),
            use_container_width=True, hide_index=True,
        )

    with tab3:
        c1, c2 = st.columns(2)
        c1.plotly_chart(wind_chart(daily_df, st.session_state.dark_mode), use_container_width=True)
        if daily_df["uv_index"].notna().any():
            c2.plotly_chart(uv_index_chart(daily_df, st.session_state.dark_mode), use_container_width=True)
        else:
            c2.info("UV index data not available for this location.")

        st.subheader("Sunrise & Sunset")
        sun_cols = ["day_label", "sunrise", "sunset"]
        st.dataframe(
            daily_df[sun_cols].rename(columns={"day_label": "Day", "sunrise": "Sunrise", "sunset": "Sunset"}),
            use_container_width=True, hide_index=True,
        )

    with tab4:
        st.subheader("Weather Insight Summary")
        st.markdown(generate_weather_insight(location, daily_df, current))
