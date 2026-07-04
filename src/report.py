import os
import requests
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    yf = None


class DailyReport:
    def __init__(self):
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.tg_chat = os.getenv("TELEGRAM_CHAT_ID", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        stocks_a_raw = os.getenv("STOCK_LIST_A", "")
        self.stocks_a = [s.strip() for s in stocks_a_raw.split(",") if s.strip()] if stocks_a_raw else []
        
        stocks_us_raw = os.getenv("STOCK_LIST_US", "")
        self.stocks_us = [s.strip() for s in stocks_us_raw.split(",") if s.strip()] if stocks_us_raw else []
        
        crypto_raw = os.getenv("CRYPTO_LIST", "bitcoin,ethereum")
        self.cryptos = [s.strip() for s in crypto_raw.split(",") if s.strip()] if crypto_raw else ["bitcoin", "ethereum"]

    def _tg_escape(self, text: str) -> str:
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return ''.join('\\' + c if c in escape_chars else c for c in str(text))

    def _plain_text(self, text: str) -> str:
        for esc in ['\\*', '\\_', '\\`', '\\.', '\\[', '\\]', '\\(', '\\)', '\\-', '\\+', '\\=', '\\|', '\\{', '\\}', '\\!', '\\~', '\\>', '\\#']:
            text = text.replace(esc, esc[-1])
        for md in ['*', '_', '`']:
            text = text.replace(md, '')
        return text

    def get_a_share_index(self) -> dict:
        """用 yfinance 获取 A股主要指数（ETF 代理）"""
        if yf is None:
            return {"error": "yfinance not installed"}
        try:
            import time
            tickers = {
                "上证指数": "000001.SS",
                "深证成指": "399001.SZ",
                "创业板指": "399006.SZ"
            }
            result = {}
            for name, symbol in tickers.items():
                hist = yf.Ticker(symbol).history(period="3d")
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change_pct = (latest['Close'] - prev['Close']) / prev['Close'] * 100
                    result[name] = {
                        "price": round(float(latest['Close']), 2),
                        "change_pct": round(float(change_pct), 2)
                    }
                time.sleep(0.5)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_a_stock(self, code: str) -> dict:
        """用 yfinance 获取 A股个股"""
        if yf is None:
            return None
        try:
            import time
            suffix = ".SS" if code.startswith("6") else ".SZ"
            hist = yf.Ticker(code + suffix).history(period="3d")
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

    def get_us_index(self) -> dict:
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
                        "price": round(float(latest['Close']), 2),
                        "change_pct": round(float(change_pct), 2)
                    }
                time.sleep(0.5)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_us_stock(self, symbol: str) -> dict:
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
        try:
            ids = ",".join(self.cryptos)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
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

    def get_finance_news(self) -> list:
        """获取新浪财经要闻（修复编码）"""
        try:
            url = "https://finance.sina.com.cn/news/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=30)
            # 修复编码：新浪用 GBK
            resp.encoding = 'gbk'
            content = resp.text
            import re
            titles = re.findall(r'<a[^>]*href="/cn/[^"]*"[^>]*>([^<]{10,60})</a>', content)
            if not titles:
                titles = re.findall(r'target="_blank">([^<]{10,60})</a>', content)
            return list(dict.fromkeys(titles))[:5]
        except Exception:
            return []

    def get_market_summary(self, a_index: dict, us_index: dict, crypto: dict) -> str:
        """基于规则生成市场速览（不需要 AI API）"""
        parts = []
        a_up = a_up_count = 0
        if a_index and "error" not in a_index:
            for v in a_index.values():
                if v.get("change_pct", 0) > 0:
                    a_up_count += 1
            a_up = a_up_count >= 2
            
        us_up = us_up_count = 0
        if us_index and "error" not in us_index:
            for v in us_index.values():
                if v.get("change_pct", 0) > 0:
                    us_up_count += 1
            us_up = us_up_count >= 2
            
        crypto_up = False
        if crypto and "error" not in crypto:
            total_change = sum(v.get("change_24h", 0) for v in crypto.values()) / max(len(crypto), 1)
            crypto_up = total_change > 0
        
        if a_up and us_up:
            parts.append("A股与美股同步走强，全球市场风险偏好回升")
        elif a_up and not us_up:
            parts.append("A股独立走强，美股有所回调")
        elif not a_up and us_up:
            parts.append("美股延续强势，A股承压调整")
        else:
            parts.append("全球主要市场普遍承压，避险情绪升温")
        
        if crypto_up:
            parts.append("加密货币市场延续反弹，资金流入积极")
        else:
            parts.append("加密货币市场调整，投资者情绪谨慎")
        
        parts.append("建议关注资金流向与政策面变化，保持理性")
        
        return "；".join(parts) + "。"

    def get_ai_summary(self, market_data: dict) -> str:
        """使用 Gemini 生成 AI 市场总结"""
        if not self.gemini_key:
            return ""
        try:
            a_str = str(market_data.get('a_index', {}))[:200]
            us_str = str(market_data.get('us_index', {}))[:200]
            c_str = str(market_data.get('crypto', {}))[:200]
            
            prompt = f"""你是一个资深财经分析师，用中文写一段市场速览（3-4句话，生动、有洞察力，带一点情绪判断但不要给出投资建议）：

A股指数涨跌：{a_str}
美股指数涨跌：{us_str}
加密货币涨跌：{c_str}

要求：
1. 像财经主播一样说话，生动不刻板
2. 对比中美市场差异
3. 指出最值得关注的趋势
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
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
                    price = info["price"]
                    pct = info["change_pct"]
                    lines.append(f"{self._emoji(pct)} {self._tg_escape(code)}: ¥{self._tg_escape(price)} ({self._tg_escape(f'{pct:+.2f}%')})")
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

        # AI 市场速览（如果配置了 Gemini）
        ai_text = self.get_ai_summary(market_data)
        if ai_text:
            lines.append("🤖 *AI 市场速览*")
            lines.append(self._tg_escape(ai_text))
            lines.append("")
        else:
            # 没有 AI Key 时，用规则版速览
            lines.append("📰 *市场速览*")
            summary = self.get_market_summary(a_index, us_index, crypto)
            lines.append(self._tg_escape(summary))
            lines.append("")

        # 财经要闻
        lines.append("📢 *财经要闻*")
        news = self.get_finance_news()
        if news:
            for i, title in enumerate(news[:3], 1):
                lines.append(f"{i}\. {self._tg_escape(title)}")
        else:
            lines.append("⚠️ 要闻获取失败")
        lines.append("")

        lines.append("💡 _数据仅供参考，不构成投资建议_")

        return "\n".join(lines)

    def send(self) -> bool:
        if not self.tg_token or not self.tg_chat:
            print("错误：TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置")
            return False

        msg = self.format_message()
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        
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
                print("✅ 推送成功！")
                return True
            else:
                print(f"⚠️ MarkdownV2 失败: {data}")
        except Exception as e:
            print(f"⚠️ MarkdownV2 请求异常: {e}")

        # 降级纯文本
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
                return False
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False


if __name__ == "__main__":
    report = DailyReport()
    success = report.send()
    exit(0 if success else 1)
