# 📊 每日财经日报（Telegram版）

> 零成本、零基础、覆盖 **A股 + 美股 + 加密货币**，每天自动推送到你的 Telegram。

---

## ✨ 你能收到什么？

每天工作日 18:30（北京时间），你的 Telegram 会收到一条消息，包含：

| 板块 | 内容 |
|------|------|
| 🇨🇳 A股市场 | 上证指数、深证成指、创业板指涨跌 |
| 📈 A股自选股 | 你关注的 A 股实时价格和涨跌幅 |
| 🇺🇸 美股市场 | 标普500、纳斯达克、道琼斯涨跌 |
| 📈 美股自选股 | 你关注的美股实时价格和涨跌幅 |
| ₿ 加密货币 | 比特币、以太坊等币种价格和 24h 涨跌 |

示例消息：
```
📊 每日财经日报 📊
🕐 2026-07-04 18:30

🇨🇳 A股市场
🟢 上证指数: 3250.12 (+0.85%)
🟢 深证成指: 10521.36 (+1.02%)
🔴 创业板指: 2156.78 (-0.35%)

📈 A股自选股
🟢 贵州茅台(600519): ¥1688.00 (+1.20%)
🔴 五粮液(000858): ¥128.50 (-0.80%)

🇺🇸 美股市场
🟢 标普500: 5250.30 (+0.45%)
🟢 纳斯达克: 16800.20 (+0.72%)
🟡 道琼斯: 39120.50 (+0.02%)

📈 美股自选股
🟢 AAPL: $214.50 (+1.35%)
🔴 TSLA: $248.30 (-2.10%)

₿ 加密货币
🟢 BITC: $62,350.00 (+3.25%)
🟢 ETH: $3,420.50 (+1.80%)
```

---

## 🚀 部署教程（只会动鼠标也能搞定）

### 第一步：创建你的 Telegram 机器人（2分钟）

1. 打开 Telegram，搜索 `@BotFather`
2. 点击底部 **「Start」** 按钮
3. 发送 `/newbot`
4. 按提示给机器人取名字（如 `MyDailyReportBot`）
5. **保存好返回的 Token**（形如 `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

**获取你的 Chat ID：**
1. 在 Telegram 搜索 `@userinfobot`
2. 点击 Start，它会告诉你一个数字（如 `123456789`）
3. **保存好这个数字**

> 💡 备选方案：把机器人拉到一个群组，用机器人发一条消息，然后访问 `https://api.telegram.org/bot<你的Token>/getUpdates` 查看 `chat.id`

---

### 第二步：Fork 本仓库（30秒）

1. 打开本仓库页面：`https://github.com/kfat77/daily-finance-telegram`
2. 点击页面右上角的 **「Fork」** 按钮
3. 直接点 **「Create fork」**（全部保持默认）

---

### 第三步：创建 GitHub Actions 工作流（2分钟）

> ⚠️ 因为 GitHub 安全限制，workflow 文件需要你手动创建，只需复制粘贴。

1. 进入你 Fork 后的仓库页面
2. 点击 **「Add file」** 按钮 → **「Create new file」**
3. 在文件名框输入：`.github/workflows/daily-report.yml`
4. 在下方大文本框中**复制粘贴以下内容**（全部选中然后粘贴）：

```yaml
name: Daily Finance Report

on:
  schedule:
    - cron: '30 10 * * 1-5'
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run daily report
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          STOCK_LIST_A: ${{ secrets.STOCK_LIST_A }}
          STOCK_LIST_US: ${{ secrets.STOCK_LIST_US }}
          CRYPTO_LIST: ${{ secrets.CRYPTO_LIST }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python src/report.py
```

5. 点击页面最下方的 **「Commit changes...」** → **「Commit directly to the main branch」** → **「Commit new file」**

✅ 搞定！

---

### 第四步：配置 Secrets（2分钟）

这是你唯一需要"填密码"的地方，一共只要填 **2 个必填项 + 3 个可选项**：

1. 在你 Fork 后的仓库页面，点击顶部 **「Settings」**
2. 左侧菜单点击 **「Secrets and variables」** → **「Actions」**
3. 点击绿色按钮 **「New repository secret」**
4. 依次添加以下 Secrets：

**必填项（不填跑不了）：**

| Name | Secret |
|------|--------|
| `TELEGRAM_BOT_TOKEN` | 你第一步从 BotFather 拿到的 Token |
| `TELEGRAM_CHAT_ID` | 你从 @userinfobot 拿到的数字 |

**自选股配置（可选，不填也有大盘指数+默认币种）：**

| Name | Secret | 示例 |
|------|--------|------|
| `STOCK_LIST_A` | A股代码，逗号分隔 | `600519,000858,002594` |
| `STOCK_LIST_US` | 美股代码，逗号分隔 | `AAPL,TSLA,NVDA` |
| `CRYPTO_LIST` | 加密货币 ID，逗号分隔 | `bitcoin,ethereum,solana` |

> 🔍 加密货币 ID 查询：打开 [CoinGecko](https://www.coingecko.com/)，搜索币种，看网址里的 ID。比特币=`bitcoin`，以太坊=`ethereum`。

---

### 第五步：启动自动任务（30秒）

1. 点击仓库顶部的 **「Actions」** 标签
2. 你会看到一行黄色提示：`Workflows aren't being run on this forked repository`
3. 点击 **「I understand my workflows, go ahead and enable them」**

✅ **完成！** 每天北京时间 **18:30**（工作日），会自动推送日报到你的 Telegram。

---

### 🎮 立刻测试（可选）

等不及明天了？现在就想看效果：

1. 点击 **「Actions」** 标签
2. 点击左侧的 **「Daily Finance Report」**
3. 点击右侧的 **「Run workflow」** → 再点一次 **「Run workflow」**
4. 等待 1-2 分钟，刷新页面看到绿色 ✔️ 就是成功了
5. 打开 Telegram，看消息！

---

## ⏰ 定时规则

| 时间 | 说明 |
|------|------|
| 每天 18:30（北京时间） | A股收盘后、美股开盘前，推送日报 |
| 支持手动触发 | 随时点 Run workflow 就能跑 |

如果你想改时间：
1. 打开 `.github/workflows/daily-report.yml`
2. 找到 `cron: '30 10 * * 1-5'`
3. 点击编辑按钮（铅笔图标）
4. 改数字后提交（这是 UTC 时间，北京时间 = UTC+8）
   - 例：`0 12 * * 1-5` = 北京时间 20:00
   - 例：`30 1 * * 1-5` = 北京时间 09:30

---

## 💰 费用说明

| 项目 | 费用 |
|------|------|
| GitHub Actions | **免费**（每月 2000 分钟，本项目每次运行约 1-2 分钟） |
| Telegram Bot API | **免费** |
| A股数据 (AkShare) | **免费** |
| 美股数据 (YFinance) | **免费** |
| 加密货币数据 (CoinGecko) | **免费**（免费版每分钟 50 次调用，足够用） |

**总费用：¥0/月**

---

## 🔧 进阶玩法

### 添加 AI 分析（需要免费 Gemini API Key）

如果你想要 AI 总结市场走向，可以：
1. 去 [Google AI Studio](https://aistudio.google.com/app/apikey) 申请免费 Gemini API Key
2. 在 Secrets 里添加 `GEMINI_API_KEY`
3. 脚本会自动启用 AI 市场速览

> Gemini 免费版每月有 1500 次请求额度，完全够用。

### 修改自选股

随时去 **Settings → Secrets → Actions** 修改 `STOCK_LIST_A`、`STOCK_LIST_US`、`CRYPTO_LIST`，下次运行就生效。

---

## 🆘 常见问题

**Q: Telegram 没收到消息？**
- 检查 Actions 页面有没有红色 ❌，点进去看报错
- 确认 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 填对了（不要有多余空格）
- 确认你给 BotFather 的机器人发过 Start 消息

**Q: 加密货币显示"获取失败"？**
- CoinGecko 免费 API 偶尔限流，等 5 分钟再试通常就好了
- 如果频繁失败，可以删掉不关注的币种，减少请求次数

**Q: 想取消自动推送？**
- 进入 Actions → Daily Finance Report → 右上角 **「...」** → **「Disable workflow」**

---

## 📄 License

MIT License — 随意使用、修改、分享。

**免责声明**：本项目所有数据仅供学习和参考，不构成任何投资建议。股市有风险，投资需谨慎。
