# 美股每日行情日报（云端自动化版）

电脑关机状态下，每天早上 6 点（北京时间）自动获取美股收盘数据，生成 HTML 日报并通过邮件发送。

## 工作原理

```
GitHub Actions 定时触发（UTC 22:00 = 北京 06:00）
    ↓
Python 获取 Yahoo Finance 美股收盘数据
    ↓
生成 HTML 格式日报
    ↓
通过 Resend HTTP API 发送邮件（非 SMTP）
```

## 部署步骤

### 1. 注册 Resend（免费）

1. 访问 https://resend.com 注册账号
2. 免费额度：100 封邮件/天（足够日报使用）
3. 如需自定义发件域名，在 Resend 控台添加并验证
4. 获取 API Key：Settings → API Keys → Create API Key

### 2. 创建 GitHub 仓库

```bash
cd stock-report-agent
git init
git add .
git commit -m "init: 美股日报云端自动化"
git branch -M main
# 在 GitHub 上创建仓库后：
git remote add origin https://github.com/你的用户名/stock-report-agent.git
git push -u origin main
```

### 3. 配置 GitHub Secrets

进入仓库 → Settings → Secrets and variables → Actions → New repository secret

添加以下 4 个 Secrets：

| Secret 名称 | 值 | 说明 |
|---|---|---|
| `RESEND_API_KEY` | `re_xxxxxxxx` | Resend API Key |
| `RESEND_FROM_EMAIL` | `onboarding@resend.dev` | 发件邮箱（测试用默认值） |
| `RESEND_FROM_NAME` | `美股日报` | 发件人名称 |
| `RESEND_FROM_EMAIL` | `你的接收邮箱` | 你接收日报的邮箱 |

> 💡 初始测试阶段可直接使用 `onboarding@resend.dev` 作为发件人，无需验证域名。自定义域名验证后可替换。

### 4. 手动测试运行

进入仓库 → Actions → US Stock Daily Report → Run workflow → Run workflow

等待执行完成，检查：
- ✅ Job 日志是否有错误
- ✅ 是否生成了 `report_*.html` artifact
- ✅ 你的邮箱是否收到日报邮件

### 5. 查看运行日志

Actions 页面 → 选择最近一次运行 → 查看详细日志

### 6. 确认定时任务

每天北京时间 06:00（UTC 22:00）会自动运行。
GitHub Actions 的 cron 可能有几分钟延迟，属于正常现象。

## 增删关注股票

编辑 `stocks.json`，在对应分组增删 `symbols`，也可新增分组：

```json
{
  "stocks": {
    "tech": { "label": "科技", "symbols": ["AAPL", "MSFT"] },
    "healthcare": { "label": "医疗", "symbols": ["JNJ", "UNH"] }
  }
}
```

修改后 push 到 GitHub 即生效。

## 休市日处理

周末和美股休市日自动跳过，不发送邮件。
休市日列表在 `data_fetcher.py` 中维护，每年更新。

## 注意事项

- 数据来源：Yahoo Finance (yfinance)，免费但可能有请求频率限制
- 涨跌颜色使用中国惯例：涨=红色，跌=绿色
- 邮件内容仅供参考，不构成投资建议
- 建议每年更新 `data_fetcher.py` 中的休市日列表
