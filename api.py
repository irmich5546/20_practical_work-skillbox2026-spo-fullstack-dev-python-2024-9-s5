import requests

API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

def fetch_rates() -> dict:
    """Получение данных о курсе валют через API-запрос"""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching rates: {e}")
        return {}