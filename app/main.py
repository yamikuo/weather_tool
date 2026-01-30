import os
import urllib.parse
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# 載入 .env 檔案 (主要用於本地測試，部署時會直接用服務的環境變數)
load_dotenv()

app = FastAPI(
    title="台灣天氣預報 API (Taiwan Weather Forecast API)",
    description="一個簡單的 API，用於查詢台灣各縣市的即時天氣預報。",
    version="1.0.0",
)

# --- 核心天氣查詢邏輯 ---
TAIWAN_CITIES = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
    "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣"
]

def get_weather(city: str) -> dict:
    """根據城市名稱查詢天氣，並以結構化字典格式回傳。"""
    normalized_city = city.replace("台", "臺")
    if normalized_city not in TAIWAN_CITIES:
        raise HTTPException(status_code=404, detail=f"找不到城市 '{city}' 的天氣資訊。")

    auth_token = os.getenv("CWA_AUTH_TOKEN")
    if not auth_token:
        raise HTTPException(status_code=500, detail="伺服器未設定 CWA_AUTH_TOKEN。")
    
    base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    encoded_location_name = urllib.parse.quote(normalized_city)
    full_api_url = f"{base_url}?Authorization={auth_token}&locationName={encoded_location_name}"
    
    try:
        response = requests.get(full_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        location_data = data['records']['location'][0]
        weather_elements = location_data['weatherElement']
        time_info = weather_elements[0]['time'][0]
        
        # 提取所有天氣元素
        weather_condition = next(p['parameter']['parameterName'] for p in weather_elements[0]['time'] if p['startTime'] == time_info['startTime'])
        rain_prob = next(p['parameter']['parameterName'] for p in weather_elements[1]['time'] if p['startTime'] == time_info['startTime'])
        min_temp = next(p['parameter']['parameterName'] for p in weather_elements[2]['time'] if p['startTime'] == time_info['startTime'])
        max_temp = next(p['parameter']['parameterName'] for p in weather_elements[4]['time'] if p['startTime'] == time_info['startTime'])

        return {
            "city": city,
            "start_time": time_info['startTime'],
            "end_time": time_info['endTime'],
            "weather_condition": weather_condition,
            "rain_probability_percent": int(rain_prob),
            "min_temp_celsius": int(min_temp),
            "max_temp_celsius": int(max_temp),
        }
    except (requests.exceptions.RequestException, KeyError, IndexError, StopIteration) as e:
        raise HTTPException(status_code=503, detail=f"查詢天氣資料失敗：{e}")

# --- API 端點定義 ---
class WeatherRequest(BaseModel):
    city: str

@app.post("/get_weather_forecast", summary="取得天氣預報")
def api_get_weather(request: WeatherRequest):
    """
    接收一個城市名稱，回傳該城市的天氣預報。
    這是給 Claude 使用的主要工具函式。
    """
    return get_weather(request.city)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "天氣預報 API 正在運行"}