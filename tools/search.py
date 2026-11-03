"""
Group 7: Real-time Weather Forecasts & Web Search.
- Open-Meteo API for real-time weather forecasts (temperature, humidity, wind, conditions).
- DuckDuckGo HTML search for current news, prices, and queries without requiring API keys.
"""

import urllib.parse

import requests
from bs4 import BeautifulSoup

import config

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
    61: "mưa nhỏ",
    63: "mưa vừa",
    65: "mưa to",
    80: "mưa rào nhẹ",
    81: "mưa rào vừa",
    82: "mưa rào lớn",
    95: "có giông bão",
    96: "giông kèm mưa đá",
}


def _fetch_weather(city: str) -> str:
    """Fetch real-time weather from Open-Meteo for specified city or DEFAULT_CITY."""
    city_q = city.strip() or config.DEFAULT_CITY
    try:
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search?"
            f"name={urllib.parse.quote(city_q)}&count=1&language=vi&format=json"
        )
        geo_resp = requests.get(geo_url, timeout=4.0).json()
        results = geo_resp.get("results")
        if not results:
            return f"Không tìm thấy tọa độ thời tiết cho khu vực '{city_q}'."
        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        loc_name = loc.get("name", city_q)

        wx_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            "&timezone=auto"
        )
        wx = requests.get(wx_url, timeout=4.0).json().get("current", {})
        temp = wx.get("temperature_2m")
        feels = wx.get("apparent_temperature")
        hum = wx.get("relative_humidity_2m")
        wind = wx.get("wind_speed_10m")
        wcode = int(wx.get("weather_code", 0))
        desc = WMO_WEATHER_CODES.get(wcode, "bình thường")

        res = (
            f"Thời tiết tại {loc_name} hiện tại: {desc}, nhiệt độ {temp} độ C "
            f"(cảm giác như {feels} độ C), độ ẩm {hum}%, gió {wind} km/h."
        )
        print(f"🌤️ [Tool Call -> Weather]: {res}")
        return res
    except Exception as e:
        return f"Không thể tra cứu thời tiết lúc này: {e}"


def _fetch_web_search(query: str) -> str:
    """Search DuckDuckGo HTML for top snippets matching query."""
    if not query.strip():
        return "Sếp cần tìm thông tin gì trên mạng vui lòng nói rõ từ khóa nhé."
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
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
            snip = snip_el.get_text(" ", strip=True) if snip_el else ""
            if title or snip:
                snippets.append(f"{title}: {snip}")

        if not snippets:
            return f"Không tìm thấy kết quả trực tuyến nào cho từ khóa '{query}'."

        combined = " | ".join(snippets)
        print(f"🌐 [Tool Call -> Web Search]: Tìm '{query}' -> {len(snippets)} kết quả")
        return f"Kết quả tra cứu cho '{query}': {combined}"
    except Exception as e:
        return f"Lỗi khi tra cứu trực tuyến: {e}"


def tool_tra_cuu_thong_tin_truc_tuyen(args: dict) -> str:
    """Dispatch online lookup for weather or general web search."""
    search_type = args.get("loai", "tim_kiem")
    query = (args.get("tu_khoa") or "").strip()
    if search_type == "thoi_tiet":
        return _fetch_weather(query or config.DEFAULT_CITY)
    return _fetch_web_search(query)

