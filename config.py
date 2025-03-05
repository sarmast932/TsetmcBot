import logging

# تنظیم لاگ‌گذاری
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# توکن بات بله
TOKEN = "1382589839:NpmhsP2ikPpx2kSZ74uLyYVv6kkv9QwCKbLncAgR"

# آدرس وب‌سرویس
API_TSETMC_URL = "https://brsapi.ir/FreeTsetmcBourseApi/TsetmcApi.php"
API_USER_URL = "https://brsapi.ir/FreeTsetmcBourseApi/TsetmcApi_User.php"
API_KEY = "FreeuqqEPm1Qg18y3OiFnwMvyLhIQ802"

# تنظیم هدرها
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Accept": "application/json, text/plain, */*"
}

# لیست نمادهای صندوق‌های طلا
GOLD_FUNDS = [
    "عیار", "طلا", "کهربا", "مثقال", "گوهر", "زر", "گنج", "جواهر",
    "نفیس", "ناب", "آلتون", "تابش", "زرفام", "درخشان", "لیان",
    "زروان", "قیراط", "آتش"
]