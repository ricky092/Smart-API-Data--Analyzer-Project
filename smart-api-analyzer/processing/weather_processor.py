"""Weather data processing layer — cleans forecast data and generates insights."""

import pandas as pd

# WMO Weather interpretation codes → human-readable labels
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}


def decode_wmo(code: int) -> str:
    return WMO_CODES.get(int(code), f"Code {code}")


def process_daily(forecast: dict) -> pd.DataFrame:
    daily = forecast.get("daily", {})
    if not daily:
        return pd.DataFrame()

    df = pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "temp_max": daily["temperature_2m_max"],
        "temp_min": daily["temperature_2m_min"],
        "precipitation": daily["precipitation_sum"],
        "wind_max": daily["windspeed_10m_max"],
        "weather_code": daily["weathercode"],
        "uv_index": daily.get("uv_index_max", [None] * 7),
        "rain_chance": daily.get("precipitation_probability_max", [None] * 7),
        "sunrise": daily.get("sunrise", [None] * 7),
        "sunset": daily.get("sunset", [None] * 7),
    })
    df["condition"] = df["weather_code"].apply(decode_wmo)
    df["temp_avg"] = (df["temp_max"] + df["temp_min"]) / 2
    df["day_label"] = df["date"].dt.strftime("%a %b %d")
    return df


def process_hourly(forecast: dict) -> pd.DataFrame:
    hourly = forecast.get("hourly", {})
    if not hourly:
        return pd.DataFrame()

    df = pd.DataFrame({
        "time": pd.to_datetime(hourly["time"]),
        "temperature": hourly["temperature_2m"],
        "humidity": hourly["relativehumidity_2m"],
        "wind": hourly["windspeed_10m"],
        "rain_chance": hourly["precipitation_probability"],
        "weather_code": hourly["weathercode"],
    })
    df["condition"] = df["weather_code"].apply(decode_wmo)
    return df


def process_historical(hist: dict) -> pd.DataFrame:
    daily = hist.get("daily", {})
    if not daily:
        return pd.DataFrame()
    return pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "temp_max": daily["temperature_2m_max"],
        "temp_min": daily["temperature_2m_min"],
        "precipitation": daily["precipitation_sum"],
        "wind_max": daily["windspeed_10m_max"],
    })


def generate_weather_insight(location: dict, daily_df: pd.DataFrame, current: dict) -> str:
    if daily_df.empty:
        return "No forecast data available."

    city = location.get("name", "Unknown")
    country = location.get("country", "")
    temp_now = current.get("temperature", "N/A")
    wind_now = current.get("windspeed", "N/A")

    avg_high = round(daily_df["temp_max"].mean(), 1)
    avg_low = round(daily_df["temp_min"].mean(), 1)
    total_rain = round(daily_df["precipitation"].sum(), 1)
    rainy_days = int((daily_df["precipitation"] > 1).sum())
    hottest_day = daily_df.loc[daily_df["temp_max"].idxmax(), "day_label"]
    coldest_day = daily_df.loc[daily_df["temp_min"].idxmin(), "day_label"]
    max_uv = daily_df["uv_index"].max() if daily_df["uv_index"].notna().any() else None
    dominant_condition = daily_df["condition"].mode()[0]

    lines = [
        f"**{city}, {country}** — 7-day forecast summary.",
        f"Current conditions: **{decode_wmo(current.get('weathercode', 0))}**, "
        f"**{temp_now}°C**, wind at **{wind_now} km/h**.",
        f"This week expects average highs of **{avg_high}°C** and lows of **{avg_low}°C**.",
        f"Dominant condition: **{dominant_condition}**.",
        f"Rainfall expected on **{rainy_days} of 7 days**, totalling **{total_rain} mm**.",
        f"Hottest day: **{hottest_day}** | Coldest day: **{coldest_day}**.",
    ]
    if max_uv is not None:
        uv_label = "extreme" if max_uv >= 11 else "very high" if max_uv >= 8 else "high" if max_uv >= 6 else "moderate"
        lines.append(f"Peak UV index this week: **{max_uv}** ({uv_label}) — {'sunscreen strongly advised' if max_uv >= 6 else 'normal precautions apply'}.")

    return "\n\n".join(lines)
