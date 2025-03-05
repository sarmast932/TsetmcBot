from config import GOLD_FUNDS
import logging

class DataProcessor:
    @staticmethod
    def safe_float(value):
        return float(value) if value is not None and isinstance(value, (int, float, str)) else 0

    @staticmethod
    def safe_int(value):
        return int(value) if value is not None and isinstance(value, (int, float, str)) else 0

    @staticmethod
    def calc_buyer_power(fund):
        buy_i_volume = DataProcessor.safe_float(fund.get("Buy_I_Volume", 0))
        buy_count_i = DataProcessor.safe_int(fund.get("Buy_CountI", 0))
        sell_i_volume = DataProcessor.safe_float(fund.get("Sell_I_Volume", 0))
        sell_count_i = DataProcessor.safe_int(fund.get("Sell_CountI", 0))
        if buy_count_i > 0 and sell_count_i > 0 and sell_i_volume > 0:
            return round(((buy_i_volume / buy_count_i) / (sell_i_volume / sell_count_i)) * 10) / 10
        return 0

    @staticmethod
    def calc_volume_ratio(fund):
        volume = DataProcessor.safe_float(fund.get("tvol", 0))
        base_volume = DataProcessor.safe_float(fund.get("bvol", 0))
        return round((volume / base_volume) * 10) / 10 if base_volume > 0 else 0

    @staticmethod
    def format_fund_info(fund):
        symbol = fund.get("l18", "نامشخص")
        time = fund.get("time", "نامشخص")
        price = DataProcessor.safe_float(fund.get("pl", 0))
        final_price = DataProcessor.safe_float(fund.get("pc", 0))
        price_change = DataProcessor.safe_float(fund.get("plc", 0))
        price_percent = DataProcessor.safe_float(fund.get("plp", 0))
        volume = DataProcessor.safe_float(fund.get("tvol", 0))
        value = DataProcessor.safe_float(fund.get("tval", 0))
        pe = DataProcessor.safe_float(fund.get("pe", 0))
        min_price = DataProcessor.safe_float(fund.get("pmin", 0))
        max_price = DataProcessor.safe_float(fund.get("pmax", 0))
        qd1 = DataProcessor.safe_float(fund.get("qd1", 0))
        qo1 = DataProcessor.safe_float(fund.get("qo1", 0))

        buyer_power = DataProcessor.calc_buyer_power(fund)
        volume_ratio = DataProcessor.calc_volume_ratio(fund)
        suspicious_volume = "بله" if volume > 2 * DataProcessor.safe_float(fund.get("bvol", 0)) else "خیر"
        avg_monthly_volume = volume * 20 if volume > 0 else 0
        order_book = "صف خرید" if qd1 > 0 and qo1 == 0 else "صف فروش" if qo1 > 0 and qd1 == 0 else "بدون صف"

        return (
            f"{symbol} (زمان: {time}):\n"
            f"قیمت فعلی: {price:,}\n"
            f"قیمت پایانی: {final_price:,}\n"
            f"تغییر قیمت: {'+' if price_change >= 0 else ''}{price_change:,} ({price_percent:.2f}%)\n"
            f"حجم معاملات: {volume:,}\n"
            f"ارزش معاملات: {value:,}\n"
            f"قدرت خریدار حقیقی: {buyer_power:.2f}\n"
            f"حجم نسبی: {volume_ratio:.2f}\n"
            f"حجم مشکوک: {suspicious_volume}\n"
            f"میانگین حجم ماهانه: {avg_monthly_volume:,}\n"
            f"وضعیت صف: {order_book}\n"
            f"P/E: {pe:.2f}\n"
            f"کمترین قیمت: {min_price:,}\n"
            f"بیشترین قیمت: {max_price:,}\n"
            "-----\n"
        )

    @staticmethod
    def process_data(data, query, remaining_requests):
        result = f"درخواست‌های باقی‌مونده: {remaining_requests}\n"
        if not data or not isinstance(data, list):
            return f"{result}API داده معتبری برنگردوند!"

        query = query.lower()
        if query == "gold":
            funds_info = "".join(DataProcessor.format_fund_info(fund) for fund in data if fund.get("l18") in GOLD_FUNDS)
            return result + (funds_info or "هیچ صندوق طلایی پیدا نشد!")
        elif query == "قدرت":
            filtered = sorted(
                [(fund, DataProcessor.calc_buyer_power(fund)) for fund in data if DataProcessor.meets_buyer_power_criteria(fund)],
                key=lambda x: x[1], reverse=True
            )
            funds_info = "".join(DataProcessor.format_fund_info(fund) for fund, _ in filtered[:10])
            return result + (funds_info or "سهامی با این فیلتر پیدا نشد!")
        elif query == "حجم":
            filtered = sorted(
                [(fund, DataProcessor.calc_volume_ratio(fund)) for fund in data if DataProcessor.meets_volume_criteria(fund)],
                key=lambda x: x[1], reverse=True
            )
            funds_info = "".join(DataProcessor.format_fund_info(fund) for fund, _ in filtered[:10])
            return result + (funds_info or "سهامی با این فیلتر پیدا نشد!")
        else:
            for fund in data:
                if fund.get("l18") == query:
                    return result + DataProcessor.format_fund_info(fund)
            return f"{result}نماد '{query}' پیدا نشد!"

    @staticmethod
    def meets_buyer_power_criteria(fund):
        buyer_power = DataProcessor.calc_buyer_power(fund)
        tno = DataProcessor.safe_int(fund.get("tno", 0))
        return buyer_power > 2 and tno > 20

    @staticmethod
    def meets_volume_criteria(fund):
        volume_ratio = DataProcessor.calc_volume_ratio(fund)
        tno = DataProcessor.safe_int(fund.get("tno", 0))
        volume = DataProcessor.safe_float(fund.get("tvol", 0))
        buy_n_volume = DataProcessor.safe_float(fund.get("Buy_N_Volume", 0))
        return volume_ratio > 1 and tno > 20 and (buy_n_volume / volume < 0.5 if volume > 0 else False)