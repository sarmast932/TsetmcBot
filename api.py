import requests
from config import API_USER_URL, API_TSETMC_URL, API_KEY, HEADERS
import logging

class TsetmcAPI:
    @staticmethod
    def get_remaining_requests():
        try:
            response = requests.get(API_USER_URL, headers=HEADERS, params={"key": API_KEY})
            if response.status_code == 200:
                data = response.json()
                usage = data.get("today_usage_count_main", "0/100")
                used, total = map(int, usage.split("/"))
                return total - used
            return "نامشخص"
        except Exception as e:
            logging.error(f"خطا در گرفتن تعداد درخواست‌ها: {e}")
            return "نامشخص"

    @staticmethod
    def fetch_fund_data():
        try:
            params = {"key": API_KEY}
            response = requests.get(API_TSETMC_URL, headers=HEADERS, params=params)
            logging.info(f"TSETMC Status Code: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"خطا در دریافت داده‌ها: {e}")
            return None