"""数据获取模块 - 通过 yfinance 获取美股数据"""
import json
import logging
from datetime import datetime, timedelta

import yfinance as yf

logger = logging.getLogger(__name__)

# 项目根目录
BASE_DIR = __file__.rsplit("/", 1)[0] if "/" in __file__ else __file__.rsplit("\\", 1)[0]

# 美股休市日期（2025-2026主要假期）
US_HOLIDAYS = {
    "2025-01-01": "元旦 (New Year's Day)",
    "2025-01-20": "马丁·路德·金日 (MLK Day)",
    "2025-02-17": "总统日 (Presidents' Day)",
    "2025-04-18": "耶稣受难日 (Good Friday)",
    "2025-05-26": "阵亡将士纪念日 (Memorial Day)",
    "2025-06-19": "六月节 (Juneteenth)",
    "2025-07-04": "独立日 (Independence Day)",
    "2025-09-01": "劳动节 (Labor Day)",
    "2025-11-27": "感恩节 (Thanksgiving)",
    "2025-12-25": "圣诞节 (Christmas)",
    "2026-01-01": "元旦 (New Year's Day)",
    "2026-01-19": "马丁·路德·金日 (MLK Day)",
    "2026-02-16": "总统日 (Presidents' Day)",
    "2026-04-03": "耶稣受难日 (Good Friday)",
    "2026-05-25": "阵亡将士纪念日 (Memorial Day)",
    "2026-06-19": "六月节 (Juneteenth)",
    "2026-07-03": "独立日 (Independence Day, observed)",
    "2026-09-07": "劳动节 (Labor Day)",
    "2026-11-26": "感恩节 (Thanksgiving)",
    "2026-12-25": "圣诞节 (Christmas)",
}


def load_stocks_config():
    """加载 stocks.json 配置"""
    config_path = f"{BASE_DIR}/stocks.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_symbols():
    """获取所有关注的股票代码列表"""
    config = load_stocks_config()
    symbols = []
    for group in config["stocks"].values():
        symbols.extend(group["symbols"])
    return symbols


def get_market_indices():
    """获取市场指数代码映射"""
    config = load_stocks_config()
    return config["market_indices"]


def is_us_trading_day(date_str=None):
    """判断是否为美股交易日"""
    if date_str is None:
        now = datetime.utcnow()
        check_date = now - timedelta(days=1)
        date_str = check_date.strftime("%Y-%m-%d")

    dt = datetime.strptime(date_str, "%Y-%m-%d")

    if dt.weekday() >= 5:
        return False, f"周末休市 ({'周六' if dt.weekday() == 5 else '周日'})"

    if date_str in US_HOLIDAYS:
        return False, f"美股休市 - {US_HOLIDAYS[date_str]}"

    return True, "正常交易日"


def get_last_trading_day():
    """获取最近的美股交易日日期"""
    now = datetime.utcnow()
    for i in range(1, 10):
        check_date = now - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        is_trading, _ = is_us_trading_day(date_str)
        if is_trading:
            return date_str
    return None


def fetch_stock_data(symbol, period="5d"):
    """获取单只股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty or len(hist) < 2:
            logger.warning(f"股票 {symbol} 数据不足")
            return None

        last_row = hist.iloc[-1]
        prev_row = hist.iloc[-2]

        info = ticker.info
        name = info.get("shortName", info.get("longName", symbol))

        close = last_row["Close"]
        prev_close = prev_row["Close"]
        change = close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0

        fifty_two_week_high = info.get("fiftyTwoWeekHigh", 0)
        fifty_two_week_low = info.get("fiftyTwoWeekLow", 0)
        if fifty_two_week_high and fifty_two_week_low:
            fifty_two_week_range_pct = (
                (close - fifty_two_week_low) / (fifty_two_week_high - fifty_two_week_low)
            ) * 100
        else:
            fifty_two_week_range_pct = None

        return {
            "symbol": symbol,
            "name": name,
            "close": float(round(close, 2)),
            "prev_close": float(round(prev_close, 2)),
            "change": float(round(change, 2)),
            "change_pct": float(round(change_pct, 2)),
            "volume": int(last_row["Volume"]),
            "market_cap": int(info.get("marketCap", 0)) if info.get("marketCap") else None,
            "fifty_two_week_high": float(fifty_two_week_high) if fifty_two_week_high else None,
            "fifty_two_week_low": float(fifty_two_week_low) if fifty_two_week_low else None,
            "fifty_two_week_range_pct": float(round(fifty_two_week_range_pct, 2)) if fifty_two_week_range_pct is not None else None,
            "date": hist.index[-1].strftime("%Y-%m-%d"),
        }

    except Exception as e:
        logger.error(f"获取 {symbol} 数据失败: {e}")
        return None


def fetch_all_stocks_data():
    """批量获取所有关注股票数据"""
    symbols = get_all_symbols()
    results = []
    for symbol in symbols:
        data = fetch_stock_data(symbol)
        if data:
            results.append(data)
    return results


def fetch_market_indices_data():
    """获取市场指数数据"""
    indices = get_market_indices()
    index_labels = {"sp500": "标普500", "nasdaq": "纳斯达克", "dow": "道琼斯", "vix": "VIX恐慌指数"}
    results = {}

    for name, symbol in indices.items():
        data = fetch_stock_data(symbol, period="5d")
        if data:
            results[name] = {
                "name": index_labels.get(name, name),
                "symbol": symbol,
                "close": data["close"],
                "change": data["change"],
                "change_pct": data["change_pct"],
                "date": data["date"],
            }
    return results


def compute_rankings(stocks_data):
    """计算涨跌排名"""
    if not stocks_data:
        return {"top_gainers": [], "top_losers": [], "most_volatile": []}

    sorted_by_gain = sorted(stocks_data, key=lambda x: x["change_pct"], reverse=True)
    top_gainers = sorted_by_gain[:5]
    top_losers = sorted_by_gain[-5:] if len(sorted_by_gain) >= 5 else sorted_by_gain

    with_range = [s for s in stocks_data if s["fifty_two_week_range_pct"] is not None]
    sorted_by_vol = sorted(with_range, key=lambda x: abs(x["change_pct"]), reverse=True)
    most_volatile = sorted_by_vol[:3]

    return {"top_gainers": top_gainers, "top_losers": top_losers, "most_volatile": most_volatile}


def generate_summary(stocks_data, indices_data):
    """生成市场总结文本"""
    total = len(stocks_data)
    if total == 0:
        return "今日无可用数据。"

    gains = sum(1 for s in stocks_data if s["change_pct"] > 0)
    losses = sum(1 for s in stocks_data if s["change_pct"] < 0)
    avg_change = sum(s["change_pct"] for s in stocks_data) / total

    parts = []
    if "sp500" in indices_data:
        sp = indices_data["sp500"]
        parts.append(f"标普500 {'上涨' if sp['change_pct'] > 0 else '下跌'} {abs(sp['change_pct']):.2f}%，收于 {sp['close']:.2f} 点。")

    parts.append(f"关注的 {total} 只股票中，{gains} 只上涨，{losses} 只下跌，平均涨跌幅 {avg_change:+.2f}%。")

    if stocks_data:
        best = max(stocks_data, key=lambda x: x["change_pct"])
        worst = min(stocks_data, key=lambda x: x["change_pct"])
        parts.append(f"涨幅最大: {best['name']}({best['symbol']}) {best['change_pct']:+.2f}%；跌幅最大: {worst['name']}({worst['symbol']}) {worst['change_pct']:+.2f}%。")

    if "vix" in indices_data:
        vix = indices_data["vix"]
        vix_level = "较低（市场平静）" if vix["close"] < 15 else ("中等" if vix["close"] < 20 else "较高（市场焦虑）")
        parts.append(f"VIX恐慌指数 {vix['close']:.2f}，{vix_level}。")

    return "\n".join(parts)
