import os
import requests
from datetime import datetime

# 尝试导入可选依赖
try:
    import akshare as ak
except ImportError:
    ak = None

try:
    import yfinance as yf
except ImportError:
    yf = None


class DailyReport:
    def __init__(self):
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.tg_chat = os.getenv("TELEGRAM_CHAT_ID", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        # 自选股配置
        stocks_a_raw = os.getenv("STOCK_LIST_A", "")
        self.stocks_a = [s.strip() for s in stocks_a_raw.split(",") if s.strip()] if stocks_a_raw else []
        
        stocks_us_raw = os.getenv("STOCK_LIST_US", "")
        self.stocks_us = [s.strip() for s in stocks_us_raw.split(",") if s.strip()] if stocks_us_raw else []
        
        crypto_raw = os.getenv("CRYPTO_LIST", "bitcoin,ethereum")
        self.cryptos = [s.strip() for s in crypto_raw.split(",") if s.strip()] if crypto_raw else ["bitcoin", "ethereum"]

    def _tg_escape(self, text: str) -> str:
        """Telegram MarkdownV2 转义 - 保留字符前加反斜杠"""
        # Telegram MarkdownV2 的保留字符
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        result = ''
        for c in str(text):
            if c in escape_chars:
                result += '\\' + c
            else:
                result += c
        return result

    def _plain_text(self, text: str) -> str:
        """生成纯文本版本（去掉所有 markdown 标记）"""
        # 去掉 markdown 标记，保留可读性
        text = text.replace('\\*', '*')
        text = text.replace('\\_', '_')
        text = text.replace('\\`', '`')
        text = text.replace('\\.', '.')
        text = text.replace('\\[', '[')
        text = text.replace('\\]', ']')
        text = text.replace('\\(', '(')
        text = text.replace('\\)', ')')
        text = text.replace('\\-', '-')
        text = text.replace('\\+', '+')
        text = text.replace('\\=', '=')
        text = text.replace('\\|', '|')
        text = text.replace('\\{', '{')
        text = text.replace('\\}', '}')
        text = text.replace('\\!', '!')
        text = text.replace('\\~', '~')
        text = text.replace('\\>', '>')
        text = text.replace('\\#', '#')
        text = text.replace('*', '')
        text = text.replace('_', '')
        text = text.replace('`', '')
        return text

    def get_a_share_index(self) -> dict:
        """获取A股主要指数"""
        if ak is None:
            return {"error": "akshare not installed"}
        try:
            df = ak.index_zh_a_spot_em()
            result = {}
            target_names = ["上证指数", "深证成指", "创业板指"]
            for name in target_names:
                row = df[df["名称"] == name]
                if len(row) > 0:
                    r = row.iloc[0]
                    result[name] = {
                        "price": r["最新价"],
                        "change_pct": r["涨跌幅"]
                    }
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_a_stock(self, code: str) -> dict:
        """获取A股个股"""
        if ak is None:
            return None
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code]
            if len(row) == 0:
                return None
            r = row.iloc[0]
            return {
                "name": r["名称"],
                "price": r["最新价"],
                "change_pct": r["涨跌幅"]
            }
        except Exception:
            return None

    def get_us_index(self) -> dict:
        """获取美股主要指数"""
        if yf is None:
            return {"error": "yfinance not installed"}
        try:
            import time
            tickers = {
                "标普500": "^GSPC",
                "纳斯达克": "^IXIC",
                "道琼斯": "^DJI"
            }
            result = {}
            for name, symbol in tickers.items():
                hist = yf.Ticker(symbol).history(period="3d")
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change_pct = (latest['Close'] - prev['Close']) / prev['Close'] * 100
                    result[name] = {
                        "price": float(latest['Close']),
                        "change_pct": float(change_pct)
                    }
                time.sleep(0.5)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_us_stock(self, symbol: str) -> dict:
        """获取美股个股"""
        if yf is None:
            return None
        try:
            import time
            hist = yf.Ticker(symbol).history(period="3d")
            if len(hist) >= 2:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                return {
                    "price": round(float(latest['Close']), 2),
                    "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2)
                }
            time.sleep(0.5)
        except Exception:
            pass
        return None

    def get_crypto(self) -> dict:
        """获取加密货币价格"""
        try:
            ids = ",".join(self.cryptos)
            url = (
                f"https://api.coingecko.com/api/v3/simple/price"
                f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
            )
            resp = requests.get(url, timeout=30)
            data = resp.json()
            result = {}
            for coin_id, info in data.items():
                result[coin_id] = {
                    "price": info.get("usd", 0),
                    "change_24h": info.get("usd_24h_change", 0)
                }
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_ai_summary(self, market_data: dict) -> str:
        """可选：使用 Gemini 生成 AI 市场总结"""
        if not self.gemini_key:
            return ""
        
        try:
            prompt = f"""你是一个专业的财经分析师。请根据以下市场数据，用中文写一段简短的市场总结（3-4句话，每句不超过30字）：

A股指数: {market_data.get('a_index', {})}
美股指数: {market_data.get('us_index', {})}
加密货币: {market_data.get('crypto', {})}

要求：
1. 语气客观冷静
2. 指出主要趋势
3. 不要给出具体投资建议
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            resp = requests.post(url, json=payload, timeout=60)
            data = resp.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
        except Exception as e:
            print(f"AI summary error: {e}")
        return ""

    def _emoji(self, val: float) -> str:
        if val > 0:
            return "🟢"
        elif val < 0:
            return "🔴"
        return "⚪"

    def format_message(self) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        lines = [
            "📊 *每日财经日报* 📊",
            f"🕐 `{now}`\n",
        ]

        market_data = {}

        # A股市场
        lines.append("🇨🇳 *A股市场*")
        a_index = self.get_a_share_index()
        market_data["a_index"] = a_index
        if "error" not in a_index and a_index:
            for name, data in a_index.items():
                price = data["price"]
                pct = data["change_pct"]
                lines.append(f"{self._emoji(pct)} {self._tg_escape(name)}: {self._tg_escape(price)} ({self._tg_escape(f'{pct:+.2f}%')})")
        else:
            lines.append("⚠️ A股数据获取失败")
        lines.append("")

        # A股自选股
        if self.stocks_a:
            lines.append("📈 *A股自选股*")
            for code in self.stocks_a:
                info = self.get_a_stock(code)
                if info:
                    name = info["name"]
                    price = info["price"]
                    pct = info["change_pct"]
                    lines.append(f"{self._emoji(pct)} {self._tg_escape(name)}({self._tg_escape(code)}): ¥{self._tg_escape(price)} ({self._tg_escape(f'{pct:+.2f}%')})")
                else:
                    lines.append(f"⚪ {self._tg_escape(code)}: 暂无数据")
            lines.append("")

        # 美股市场
        lines.append("🇺🇸 *美股市场*")
        us_index = self.get_us_index()
        market_data["us_index"] = us_index
        if "error" not in us_index and us_index:
            for name, data in us_index.items():
                price = data["price"]
                pct = data["change_pct"]
                lines.append(f"{self._emoji(pct)} {self._tg_escape(name)}: {self._tg_escape(f'{price:,.2f}')} ({self._tg_escape(f'{pct:+.2f}%')})")
        else:
            lines.append("⚠️ 美股数据获取失败")
        lines.append("")

        # 美股自选股
        if self.stocks_us:
            lines.append("📈 *美股自选股*")
            for symbol in self.stocks_us:
                info = self.get_us_stock(symbol)
                if info:
                    price = info["price"]
                    pct = info["change_pct"]
                    lines.append(f"{self._emoji(pct)} {self._tg_escape(symbol)}: ${self._tg_escape(f'{price:,.2f}')} ({self._tg_escape(f'{pct:+.2f}%')})")
                else:
                    lines.append(f"⚪ {self._tg_escape(symbol)}: 暂无数据")
            lines.append("")

        # 加密货币
        lines.append("₿ *加密货币*")
        crypto = self.get_crypto()
        market_data["crypto"] = crypto
        if "error" not in crypto and crypto:
            for coin_id, data in crypto.items():
                price = data.get("price", 0)
                change = data.get("change_24h", 0)
                display_name = coin_id.upper()[:6]
                lines.append(f"{self._emoji(change)} {self._tg_escape(display_name)}: ${self._tg_escape(f'{price:,.2f}')} ({self._tg_escape(f'{change:+.2f}% /24h')})")
        else:
            lines.append("⚠️ 加密货币数据获取失败")
        lines.append("")

        # AI 总结（可选）
        ai_text = self.get_ai_summary(market_data)
        if ai_text:
            lines.append("🤖 *AI 市场速览*")
            lines.append(self._tg_escape(ai_text))
            lines.append("")

        lines.append("💡 _数据仅供参考，不构成投资建议_")
        lines.append("🏠 [每日财经日报](https://github.com/kfat77/daily-finance-telegram)")

        return "\n".join(lines)

    def send(self) -> bool:
        if not self.tg_token or not self.tg_chat:
            print("错误：TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置")
            return False

        msg = self.format_message()
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        
        # 先尝试 MarkdownV2
        payload_md = {
            "chat_id": self.tg_chat,
            "text": msg,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True
        }
        
        try:
            resp = requests.post(url, json=payload_md, timeout=30)
            data = resp.json()
            if data.get("ok"):
                print("✅ 推送成功（MarkdownV2）！")
                return True
            else:
                print(f"⚠️ MarkdownV2 失败: {data}")
        except Exception as e:
            print(f"⚠️ MarkdownV2 请求异常: {e}")

        # 降级：发送纯文本版本
        plain_msg = self._plain_text(msg)
        payload_plain = {
            "chat_id": self.tg_chat,
            "text": plain_msg,
            "disable_web_page_preview": True
        }
        
        try:
            resp2 = requests.post(url, json=payload_plain, timeout=30)
            data2 = resp2.json()
            if data2.get("ok"):
                print("✅ 推送成功（纯文本）！")
                return True
            else:
                print(f"❌ 纯文本也失败: {data2}")
                print(f"\n📋 诊断信息：")
                print(f"   Token 前10位: {self.tg_token[:10]}...")
                print(f"   Chat ID: {self.tg_chat}")
                print(f"\n💡 请检查：")
                print("   1. TELEGRAM_BOT_TOKEN 是否填对了（不要有多余空格）")
                print("   2. TELEGRAM_CHAT_ID 是否填对了（纯数字，不要引号）")
                print("   3. 你是否给机器人发过 Start 消息（在 Telegram 里找机器人点一下 Start）")
                print("   4. 如果 Chat ID 是群组的，确认机器人已经被加入群组")
                return False
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False


if __name__ == "__main__":
    report = DailyReport()
    success = report.send()
    exit(0 if success else 1)
