"""美股每日行情日报 - 主入口（云端版）"""
import logging
import os
import sys
from datetime import datetime, timezone, timedelta

from data_fetcher import (
    is_us_trading_day,
    get_last_trading_day,
    fetch_all_stocks_data,
    fetch_market_indices_data,
    compute_rankings,
    generate_summary,
)
from report_generator import generate_html_report, generate_holiday_notice, get_email_subject
from email_sender import send_email

# 北京时间时区
BJT = timezone(timedelta(hours=8))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


def _now_bjt():
    """返回当前北京时间字符串"""
    return datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")


def run():
    """主执行流程"""
    logger.info("=" * 60)
    logger.info(f"美股每日行情日报 - 开始运行")
    logger.info(f"运行时间（北京时间）: {_now_bjt()}")
    logger.info(f"运行环境: {'GitHub Actions' if os.environ.get('GITHUB_ACTIONS') else '本地'}")
    logger.info("=" * 60)

    # 1. 判断是否为交易日
    trading_date = get_last_trading_day()
    if trading_date is None:
        logger.error("无法确定最近交易日")
        return False

    is_trading, reason = is_us_trading_day(trading_date)

    if not is_trading:
        logger.info(f"非交易日: {reason}")
        logger.info(f"休市日跳过发送，流程正常结束")
        logger.info(f"完成时间（北京时间）: {_now_bjt()}")
        return True

    logger.info(f"交易日: {trading_date} - {reason}")

    # 2. 获取股票数据
    logger.info(">>> 步骤1: 获取股票数据...")
    stocks_data = fetch_all_stocks_data()
    logger.info(f"    获取股票数量: {len(stocks_data)} 只")
    for s in stocks_data:
        logger.info(f"    - {s['symbol']} ({s['name']}): ${s['close']} ({s['change_pct']:+.2f}%)")

    # 3. 获取市场指数数据
    logger.info(">>> 步骤2: 获取市场指数数据...")
    indices_data = fetch_market_indices_data()
    logger.info(f"    获取指数数量: {len(indices_data)} 个")

    if not stocks_data and not indices_data:
        logger.error("无法获取任何数据，流程终止")
        return False

    # 4. 计算排名和总结
    logger.info(">>> 步骤3: 计算涨跌排名...")
    rankings = compute_rankings(stocks_data)
    gainers = [(s['symbol'], round(s['change_pct'], 2)) for s in rankings['top_gainers'][:3]]
    losers = [(s['symbol'], round(s['change_pct'], 2)) for s in rankings['top_losers'][:3]]
    logger.info(f"    涨幅TOP3: {gainers}")
    logger.info(f"    跌幅TOP3: {losers}")

    summary = generate_summary(stocks_data, indices_data)

    # 5. 生成 HTML 报告
    logger.info(">>> 步骤4: 生成 HTML 报告...")
    html = generate_html_report(stocks_data, indices_data, rankings, summary, trading_date)
    logger.info(f"    报告生成成功，HTML 长度: {len(html)} 字符")

    # 6. 保存本地报告（用于调试和 GitHub Actions artifact）
    report_path = f"report_{trading_date}.html"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"    本地报告已保存: {report_path}")
    except Exception as e:
        logger.warning(f"    保存本地报告失败: {e}")

    # 7. 发送邮件
    logger.info(">>> 步骤5: 发送邮件...")
    subject = get_email_subject(trading_date)
    logger.info(f"    邮件标题: {subject}")
    logger.info(f"    收件人: {os.environ.get('RESEND_RECIPIENT', '未设置')}")

    success = send_email(subject, html)

    if success:
        logger.info("    ✅ 邮件发送成功！")
    else:
        logger.error("    ❌ 邮件发送失败！")

    # 汇总
    logger.info("=" * 60)
    logger.info(f"运行完成（北京时间）: {_now_bjt()}")
    logger.info(f"结果: {'成功' if success else '失败'}")
    logger.info("=" * 60)

    return success


if __name__ == "__main__":
    result = run()
    sys.exit(0 if result else 1)
