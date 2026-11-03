"""
Group 7: Real-time Weather Forecasts & Web Search.
- Open-Meteo API for real-time weather forecasts and daily outlook (TL-13).
- DuckDuckGo web search with result attribution and prompt isolation (TL-04, TL-13).
"""

import logging
import urllib.parse

import requests
from bs4 import BeautifulSoup

import config
from tools.policy import ToolResult, wrap_untrusted

log = logging.getLogger("teo.search")

_session = requests.Session()

WMO_WEATHER_CODES = {
    0: "trời quang mây tạnh",
    1: "ít mây",
    2: "có mây rải rác",
    3: "nhiều mây âm u",
    45: "có sương mù",
    48: "sương mù dày",
    51: "mưa phùn nhẹ",
    53: "mưa phùn vừa",
    55: "mưa phùn dày",
    56: "mưa phùn lạnh",
    57: "mưa phùn lạnh dày",
    61: "mưa nhỏ",
    63: "mưa vừa",
    65: "mưa to",
    66: "mưa lạnh",
    67: "mưa lạnh nặng hạt",
    71: "tuyết nhẹ",
    73: "tuyết vừa",
    75: "tuyết dày",
    77: "hạt tuyết",
    80: "mưa rào nhẹ",
    81: "mưa rào vừa",
    82: "mưa rào lớn",
    85: "mưa tuyết nhẹ",
    86: "mưa tuyết nặng",
    95: "có giông bão",
    96: "giông kèm mưa đá",
    99: "giông kèm mưa đá lớn",
}


def _fetch_weather(city: str) -> str:
    """Fetch real-time weather and forecast from Open-Meteo (TL-13)."""
    city_q = city.strip() or config.DEFAULT_CITY
    try:
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search?"
            f"name={urllib.parse.quote(city_q)}&count=1&language=vi&format=json"
        )
        geo_resp = _session.get(geo_url, timeout=4.0)
        geo_resp.raise_for_status()
        results = geo_resp.json().get("results")
        if not results:
            return f"Không tìm thấy tọa độ thời tiết cho khu vực '{city_q}'."
        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        loc_name = loc.get("name", city_q)

        wx_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&forecast_days=2"
            "&timezone=auto"
        )
        wx_resp = _session.get(wx_url, timeout=4.0)
        wx_resp.raise_for_status()
        data = wx_resp.json()
        wx = data.get("current")
        if not wx or wx.get("temperature_2m") is None:
            return "ERROR weather_unavailable: cannot retrieve weather data."

        temp = wx.get("temperature_2m")
        feels = wx.get("apparent_temperature")
        hum = wx.get("relative_humidity_2m")
        wind = wx.get("wind_speed_10m")
        wcode = int(wx.get("weather_code", 0))
        desc = WMO_WEATHER_CODES.get(wcode, "thời tiết không xác định")

        forecast_note = ""
        daily = data.get("daily", {})
        if daily and "temperature_2m_max" in daily and len(daily["temperature_2m_max"]) > 1:
            t_max = daily["temperature_2m_max"][1]
            t_min = daily["temperature_2m_min"][1]
            pop = daily.get("precipitation_probability_max", [0, 0])[1]
            forecast_note = f" Dự báo ngày mai nhiệt độ từ {t_min} đến {t_max} độ C, xác suất mưa khoảng {pop}%."

        return (
            f"Thời tiết tại {loc_name} hiện tại: {desc}, nhiệt độ {temp} độ C "
            f"(cảm giác như {feels} độ C), độ ẩm {hum}%, gió {wind} km/h.{forecast_note}"
        )
    except Exception as e:
        log.exception("Weather lookup error")
        return f"ERROR weather_unavailable: {e}"


def _fetch_web_search(query: str) -> ToolResult | str:
    """Search DuckDuckGo HTML with Vietnamese localization and untrusted wrapping (TL-04, TL-13)."""
    if not query.strip():
        return "Sếp cần tìm thông tin gì trên mạng vui lòng nói rõ từ khóa nhé."
    try:
        resp = _session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "vn-vi"},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=5.0,
        )
        if resp.status_code != 200:
            return f"Không thể kết nối công cụ tìm kiếm (mã {resp.status_code})."

        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = []
        for res_div in soup.select(".result__body")[:3]:
            title_el = res_div.select_one(".result__title")
            snip_el = res_div.select_one(".result__snippet")
            title = title_el.get_text(" ", strip=True) if title_el else ""
            snip = snip_el.get_text(" ", strip=True)[:250] if snip_el else ""
            if title or snip:
                snippets.append(f"{title}: {snip}")

        if not snippets:
            return f"Không tìm thấy kết quả trực tuyến nào cho từ khóa '{query}'."

        combined = " | ".join(snippets)
        wrapped = wrap_untrusted("web", combined)
        return ToolResult(
            text=f"Kết quả tra cứu cho '{query}':\n{wrapped}",
            tainted=True,
        )
    except Exception as e:
        log.exception("Web search error")
        return f"Lỗi khi tra cứu trực tuyến: {e}"


def tool_tra_cuu_thong_tin_truc_tuyen(args: dict) -> ToolResult | str:
    """Dispatch online lookup for weather or general web search."""
    search_type = args.get("loai", "tim_kiem")
    query = (args.get("tu_khoa") or "").strip()
    if search_type == "thoi_tiet":
        return _fetch_weather(query or config.DEFAULT_CITY)
    return _fetch_web_search(query)
