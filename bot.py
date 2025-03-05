from bale import Bot, Message
from api import TsetmcAPI
from data_processor import DataProcessor
from portfolio import PortfolioManager
import logging
import asyncio

class BaleBot:
    def __init__(self, token):
        self.client = Bot(token=token)
        self.processor = DataProcessor()
        self.portfolio_manager = PortfolioManager()
        self.user_states = {}

    async def send_long_message(self, message, text):
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(text)

    async def send_message(self, user_id, text):
        chat = await self.client.get_chat(int(user_id))
        await chat.send(text)

    def run(self):
        @self.client.event
        async def on_ready():
            logging.info(f"بات {self.client.user.username} آماده‌ست!")
            asyncio.create_task(self.portfolio_manager.monitor_portfolios(self))

        @self.client.event
        async def on_message(message: Message):
            logging.info(f"پیام دریافتی: {message.content}")
            user_id = str(message.chat.id)
            content = message.content.strip().lower()

            # اگر کاربر توی یه حالت خاص باشه
            if user_id in self.user_states:
                state = self.user_states[user_id]
                if state["step"] == "main_menu":
                    if content == "1":
                        await message.reply(
                            "با پرتفوی چیکار می‌خوای بکنی؟\n۱- اضافه کردن نماد\n۲- حذف نماد\n۳- مشاهده پرتفوی"
                        )
                        self.user_states[user_id]["step"] = "portfolio_action"
                    elif content == "2":
                        await message.reply(
                            "با واچ‌لیست چیکار می‌خوای بکنی؟\n۱- اضافه کردن نماد\n۲- حذف نماد\n۳- مشاهده واچ‌لیست"
                        )
                        self.user_states[user_id]["step"] = "watchlist_action"
                    elif content == "3":
                        data = TsetmcAPI.fetch_fund_data()
                        if data:
                            remaining_requests = TsetmcAPI.get_remaining_requests()
                            result = self.processor.process_data(data, "gold", remaining_requests)
                            await self.send_long_message(message, result)
                        else:
                            await message.reply("خطا در دریافت داده‌ها!")
                        del self.user_states[user_id]
                    elif content == "4":
                        data = TsetmcAPI.fetch_fund_data()
                        if data:
                            remaining_requests = TsetmcAPI.get_remaining_requests()
                            result = self.processor.process_data(data, "قدرت", remaining_requests)
                            await self.send_long_message(message, result)
                        else:
                            await message.reply("خطا در دریافت داده‌ها!")
                        del self.user_states[user_id]
                    elif content == "5":
                        data = TsetmcAPI.fetch_fund_data()
                        if data:
                            remaining_requests = TsetmcAPI.get_remaining_requests()
                            result = self.processor.process_data(data, "حجم", remaining_requests)
                            await self.send_long_message(message, result)
                        else:
                            await message.reply("خطا در دریافت داده‌ها!")
                        del self.user_states[user_id]
                    elif content == "6":
                        await message.reply("اسم نماد رو بفرست (مثل طلا):")
                        self.user_states[user_id]["step"] = "symbol_info"
                    else:
                        await message.reply("لطفاً یه عدد بین ۱ تا ۶ بفرست!")
                elif state["step"] == "portfolio_action":
                    if content == "1":
                        await message.reply("نمادها رو با کاما جدا کن (مثل: طلا,زر):")
                        self.user_states[user_id]["step"] = "portfolio_add"
                    elif content == "2":
                        await message.reply("نمادی که می‌خوای حذف کنی رو بگو:")
                        self.user_states[user_id]["step"] = "portfolio_remove"
                    elif content == "3":
                        symbols = self.portfolio_manager.portfolios.get(user_id, {}).get("portfolio", [])
                        if symbols:
                            await message.reply(f"نمادهای پرتفوی شما: {', '.join(symbols)}")
                            data = TsetmcAPI.fetch_fund_data()
                            if data:
                                result = self.portfolio_manager.get_portfolio_data(user_id, data)
                                await self.send_long_message(message, result)
                        else:
                            await message.reply("پرتفوی شما خالیه!")
                        del self.user_states[user_id]
                    else:
                        await message.reply("لطفاً یه عدد بین ۱ تا ۳ بفرست!")
                elif state["step"] == "portfolio_add":
                    symbols = [s.strip() for s in content.split(",") if s.strip()]
                    self.portfolio_manager.add_portfolio(user_id, symbols)
                    await message.reply("نمادها به پرتفوی اضافه شدن!")
                    del self.user_states[user_id]
                elif state["step"] == "portfolio_remove":
                    symbols = self.portfolio_manager.portfolios.get(user_id, {}).get("portfolio", [])
                    if content in symbols:
                        symbols.remove(content)
                        self.portfolio_manager.add_portfolio(user_id, symbols)
                        await message.reply(f"نماد '{content}' حذف شد!")
                    else:
                        await message.reply("این نماد توی پرتفوی نیست!")
                    del self.user_states[user_id]
                elif state["step"] == "watchlist_action":
                    if content == "1":
                        await message.reply("نمادها رو با کاما جدا کن (مثل: عیار,گوهر):")
                        self.user_states[user_id]["step"] = "watchlist_add"
                    elif content == "2":
                        await message.reply("نمادی که می‌خوای حذف کنی رو بگو:")
                        self.user_states[user_id]["step"] = "watchlist_remove"
                    elif content == "3":
                        symbols = self.portfolio_manager.portfolios.get(user_id, {}).get("watchlist", [])
                        if symbols:
                            await message.reply(f"نمادهای واچ‌لیست شما: {', '.join(symbols)}")
                            data = TsetmcAPI.fetch_fund_data()
                            if data:
                                result = self.portfolio_manager.get_watchlist_data(user_id, data)
                                await self.send_long_message(message, result)
                        else:
                            await message.reply("واچ‌لیست شما خالیه!")
                        del self.user_states[user_id]
                    else:
                        await message.reply("لطفاً یه عدد بین ۱ تا ۳ بفرست!")
                elif state["step"] == "watchlist_add":
                    symbols = [s.strip() for s in content.split(",") if s.strip()]
                    self.portfolio_manager.add_watchlist(user_id, symbols)
                    await message.reply("نمادها به واچ‌لیست اضافه شدن!")
                    del self.user_states[user_id]
                elif state["step"] == "watchlist_remove":
                    symbols = self.portfolio_manager.portfolios.get(user_id, {}).get("watchlist", [])
                    if content in symbols:
                        symbols.remove(content)
                        self.portfolio_manager.add_watchlist(user_id, symbols)
                        await message.reply(f"نماد '{content}' حذف شد!")
                    else:
                        await message.reply("این نماد توی واچ‌لیست نیست!")
                    del self.user_states[user_id]
                elif state["step"] == "symbol_info":
                    data = TsetmcAPI.fetch_fund_data()
                    if data:
                        remaining_requests = TsetmcAPI.get_remaining_requests()
                        result = self.processor.process_data(data, content, remaining_requests)
                        await self.send_long_message(message, result)
                    else:
                        await message.reply("خطا در دریافت داده‌ها!")
                    del self.user_states[user_id]
            else:
                # اگر کاربر توی هیچ حالتی نباشه
                if content == "/start" or content == "/help":
                    await message.reply(
                        "سلام! من بات بورس هستم. چیکار می‌خوای بکنی؟\n"
                        "۱- کار با پرتفوی\n"
                        "۲- کار با واچ‌لیست\n"
                        "۳- اطلاعات صندوق‌های طلا\n"
                        "۴- فیلتر قدرت خریداران\n"
                        "۵- فیلتر حجم نسبی\n"
                        "۶- اطلاعات یه نماد خاص\n"
                        "یه عدد بین ۱ تا ۶ بفرست!"
                    )
                    self.user_states[user_id] = {"step": "main_menu"}
                else:
                    await message.reply("لطفاً با /start یا /help شروع کن!")

        self.client.run()