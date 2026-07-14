"""报告生成模块 - 生成 HTML 邮件内容"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = __file__.rsplit("/", 1)[0] if "/" in __file__ else __file__.rsplit("\\", 1)[0]


def _load_stocks_config():
    """加载股票配置"""
    config_path = f"{BASE_DIR}/stocks.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_market_cap(cap):
    """格式化市值"""
    if cap is None:
        return "N/A"
    if cap >= 1e12:
        return f"${cap/1e12:.2f}T"
    if cap >= 1e9:
        return f"${cap/1e9:.2f}B"
    if cap >= 1e6:
        return f"${cap/1e6:.2f}M"
    return f"${cap:.0f}"


def format_volume(vol):
    """格式化成交量"""
    if vol >= 1e9:
        return f"{vol/1e9:.2f}B"
    if vol >= 1e6:
        return f"{vol/1e6:.2f}M"
    if vol >= 1e3:
        return f"{vol/1e3:.2f}K"
    return str(vol)


def _change_color(pct):
    """涨跌颜色（中国惯例：涨红跌绿）"""
    if pct > 0:
        return "#e74c3c"
    elif pct < 0:
        return "#2ecc71"
    return "#999999"


def generate_html_report(stocks_data, indices_data, rankings, summary, trading_date):
    """生成完整 HTML 日报"""
    stocks_config = _load_stocks_config()

    grouped_stocks = {}
    for group_key, group_info in stocks_config["stocks"].items():
        group_symbols = group_info["symbols"]
        group_label = group_info["label"]
        grouped_stocks[group_label] = [
            s for s in stocks_data if s["symbol"] in group_symbols
        ]

    # 显示北京时间（支持 TZ 环境变量）
    try:
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M 北京时间")
    except Exception:
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    date_title = trading_date or "最新交易日"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
    background: #f5f7fa;
    color: #333;
    margin: 0;
    padding: 20px;
  }}
  .container {{
    max-width: 800px;
    margin: 0 auto;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    overflow: hidden;
  }}
  .header {{
    background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
    color: #fff;
    padding: 24px 30px;
    text-align: center;
  }}
  .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 2px; }}
  .header .date {{ margin-top: 8px; font-size: 14px; opacity: 0.9; }}
  .section {{ padding: 20px 30px; border-bottom: 1px solid #eee; }}
  .section:last-child {{ border-bottom: none; }}
  .section-title {{
    font-size: 18px; font-weight: bold; color: #1a2a6c;
    margin-bottom: 12px; padding-left: 10px; border-left: 4px solid #fdbb2d;
  }}
  table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 14px; }}
  th {{ background: #1a2a6c; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
  tr:hover {{ background: #f0f4ff; }}
  .positive {{ color: #e74c3c; font-weight: 600; }}
  .negative {{ color: #2ecc71; font-weight: 600; }}
  .index-card {{
    display: inline-block; width: 23%; margin: 0 1%;
    background: #f8f9fb; border-radius: 8px; padding: 12px;
    text-align: center; box-sizing: border-box;
  }}
  .index-card .name {{ font-size: 13px; color: #666; }}
  .index-card .value {{ font-size: 20px; font-weight: bold; margin-top: 4px; }}
  .index-card .change {{ font-size: 14px; margin-top: 2px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
  .badge-up {{ background: #fde8e8; color: #e74c3c; }}
  .badge-down {{ background: #e8f8e8; color: #2ecc71; }}
  .summary-box {{
    background: #f0f4ff; border-radius: 8px; padding: 15px 20px;
    line-height: 1.8; font-size: 14px;
  }}
  .footer {{
    text-align: center; padding: 15px; font-size: 12px;
    color: #999; background: #f5f7fa;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>美股每日行情日报</h1>
    <div class="date">交易日: {date_title} | 生成时间: {now_str}</div>
  </div>

  <div class="section">
    <div class="section-title">一、市场指数表现</div>
    <div style="text-align:center;">"""

    for key in ["sp500", "nasdaq", "dow", "vix"]:
        if key in indices_data:
            idx = indices_data[key]
            color = _change_color(idx["change_pct"])
            sign = "+" if idx["change_pct"] > 0 else ""
            html += f"""
      <div class="index-card">
        <div class="name">{idx['name']}</div>
        <div class="value">{idx['close']:.2f}</div>
        <div class="change" style="color:{color}">
          {sign}{idx['change_pct']:.2f}% ({sign}{idx['change']:.2f})
        </div>
      </div>"""

    html += """
    </div>
  </div>

  <div class="section">
    <div class="section-title">二、关注股票涨跌</div>"""

    for group_label, group_stocks in grouped_stocks.items():
        if not group_stocks:
            continue
        html += f"""
    <h3 style="color:#555; margin: 10px 0 5px;">{group_label}</h3>
    <table>
      <tr>
        <th>股票名称</th><th>代码</th><th>收盘价</th>
        <th>涨跌额</th><th>涨跌幅</th><th>成交量</th>
        <th>市值</th><th>52周区间</th>
      </tr>"""
        for s in group_stocks:
            pct_color = _change_color(s["change_pct"])
            sign = "+" if s["change_pct"] > 0 else ""
            badge_class = "badge-up" if s["change_pct"] > 0 else ("badge-down" if s["change_pct"] < 0 else "")
            range_str = f"{s['fifty_two_week_range_pct']:.0f}%" if s["fifty_two_week_range_pct"] else "N/A"
            html += f"""
      <tr>
        <td><strong>{s['name']}</strong></td>
        <td>{s['symbol']}</td>
        <td>${s['close']:.2f}</td>
        <td style="color:{pct_color}">{sign}{s['change']:.2f}</td>
        <td style="color:{pct_color}">
          <span class="badge {badge_class}">{sign}{s['change_pct']:.2f}%</span>
        </td>
        <td>{format_volume(s['volume'])}</td>
        <td>{format_market_cap(s['market_cap'])}</td>
        <td>{range_str}</td>
      </tr>"""
        html += "    </table>\n"

    html += """  </div>

  <div class="section">
    <div class="section-title">三、涨幅排行榜 TOP 5</div>
    <table>
      <tr><th>排名</th><th>股票</th><th>代码</th><th>涨跌幅</th><th>收盘价</th></tr>"""
    for i, s in enumerate(rankings["top_gainers"], 1):
        html += f"""
      <tr>
        <td>{i}</td><td><strong>{s['name']}</strong></td>
        <td>{s['symbol']}</td>
        <td class="positive">+{s['change_pct']:.2f}%</td>
        <td>${s['close']:.2f}</td>
      </tr>"""
    html += """    </table>
  </div>

  <div class="section">
    <div class="section-title">四、跌幅排行榜 TOP 5</div>
    <table>
      <tr><th>排名</th><th>股票</th><th>代码</th><th>涨跌幅</th><th>收盘价</th></tr>"""
    for i, s in enumerate(rankings["top_losers"], 1):
        html += f"""
      <tr>
        <td>{i}</td><td><strong>{s['name']}</strong></td>
        <td>{s['symbol']}</td>
        <td class="negative">{s['change_pct']:.2f}%</td>
        <td>${s['close']:.2f}</td>
      </tr>"""
    html += """    </table>
  </div>

  <div class="section">
    <div class="section-title">五、市场总结</div>
    <div class="summary-box">"""
    for line in summary.split("\n"):
        html += f"      <p>{line}</p>\n"
    html += """    </div>
  </div>

  <div class="footer">
    此报告由自动化系统生成 | 数据来源: Yahoo Finance | 仅供参考，不构成投资建议
  </div>
</div>
</body>
</html>"""

    return html


def generate_holiday_notice(holiday_name, date_str):
    """生成休市提醒邮件"""
    try:
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M 北京时间")
    except Exception:
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8">
<style>
  body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f7fa; color: #333; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #34495e, #2c3e50); color: #fff; padding: 24px 30px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 22px; }}
  .content {{ padding: 30px; text-align: center; font-size: 16px; line-height: 1.8; }}
  .holiday-name {{ font-size: 24px; font-weight: bold; color: #e74c3c; margin: 20px 0; }}
  .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #999; background: #f5f7fa; }}
</style>
</head>
<body>
<div class="container">
  <div class="header"><h1>美股休市提醒</h1></div>
  <div class="content">
    <p>今天是 <strong>{date_str}</strong></p>
    <div class="holiday-name">{holiday_name}</div>
    <p>美股今日休市，无交易数据。下一个交易日恢复发送日报。</p>
  </div>
  <div class="footer">此提醒由自动化系统生成 | 生成时间: {now_str}</div>
</div>
</body>
</html>"""


def get_email_subject(trading_date, is_holiday=False):
    """生成邮件标题"""
    if is_holiday:
        return f"美股休市提醒 {trading_date}"
    return f"《美股每日行情日报 {trading_date}》"
