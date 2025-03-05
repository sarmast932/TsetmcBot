from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from api import TsetmcAPI
from data_processor import DataProcessor
from portfolio import PortfolioManager
import logging

# تنظیم لاگ‌گذاری
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TelegramBot:
    def __init__(self, token):
        self.processor = DataProcessor()
        self.portfolio_manager = PortfolioManager()
        self.user_states = {}
        self.application = Application.builder().token(token).build()

    async def send_long_message(self, chat_id, text, context):
        if len(text) > 4096:  # محدودیت تلگرام
            parts = [text[i:i+4096] for i in range(0, len(text), 4096)]
            for part in parts:
                await context.bot.send_message(chat_id=chat_id, text=part)
        else:
            await context.bot.send_message(chat_id=chat_id, text=text)

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
        # منوی اصلی با دکمه‌های Inline
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 کار با پرتفوی", callback_data="portfolio"), InlineKeyboardButton("👀 کار با واچ‌لیست", callback_data="watchlist")],
            [InlineKeyboardButton("💰 صندوق‌های طلا", callback_data="gold"), InlineKeyboardButton("⚡ فیلتر قدرت خریداران", callback_data="قدرت")],
            [InlineKeyboardButton("📈 فیلتر حجم نسبی", callback_data="حجم"), InlineKeyboardButton("🔍 اطلاعات نماد خاص", callback_data="symbol")]
        ])
        if update.message:
            await update.message.reply_text(
                "سلام! من بات بورس هستم. چیکار می‌خوای بکنی؟\nیکی از گزینه‌ها رو انتخاب کن:",
                reply_markup=keyboard
            )
        else:
            await update.callback_query.edit_message_text(
                "سلام! من بات بورس هستم. چیکار می‌خوای بکنی؟\nیکی از گزینه‌ها رو انتخاب کن:",
                reply_markup=keyboard
            )
        self.user_states[chat_id] = {"step": "main_menu"}

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = query.message.chat_id
        content = query.data
        logging.info(f"دکمه زده شد: {content}")
        await query.answer()  # پاسخ به کلیک دکمه

        if chat_id in self.user_states:
            state = self.user_states[chat_id]
            if state["step"] == "main_menu":
                if content == "portfolio":
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ اضافه کردن نماد", callback_data="portfolio_add"), InlineKeyboardButton("➖ حذف نماد", callback_data="portfolio_remove")],
                        [InlineKeyboardButton("👁️ مشاهده پرتفوی", callback_data="portfolio_view"), InlineKeyboardButton("🔙 برگشت", callback_data="menu")]
                    ])
                    await query.edit_message_text(
                        "با پرتفوی چیکار می‌خوای بکنی؟",
                        reply_markup=keyboard
                    )
                    self.user_states[chat_id]["step"] = "portfolio_action"
                elif content == "watchlist":
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ اضافه کردن نماد", callback_data="watchlist_add"), InlineKeyboardButton("➖ حذف نماد", callback_data="watchlist_remove")],
                        [InlineKeyboardButton("👁️ مشاهده واچ‌لیست", callback_data="watchlist_view"), InlineKeyboardButton("🔙 برگشت", callback_data="menu")]
                    ])
                    await query.edit_message_text(
                        "با واچ‌لیست چیکار می‌خوای بکنی؟",
                        reply_markup=keyboard
                    )
                    self.user_states[chat_id]["step"] = "watchlist_action"
                elif content == "gold":
                    data = TsetmcAPI.fetch_fund_data()
                    if data:
                        remaining_requests = TsetmcAPI.get_remaining_requests()
                        result = self.processor.process_data(data, "gold", remaining_requests)
                        await self.send_long_message(chat_id, result, context)
                    else:
                        await query.edit_message_text("خطا در دریافت داده‌ها!")
                    del self.user_states[chat_id]
                elif content == "قدرت":
                    data = TsetmcAPI.fetch_fund_data()
                    if data:
                        remaining_requests = TsetmcAPI.get_remaining_requests()
                        result = self.processor.process_data(data, "قدرت", remaining_requests)
                        await self.send_long_message(chat_id, result, context)
                    else:
                        await query.edit_message_text("خطا در دریافت داده‌ها!")
                    del self.user_states[chat_id]
                elif content == "حجم":
                    data = TsetmcAPI.fetch_fund_data()
                    if data:
                        remaining_requests = TsetmcAPI.get_remaining_requests()
                        result = self.processor.process_data(data, "حجم", remaining_requests)
                        await self.send_long_message(chat_id, result, context)
                    else:
                        await query.edit_message_text("خطا در دریافت داده‌ها!")
                    del self.user_states[chat_id]
                elif content == "symbol":
                    await query.edit_message_text("اسم نماد رو بفرست (مثل طلا):")
                    self.user_states[chat_id]["step"] = "symbol_info"
                elif content == "menu":
                    await self.show_menu(update, context)
            elif state["step"] == "portfolio_action":
                if content == "portfolio_add":
                    await query.edit_message_text("نمادها رو با کاما جدا کن (مثل: طلا,زر):")
                    self.user_states[chat_id]["step"] = "portfolio_add"
                elif content == "portfolio_remove":
                    await query.edit_message_text("نمادی که می‌خوای حذف کنی رو بگو:")
                    self.user_states[chat_id]["step"] = "portfolio_remove"
                elif content == "portfolio_view":
                    symbols = self.portfolio_manager.portfolios.get(chat_id, {}).get("portfolio", [])
                    if symbols:
                        await query.edit_message_text(f"نمادهای پرتفوی شما: {', '.join(symbols)}")
                        data = TsetmcAPI.fetch_fund_data()
                        if data:
                            result = self.portfolio_manager.get_portfolio_data(chat_id, data)
                            await self.send_long_message(chat_id, result, context)
                    else:
                        await query.edit_message_text("پرتفوی شما خالیه!")
                    del self.user_states[chat_id]
                elif content == "menu":
                    await self.show_menu(update, context)
            elif state["step"] == "watchlist_action":
                if content == "watchlist_add":
                    await query.edit_message_text("نمادها رو با کاما جدا کن (مثل: عیار,گوهر):")
                    self.user_states[chat_id]["step"] = "watchlist_add"
                elif content == "watchlist_remove":
                    await query.edit_message_text("نمادی که می‌خوای حذف کنی رو بگو:")
                    self.user_states[chat_id]["step"] = "watchlist_remove"
                elif content == "watchlist_view":
                    symbols = self.portfolio_manager.portfolios.get(chat_id, {}).get("watchlist", [])
                    if symbols:
                        await query.edit_message_text(f"نمادهای واچ‌لیست شما: {', '.join(symbols)}")
                        data = TsetmcAPI.fetch_fund_data()
                        if data:
                            result = self.portfolio_manager.get_watchlist_data(chat_id, data)
                            await self.send_long_message(chat_id, result, context)
                    else:
                        await query.edit_message_text("واچ‌لیست شما خالیه!")
                    del self.user_states[chat_id]
                elif content == "menu":
                    await self.show_menu(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        content = update.message.text.strip().lower()
        logging.info(f"پیام دریافتی: {content}")

        if chat_id in self.user_states:
            state = self.user_states[chat_id]
            if state["step"] == "portfolio_add":
                symbols = [s.strip() for s in content.split(",") if s.strip()]
                self.portfolio_manager.add_portfolio(chat_id, symbols)
                await update.message.reply_text("نمادها به پرتفوی اضافه شدن!")
                del self.user_states[chat_id]
            elif state["step"] == "portfolio_remove":
                symbols = self.portfolio_manager.portfolios.get(chat_id, {}).get("portfolio", [])
                if content in symbols:
                    symbols.remove(content)
                    self.portfolio_manager.add_portfolio(chat_id, symbols)
                    await update.message.reply_text(f"نماد '{content}' حذف شد!")
                else:
                    await update.message.reply_text("این نماد توی پرتفوی نیست!")
                del self.user_states[chat_id]
            elif state["step"] == "watchlist_add":
                symbols = [s.strip() for s in content.split(",") if s.strip()]
                self.portfolio_manager.add_watchlist(chat_id, symbols)
                await update.message.reply_text("نمادها به واچ‌لیست اضافه شدن!")
                del self.user_states[chat_id]
            elif state["step"] == "watchlist_remove":
                symbols = self.portfolio_manager.portfolios.get(chat_id, {}).get("watchlist", [])
                if content in symbols:
                    symbols.remove(content)
                    self.portfolio_manager.add_watchlist(chat_id, symbols)
                    await update.message.reply_text(f"نماد '{content}' حذف شد!")
                else:
                    await update.message.reply_text("این نماد توی واچ‌لیست نیست!")
                del self.user_states[chat_id]
            elif state["step"] == "symbol_info":
                data = TsetmcAPI.fetch_fund_data()
                if data:
                    remaining_requests = TsetmcAPI.get_remaining_requests()
                    result = self.processor.process_data(data, content, remaining_requests)
                    await self.send_long_message(chat_id, result, context)
                else:
                    await update.message.reply_text("خطا در دریافت داده‌ها!")
                del self.user_states[chat_id]
        else:
            if content == "?" or content == "؟" or content == "/start" or content == "/help":
                await self.show_menu(update, context)
            else:
                await update.message.reply_text("لطفاً با ? یا ؟ یا /start یا /help شروع کن!")

    def run(self):
        self.application.add_handler(CommandHandler("start", self.show_menu))
        self.application.add_handler(CommandHandler("help", self.show_menu))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.run_polling()

if __name__ == "__main__":
    TOKEN = "7837115196:AAH3HgvHz_r9JbBkXlHVFArax3-TkWW29I8"  # توکن تلگرام
    bot = TelegramBot(TOKEN)
    bot.run()