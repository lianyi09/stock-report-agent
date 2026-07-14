"""美股每日行情日报 - 主入口（云端版）"""
import logging
import os
import sys

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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


def run():
    """主执行流程"""
    logger.info("=" * 50)
    logger.info("美股每日行情日报 - 开始执行")
    logger.info("=" * 50)

    # 1. 判断是否为交易日
    trading_date = get_last_trading_day()
    if trading_date is None:
        logger.error("无法确定最近交易日")
        return False

    is_trading, reason = is_us_trading_day(trading_date)

    if not is_trading:
        logger.info(f"非交易日: {reason}")
        # 休市日：生成提醒但不发送（可选发送休市通知）
        # 如需发送休市通知，取消下面注释：
        # html = generate_holiday_notice(reason, trading_date)
        # subject = get_email_subject(trading_date, is_holiday=True)
        # send_email(subject, html)
        logger.info(f"休市日跳过: {reason}")
        return True  # 休市日视为成功执行

    logger.info(f"交易日: {trading_date} - {reason}")

    # 2. 获取股票数据
    logger.info("正在获取股票数据...")
    stocks_data = fetch_all_stocks_data()
    logger.info(f"获取到 {len(stocks_data)} 只股票数据")

    # 3. 获取市场指数数据
    logger.info("正在获取市场指数数据...")
    indices_data = fetch_market_indices_data()
    logger.info(f"获取到 {len(indices_data)} 个指数数据")

    if not stocks_data and not indices_data:
        logger.error("无法获取任何数据")
        return False

    # 4. 计算排名和总结
    rankings = compute_rankings(stocks_data)
    summary = generate_summary(stocks_data, indices_data)

    # 5. 生成 HTML 报告
    html = generate_html_report(stocks_data, indices_data, rankings, summary, trading_date)

    # 6. 保存本地报告（用于调试和 GitHub Actions artifact）
    report_path = f"report_{trading_date}.html"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"本地报告已保存: {report_path}")
    except Exception as e:
        logger.warning(f"保存本地报告失败: {e}")

    # 7. 发送邮件
    subject = get_email_subject(trading_date)
    logger.info(f"邮件标题: {subject}")

    success = send_email(subject, html)

    if success:
        logger.info("日报邮件发送成功！")
    else:
        logger.error("日报邮件发送失败！")

    return success


if __name__ == "__main__":
    result = run()
    sys.exit(0 if result else 1)
