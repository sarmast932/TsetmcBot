from datetime import datetime, time
import asyncio
from api import TsetmcAPI
from data_processor import DataProcessor
import logging

class PortfolioManager:
    def __init__(self):
        self.portfolios = {}  # {user_id: {"portfolio": [symbols], "watchlist": [symbols]}}
        self.running = False

    def add_portfolio(self, user_id, symbols):
        if user_id not in self.portfolios:
            self.portfolios[user_id] = {"portfolio": [], "watchlist": []}
        self.portfolios[user_id]["portfolio"] = symbols

    def add_watchlist(self, user_id, symbols):
        if user_id not in self.portfolios:
            self.portfolios[user_id] = {"portfolio": [], "watchlist": []}
        self.portfolios[user_id]["watchlist"] = symbols

    def get_portfolio_data(self, user_id, data):
        if user_id not in self.portfolios or not self.portfolios[user_id]["portfolio"]:
            return "پرتفوی شما خالی است!"
        remaining_requests = TsetmcAPI.get_remaining_requests()
        result = f"درخواست‌های باقی‌مونده: {remaining_requests}\n"
        funds_info = ""
        for fund in data:
            if fund.get("l18") in self.portfolios[user_id]["portfolio"]:
                funds_info += DataProcessor.format_fund_info(fund)
        return result + (funds_info or "داده‌ای برای پرتفوی شما پیدا نشد!")

    def get_watchlist_data(self, user_id, data):
        if user_id not in self.portfolios or not self.portfolios[user_id]["watchlist"]:
            return "واچ‌لیست شما خالی است!"
        remaining_requests = TsetmcAPI.get_remaining_requests()
        result = f"درخواست‌های باقی‌مونده: {remaining_requests}\n"
        funds_info = ""
        for fund in data:
            if fund.get("l18") in self.portfolios[user_id]["watchlist"]:
                funds_info += DataProcessor.format_fund_info(fund)
        return result + (funds_info or "داده‌ای برای واچ‌لیست شما پیدا نشد!")

    async def monitor_portfolios(self, bot):
        self.running = True
        while self.running:
            now = datetime.now().time()
            if time(9, 0) <= now <= time(15, 0):
                data = TsetmcAPI.fetch_fund_data()
                if data:
                    for user_id in self.portfolios:
                        if self.portfolios[user_id]["portfolio"]:
                            result = self.get_portfolio_data(user_id, data)
                            await bot.send_message(user_id, result)
                await asyncio.sleep(900)  # هر 15 دقیقه (900 ثانیه)
            else:
                await asyncio.sleep(60)  # چک هر دقیقه خارج از ساعت کاری