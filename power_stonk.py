import sys
import xml.etree.ElementTree as ET
import pandas as pd
import requests
import yfinance as yf

from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot, QUrl, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QDockWidget, QStyledItemDelegate, QMessageBox, QComboBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

# -------------------------------------------------------------------------
# WATCHLIST DEFINITIONS & TICKER MAPPINGS
# -------------------------------------------------------------------------
WATCHLIST_DATA = {
    "Bonds": [
        ("Corp Bond Intnl", "PICB"),
        ("Corp LT Bond", "BLV"),
        ("Corp MT Bond", "BIV"),
        ("Corp ST Bond", "BSV"),
        ("Muni local", "MUB"),
        ("US <1y Treas", "BIL"),
        ("US 1-3 year Treas", "SHY"),
        ("US 20+y Treas", "TLT"),
        ("US 7-10y Treas", "IEF"),
        ("US Agency MBS", "MBB"),
        ("US Bond Market", "AGG"),
        ("US Corp Bond IG", "LQD"),
        ("US Corp Bond HY", "HYG"),
        ("US TIPS", "TIP"),
    ],
    "Country Markets": [
        ("All-World ex US", "ACWX"),
        ("Asia", "AAXJ"),
        ("Brazil", "EWZ"),
        ("Bric", "BKF"),
        ("Canada", "EWC"),
        ("China", "FXI"),
        ("Developed Mrkts", "EFA"),
        ("EAFE", "EFA"),
        ("Emerging Mrkts 1", "EEM"),
        ("Emerging Mrkts 2", "VWO"),
        ("Emerging Small Cap", "EEMS"),
        ("Emerging Small Cap 2", "DGS"),
        ("Europe", "VGK"),
        ("Germany", "EWG"),
        ("Hong Kong", "EWH"),
        ("India", "INDA"),
        ("International", "VXUS"),
        ("International Small Cap", "GWX"),
        ("Japan", "EWJ"),
        ("Latin", "ILF"),
        ("Pacific ex Japan", "EPP"),
        ("US Stock Mrkt", "VTI"),
        ("South Korea", "EWY"),
        ("Switzerland", "EWL"),
        ("Taiwan", "EWT"),
        ("UK", "EWU"),
        ("Vang US Stock Mrkt", "VTI"),
    ],
    "Commodities": [
        ("Agribusiness", "MOO"),
        ("Aluminum", "JJU"),
        ("Basic Materials", "IYM"),
        ("Coal", "ARCH"),
        ("Cocoa US", "NIB"),
        ("Coffee US", "JO"),
        ("Copper", "CPER"),
        ("Corn US", "CORN"),
        ("Cotton US", "BAL"),
        ("Energy MLP", "AMLP"),
        ("Gold", "GLD"),
        ("Gold Miners", "GDX"),
        ("Live Cattle", "COW"),
        ("Lumber", "WOOD"),
        ("Metals & Mining", "XME"),
        ("Natural Gas", "UNG"),
        ("Natural Resources", "IGE"),
        ("O&G E&S", "XOP"),
        ("Oil Services", "OIH"),
        ("Palladium", "PALL"),
        ("Platinum", "PPLT"),
        ("Rare Earths", "REMX"),
        ("Silver", "SLV"),
        ("Silver Miners", "SIL"),
        ("Solar", "TAN"),
        ("Soybeans US", "SOYB"),
        ("Steel", "SLX"),
        ("Sugar", "CANE"),
        ("Timber & Forestry", "CUT"),
        ("Uranium", "URA"),
        ("Water", "PHO"),
        ("Wheat US", "WEAT"),
        ("Zinc", "ZINC"),
    ],
    "Industries": [
        ("Aero & Defense", "ITA"),
        ("Bank", "KBE"),
        ("Biotech", "XBI"),
        ("Cloud Computing", "CLOU"),
        ("Computer Software", "IGV"),
        ("Consumer Service", "IYC"),
        ("Cyber Security", "HACK"),
        ("Environmental Services", "EVX"),
        ("Gaming", "HERO"),
        ("Homebuilders", "XHB"),
        ("Innovation", "ARKK"),
        ("Insurance", "KIE"),
        ("Internet", "FDN"),
        ("Marijuana", "MSOS"),
        ("Medical Devices", "IHI"),
        ("Pharma", "PJP"),
        ("Real Estate US", "IYR"),
        ("Real Estate US Residential", "REZ"),
        ("Regional Banking", "KRE"),
        ("REIT Global", "REET"),
        ("REIT US", "VNQ"),
        ("Robotics", "BOTZ"),
        ("Semiconductors", "SMH"),
        ("Space", "UFO"),
        ("Technology", "XLK"),
        ("Transports", "IYT"),
    ],
    "Sectors": [
        ("Basic Materials", "XLB"),
        ("Communication Services", "XLC"),
        ("Consumer Discretionary", "XLY"),
        ("Consumer Staples", "XLP"),
        ("Energy", "XLE"),
        ("Finance", "XLF"),
        ("Health Care", "XLV"),
        ("Industrial", "XLI"),
        ("Metals & Mining", "XME"),
        ("Oil & Gas", "XOP"),
        ("Real Estate", "XLRE"),
        ("Technology", "XLK"),
        ("Utilities", "XLU"),
    ],
    "Market": [
        ("Bitcoin", "BTC-USD"),
        ("Bitcoin Trust", "GBTC"),
        ("Blockchain", "BLOK"),
        ("Cambria Momentum", "GMOM"),
        ("Cambria Tail", "TAIL"),
        ("Global Value", "GVAL"),
        ("Hussman Str Growth", "HSGFX"),
        ("MSCI US Momentum", "MTUM"),
        ("Russell 1000 Growth", "IWF"),
        ("Russell 1000 Value", "IWD"),
        ("Russell 2000 Growth", "IWO"),
        ("Russell 2000 Value", "IWN"),
        ("Russell Midcap Growth", "IWP"),
        ("Russell Midcap Value", "IWR"),
        ("S&P 400", "IJH"),
        ("S&P 400 Growth", "IJK"),
        ("S&P 400 Value", "IJJ"),
        ("S&P 500 Eq Wt", "RSP"),
        ("S&P 500 Growth", "IVW"),
        ("S&P 500 Value", "IVE"),
        ("S&P 600", "IJR"),
        ("S&P 600 Growth", "IJT"),
        ("S&P 600 Value", "IJS"),
        ("S&P Dividend", "NOBL"),
        ("Towle", "TOWLX"),
    ],
}

# -------------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------------
def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        parsed = float(str(val).replace('$', '').replace(',', '').strip())
        return parsed
    except Exception:
        return default

def get_price_fallback(info):
    return safe_float(info.get("currentPrice", info.get("regularMarketPrice", info.get("previousClose", 0))))

def get_fast_price(ticker_obj):
    """Fast lookup using fast_info to avoid heavy yfinance .info web scrapes."""
    try:
        price = ticker_obj.fast_info.get('lastPrice', ticker_obj.fast_info.get('last_price', None))
        if price is not None:
            return safe_float(price)
    except Exception:
        pass
    return get_price_fallback(ticker_obj.info)

def create_readonly_item(text=""):
    """Helper to create strictly non-selectable, non-editable table cells."""
    item = QTableWidgetItem(str(text))
    item.setFlags(Qt.ItemIsEnabled)
    return item

# -------------------------------------------------------------------------
# TRADINGVIEW WEB ENGINE CONTAINER (ANTI-BOT & MODAL FIX)
# -------------------------------------------------------------------------
class TradingViewChartWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        
        self.tv_profile = QWebEngineProfile("power_stonk_tv_profile", self)
        self.tv_profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        
        chrome_ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        self.tv_profile.setHttpUserAgent(chrome_ua)
        
        settings = self.tv_profile.settings()
        settings.setAttribute(settings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        
        self.tv_page = QWebEnginePage(self.tv_profile, self)
        self.tv_page.newWindowRequested.connect(self.handle_new_window)
        self.tv_page.loadFinished.connect(self.inject_nuke_script)
        
        self.setPage(self.tv_page)
        self.current_symbol = None
        self.load_chart("AAPL")

    def handle_new_window(self, request):
        request.openIn(self.tv_page)
        
    def inject_nuke_script(self, ok):
        if ok:
            js_code = """
            setInterval(function() {
                const dialogs = document.querySelectorAll('div[class*="dialog"], div[data-dialog-name]');
                dialogs.forEach(d => {
                    if (d.innerText.includes('Look first') || d.innerText.includes('Make every move count')) {
                        d.remove();
                    }
                });
                
                const backdrops = document.querySelectorAll('div[class*="backdrop"]');
                backdrops.forEach(b => b.remove());
            }, 2000);
            """
            self.tv_page.runJavaScript(js_code)

    def load_chart(self, symbol="AAPL"):
        if ":" not in symbol:
            symbol = f"{symbol.upper()}"
            
        if self.current_symbol == symbol:
            return
            
        self.current_symbol = symbol
        url = f"https://www.tradingview.com/chart/?symbol={symbol}"
        self.setUrl(QUrl(url))

# -------------------------------------------------------------------------
# CUSTOM PILL BADGE DELEGATE
# -------------------------------------------------------------------------
class BadgeDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        text = str(index.data() or "")
        if not text:
            return
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        bg_color, text_color = QColor("#111111"), QColor("#94a3b8")
        
        t_lower = text.lower()
        if "buy" in t_lower or "bullish" in t_lower or "undervalued" in t_lower or text.startswith("+"):
            bg_color, text_color = QColor("#00ff88"), QColor("#000000")
        elif "sell" in t_lower or "bearish" in t_lower or "overvalued" in t_lower or text.startswith("-"):
            bg_color, text_color = QColor("#ef4444"), QColor("#ffffff")
        elif "neutral" in t_lower or "option" in t_lower or "fair" in t_lower:
            bg_color, text_color = QColor("#f59e0b"), QColor("#000000")
        elif "sec form" in t_lower:
            bg_color, text_color = QColor("#3b82f6"), QColor("#ffffff")
        
        rect = option.rect.adjusted(4, 6, -4, -6)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Inter", 8, QFont.Bold))
        painter.drawText(option.rect, Qt.AlignCenter, text)
        painter.restore()

# -------------------------------------------------------------------------
# ASYNC WORKER FOR LIVE WATCHLIST
# -------------------------------------------------------------------------
class WatchlistWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, watchlist_def):
        super().__init__()
        self.watchlist_def = watchlist_def

    def run(self):
        try:
            all_tickers = list(set([t for cat in self.watchlist_def.values() for _, t in cat]))
            data = yf.download(all_tickers, period="5d", progress=False)
            
            close_data = data['Close'] if isinstance(data, dict) or 'Close' in data else data

            results = []
            for cat, items in self.watchlist_def.items():
                for name, ticker in items:
                    price, pct_change = 0.0, 0.0
                    try:
                        if isinstance(close_data, pd.DataFrame) and ticker in close_data.columns:
                            col = close_data[ticker].dropna()
                        elif hasattr(close_data, 'name') and close_data.name == ticker:
                            col = close_data.dropna()
                        else:
                            col = []

                        if len(col) >= 2:
                            price = float(col.iloc[-1])
                            prev = float(col.iloc[-2])
                            if prev != 0:
                                pct_change = ((price - prev) / prev) * 100
                        elif len(col) == 1:
                            price = float(col.iloc[-1])
                    except Exception:
                        pass
                    results.append((cat, name, ticker, price, pct_change))

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

# -------------------------------------------------------------------------
# ASYNC WORKER FOR MACRO & BREADTH
# -------------------------------------------------------------------------
class MacroWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, fred_key=""):
        super().__init__()
        self.fred_key = fred_key

    def run(self):
        try:
            macro_data = []
            
            tickers = yf.Tickers('^VIX ^GSPC ^RUT RSP')
            try:
                vix = get_fast_price(tickers.tickers['^VIX'])
                spy = get_fast_price(tickers.tickers['^GSPC'])
                rut = get_fast_price(tickers.tickers['^RUT'])
                rsp = get_fast_price(tickers.tickers['RSP'])
                
                macro_data.append(("VIX (Volatility)", f"{vix:.2f}"))
                macro_data.append(("S&P 500 (Cap-Wt)", f"{spy:,.2f}"))
                macro_data.append(("S&P 500 (Eq-Wt)", f"${rsp:,.2f}"))
                macro_data.append(("Russell 2000", f"{rut:,.2f}"))
            except Exception:
                macro_data.append(("YF Breadth", "Data Error"))

            if self.fred_key:
                endpoints = {
                    "10Y Treasury Yield": "DGS10",
                    "Fed Funds Rate": "FEDFUNDS",
                    "Unemployment Rate": "UNRATE"
                }
                for label, series_id in endpoints.items():
                    try:
                        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={self.fred_key}&file_type=json&sort_order=desc&limit=1"
                        res = requests.get(url, timeout=5)
                        if res.status_code == 200:
                            val = res.json()['observations'][0]['value']
                            macro_data.append((label, f"{float(val):.2f}%"))
                    except Exception:
                        macro_data.append((label, "N/A"))
            else:
                macro_data.append(("FRED Data", "API Key Required"))

            self.finished.emit(macro_data)
        except Exception as e:
            self.error.emit(str(e))

# -------------------------------------------------------------------------
# ASYNC WORKER FOR DATA & VALUATION MATH
# -------------------------------------------------------------------------
class DataWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, ticker, fmp_key=""):
        super().__init__()
        self.ticker = ticker.upper()
        self.fmp_key = fmp_key

    def get_sentiment(self, text):
        if not text:
            return "Neutral"
        t = str(text).lower()
        bull_words = ['buy', 'bullish', 'upgrade', 'outperform', 'surge', 'jump', 'soar', 'beat', 'growth', 'undervalued', 'profit', 'positive']
        bear_words = ['sell', 'bearish', 'downgrade', 'underperform', 'plunge', 'drop', 'fall', 'miss', 'decline', 'overvalued', 'loss', 'negative', 'lawsuit', 'investigation']
        
        bull_score = sum(1 for w in bull_words if w in t)
        bear_score = sum(1 for w in bear_words if w in t)
        
        if bull_score > bear_score:
            return "Bullish"
        elif bear_score > bull_score:
            return "Bearish"
        return "Neutral"

    def run(self):
        try:
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info or {}
            
            price = safe_float(info.get("currentPrice", info.get("regularMarketPrice")))
            beta = max(safe_float(info.get("beta"), default=1.0), 0.1)
            shares = safe_float(info.get("sharesOutstanding", 0))
            fcf = safe_float(info.get("freeCashflow", 0))
            total_debt = safe_float(info.get("totalDebt", 0))
            total_cash = safe_float(info.get("totalCash", 0))
            market_cap = safe_float(info.get("marketCap", price * shares))
            
            bvps = safe_float(info.get("bookValue", 0))
            eps = safe_float(info.get("trailingEps", 0))
            roe = safe_float(info.get("returnOnEquity", 0))
            if roe == 0 and bvps != 0:
                roe = eps / bvps
            dividend = safe_float(info.get("dividendRate", 0))

            risk_free_rate = 0.042
            market_return = 0.10
            
            erp = market_return - risk_free_rate
            cost_of_equity = risk_free_rate + (beta * erp)

            cost_of_debt = 0.05
            tax_rate = 0.21
            weight_equity = market_cap / (market_cap + total_debt) if (market_cap + total_debt) > 0 else 1
            weight_debt = total_debt / (market_cap + total_debt) if (market_cap + total_debt) > 0 else 0
            wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
            wacc = max(wacc, 0.04)

            if wacc > erp:
                discount_rate = erp
                rate_label = "ERP Override"
            else:
                discount_rate = wacc
                rate_label = "WACC Baseline"

            dcf_price = 0
            if fcf > 0 and shares > 0:
                growth_rate = 0.05
                perp_growth = 0.025
                pv_fcf = 0
                projected_fcf = fcf
                for i in range(1, 6):
                    projected_fcf *= (1 + growth_rate)
                    pv_fcf += projected_fcf / ((1 + discount_rate) ** i)
                
                terminal_value = (projected_fcf * (1 + perp_growth)) / max(discount_rate - perp_growth, 0.01)
                pv_tv = terminal_value / ((1 + discount_rate) ** 5)
                enterprise_value = pv_fcf + pv_tv
                equity_value = enterprise_value + total_cash - total_debt
                dcf_price = max(equity_value / shares, 0)

            riv_price = 0
            if bvps > 0 and roe > 0:
                current_bvps = bvps
                pv_ri = 0
                payout_ratio = max(0, min(1, (dividend / eps) if eps > 0 else 0))
                retention_ratio = 1 - payout_ratio
                
                for i in range(1, 6):
                    ri = (roe - discount_rate) * current_bvps
                    pv_ri += ri / ((1 + discount_rate) ** i)
                    current_bvps += (current_bvps * roe * retention_ratio)
                
                riv_price = max(bvps + pv_ri, 0)

            ggm_price = 0
            if dividend > 0:
                div_growth = 0.02
                if discount_rate > div_growth:
                    ggm_price = (dividend * (1 + div_growth)) / (discount_rate - div_growth)

            valid_prices = [p for p in (dcf_price, riv_price, ggm_price) if p > 0]
            blended_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
            
            valuation_status = "N/A"
            margin_safety = 0
            if price > 0 and blended_price > 0:
                margin_safety = ((blended_price - price) / price) * 100
                if margin_safety > 15:
                    valuation_status = "Undervalued"
                elif margin_safety < -15:
                    valuation_status = "Overvalued"
                else:
                    valuation_status = "Fair Value"

            valuation_data = [
                ("Current Price", f"${price:,.2f}"),
                ("Beta", f"{beta:.2f}"),
                ("WACC", f"{wacc*100:.1f}%"),
                ("Equity Risk Premium (ERP)", f"{erp*100:.1f}%"),
                ("Applied Discount Rate", f"{discount_rate*100:.1f}% ({rate_label})"),
                ("DCF Implied Price", f"${dcf_price:,.2f}" if dcf_price else "N/A (Neg FCF)"),
                ("RIV Implied Price", f"${riv_price:,.2f}" if riv_price else "N/A"),
                ("GGM Implied Price", f"${ggm_price:,.2f}" if ggm_price else "N/A (No Div)"),
                ("Blended Target Price", f"${blended_price:,.2f}" if blended_price else "N/A"),
                ("Estimated Returns", f"{margin_safety:+.1f}%" if blended_price else "N/A"),
                ("Aggregate Verdict", valuation_status)
            ]

            insider_df = ticker_obj.insider_transactions
            cleaned_insiders = []
            if insider_df is not None and not insider_df.empty:
                for idx, row in insider_df.head(20).iterrows():
                    tx_lower = str(row.to_dict()).lower()
                    action = "Sell" if 'sale' in tx_lower or 'sell' in tx_lower else "Buy" if 'purchase' in tx_lower or 'buy' in tx_lower else "Option"
                    shares_str = f"{float(row.get('Shares', 0)):,.0f}" if row.get('Shares') else "N/A"
                    cleaned_insiders.append((str(row.get('Start Date', ''))[:10], str(row.get('Insider', ''))[:20], str(row.get('Position', ''))[:15], action, shares_str))

            feed_items = []
            try:
                rss_url = f"https://news.google.com/rss/search?q={self.ticker}+stock&hl=en-US&gl=US&ceid=US:en"
                response = requests.get(rss_url, headers={'User-Agent': 'Mozilla'}, timeout=5)
                if response.status_code == 200:
                    for item in ET.fromstring(response.content).findall('.//item')[:15]:
                        title = item.find('title').text
                        sentiment = self.get_sentiment(title)
                        feed_items.append((item.find('pubDate').text[:16], "Google News", sentiment, title, item.find('link').text))
            except Exception:
                pass

            if self.fmp_key:
                try:
                    fmp_url = f"https://financialmodelingprep.com/api/v3/sec_filings/{self.ticker}?limit=15&apikey={self.fmp_key}"
                    fmp_res = requests.get(fmp_url, timeout=5)
                    if fmp_res.status_code == 200:
                        filings = fmp_res.json()
                        for f in filings:
                            dt = str(f.get('fillingDate', ''))[:16]
                            f_type = f.get('type', 'Filing')
                            link = f.get('finalLink', '')
                            title = f"{self.ticker} SEC Filing: {f_type}"
                            sentiment = self.get_sentiment(title)
                            feed_items.append((dt, f"SEC Form {f_type}", sentiment, title, link))
                except Exception:
                    pass
            
            feed_items.sort(key=lambda x: x[0], reverse=True)

            self.finished.emit({
                'symbol': self.ticker,
                'valuation': valuation_data,
                'insiders': cleaned_insiders,
                'feed_items': feed_items
            })
        except Exception as e:
            self.error.emit(str(e))

# -------------------------------------------------------------------------
# MAIN WORKSPACE WINDOW
# -------------------------------------------------------------------------
class ProTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trilly's Stonk Terminal")
        self.resize(1800, 1000)
        
        self.raw_watchlist_results = []
        
        self.setStyleSheet("""
            QMainWindow { background-color: #030303; }
            QDockWidget { color: #00ff88; font-family: 'JetBrains Mono', monospace; font-weight: bold; font-size: 10pt; }
            QDockWidget::title { background: #0a0a0a; padding: 10px; border: 1px solid #1a1a1a; }
            QWidget { background-color: #050505; color: #f8fafc; font-family: 'Inter', sans-serif; }
            QLineEdit { background-color: #0a0a0a; border: 1px solid #1a1a1a; padding: 8px; color: #00ff88; font-weight: bold; font-size: 10pt;}
            QComboBox { background-color: #0a0a0a; border: 1px solid #1a1a1a; padding: 6px; color: #00ff88; font-weight: bold; cursor: pointer; }
            QPushButton { background-color: #00ff88; color: #000000; font-weight: bold; border-radius: 2px; padding: 10px; cursor: pointer; }
            QPushButton:hover { background-color: #00cc6a; }
            QTableWidget { background-color: #050505; border: 1px solid #1a1a1a; gridline-color: #111111; font-size: 9pt; }
            QTableWidget::item:selected { background-color: transparent; }
            QHeaderView::section { background-color: #0a0a0a; color: #64748b; padding: 6px; border: none; font-weight: bold; }
        """)

        self.watchlist_timer = QTimer(self)
        self.watchlist_timer.setInterval(300000)
        self.watchlist_timer.timeout.connect(self.run_watchlist_update)

        self.setup_ui()

    def setup_ui(self):
        self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)

        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)

        self.tv_chart = TradingViewChartWidget()
        self.setCentralWidget(self.tv_chart)

        # --- SETTINGS DOCK ---
        dock_tools = QDockWidget("SETTINGS", self)
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        
        tools_layout.addWidget(QLabel("TICKER:", styleSheet="color: #64748b; font-weight: bold;"))
        self.ticker_entry = QLineEdit("AAPL")
        self.ticker_entry.returnPressed.connect(self.run_update)
        tools_layout.addWidget(self.ticker_entry)

        tools_layout.addWidget(QLabel("FMP API KEY (SEC Filings):", styleSheet="color: #64748b; font-weight: bold; margin-top: 10px;"))
        self.fmp_entry = QLineEdit()
        self.fmp_entry.setEchoMode(QLineEdit.Password)
        self.fmp_entry.setPlaceholderText("Paste API key here...")
        tools_layout.addWidget(self.fmp_entry)

        self.exec_btn = QPushButton("Fetch Data")
        self.exec_btn.setCursor(Qt.PointingHandCursor)
        self.exec_btn.clicked.connect(self.run_update)
        self.exec_btn.setStyleSheet("margin-top: 10px;")
        tools_layout.addWidget(self.exec_btn)
        
        tools_layout.addWidget(QLabel("WATCHLIST REFRESH RATE:", styleSheet="color: #64748b; font-weight: bold; margin-top: 15px;"))
        self.watchlist_interval_combo = QComboBox()
        self.watchlist_interval_combo.setCursor(Qt.PointingHandCursor)
        self.watchlist_interval_combo.addItems(["1 Min", "3 Mins", "5 Mins (Default)", "10 Mins", "15 Mins", "30 Mins"])
        self.watchlist_interval_combo.setCurrentIndex(2)
        self.watchlist_interval_combo.currentIndexChanged.connect(self.on_watchlist_interval_change)
        tools_layout.addWidget(self.watchlist_interval_combo)

        self.wl_refresh_btn = QPushButton("REFRESH WATCHLIST NOW")
        self.wl_refresh_btn.setCursor(Qt.PointingHandCursor)
        self.wl_refresh_btn.clicked.connect(self.run_watchlist_update)
        self.wl_refresh_btn.setStyleSheet("background-color: #10b981; color: black; margin-top: 5px;")
        tools_layout.addWidget(self.wl_refresh_btn)

        tools_layout.addWidget(QLabel("MACRO & BREADTH", styleSheet="color: #00ff88; font-family: 'JetBrains Mono'; font-weight: bold; margin-top: 15px;"))
        
        self.macro_table = QTableWidget(0, 2)
        self.macro_table.horizontalHeader().setVisible(False)
        self.macro_table.verticalHeader().setVisible(False)
        self.macro_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.macro_table.setStyleSheet("QTableWidget { background-color: #0a0a0a; font-size: 8pt; }")
        self.macro_table.setMaximumHeight(150)
        tools_layout.addWidget(self.macro_table)

        tools_layout.addWidget(QLabel("FRED API KEY (Macro Data):", styleSheet="color: #64748b; font-weight: bold; margin-top: 5px;"))
        self.fred_entry = QLineEdit()
        self.fred_entry.setEchoMode(QLineEdit.Password)
        self.fred_entry.setPlaceholderText("Paste FRED key...")
        tools_layout.addWidget(self.fred_entry)
        
        self.macro_btn = QPushButton("LOAD MACRO DATA")
        self.macro_btn.setCursor(Qt.PointingHandCursor)
        self.macro_btn.clicked.connect(self.run_macro_update)
        self.macro_btn.setStyleSheet("background-color: #3b82f6; color: white;")
        tools_layout.addWidget(self.macro_btn)

        tools_layout.addStretch()
        dock_tools.setWidget(tools_widget)

        # --- LIVE WATCHLIST DOCK ---
        dock_watchlist = QDockWidget("LIVE WATCHLIST", self)
        wl_widget = QWidget()
        wl_layout = QVBoxLayout(wl_widget)
        
        filter_box = QHBoxLayout()
        self.wl_cat_filter = QComboBox()
        self.wl_cat_filter.setCursor(Qt.PointingHandCursor)
        self.wl_cat_filter.addItems(["All Categories"] + list(WATCHLIST_DATA.keys()))
        self.wl_cat_filter.currentIndexChanged.connect(self.apply_watchlist_filters)
        
        self.wl_search = QLineEdit()
        self.wl_search.setPlaceholderText("Search name/ticker...")
        self.wl_search.textChanged.connect(self.apply_watchlist_filters)
        
        filter_box.addWidget(self.wl_cat_filter)
        filter_box.addWidget(self.wl_search)
        wl_layout.addLayout(filter_box)

        self.table_watchlist = QTableWidget(0, 5)
        self.table_watchlist.setHorizontalHeaderLabels(["Category", "Name", "Ticker", "Price", "Change %"])
        self.table_watchlist.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_watchlist.setItemDelegateForColumn(4, BadgeDelegate())
        self.table_watchlist.itemDoubleClicked.connect(self.on_watchlist_item_clicked)
        wl_layout.addWidget(self.table_watchlist)
        
        dock_watchlist.setWidget(wl_widget)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock_tools)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_watchlist)
        self.splitDockWidget(dock_tools, dock_watchlist, Qt.Vertical)

        # --- VALUATION DOCK ---
        dock_val = QDockWidget("VALUATION", self)
        self.table_val = QTableWidget(0, 2)
        self.table_val.horizontalHeader().setVisible(False)
        self.table_val.verticalHeader().setVisible(False)
        self.table_val.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_val.setItemDelegateForColumn(1, BadgeDelegate())
        dock_val.setWidget(self.table_val)

        # --- INSIDER TRANSACTIONS DOCK ---
        dock_insiders = QDockWidget("INSIDER TRANSACTIONS", self)
        self.table_insiders = QTableWidget(0, 5)
        self.table_insiders.setHorizontalHeaderLabels(["Date", "Insider", "Position", "Action", "Shares"])
        self.table_insiders.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_insiders.setItemDelegateForColumn(3, BadgeDelegate())
        dock_insiders.setWidget(self.table_insiders)

        self.addDockWidget(Qt.RightDockWidgetArea, dock_val)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_insiders)
        self.splitDockWidget(dock_val, dock_insiders, Qt.Vertical)

        # --- NEWS FEED DOCK ---
        dock_news = QDockWidget("NEWS FEED", self)
        self.table_news = QTableWidget(0, 4)
        self.table_news.setHorizontalHeaderLabels(["Date", "Source", "Sentiment", "Headline / URL"])
        self.table_news.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_news.setItemDelegateForColumn(1, BadgeDelegate())
        self.table_news.setItemDelegateForColumn(2, BadgeDelegate())
        self.table_news.cellClicked.connect(self.on_news_cell_clicked)
        dock_news.setWidget(self.table_news)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_news)

        # Completely lock down tables: disable cell editing, row/text selection, and focus boxes
        for tbl in [self.macro_table, self.table_watchlist, self.table_val, self.table_insiders, self.table_news]:
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl.setSelectionMode(QTableWidget.NoSelection)
            tbl.setFocusPolicy(Qt.NoFocus)
            tbl.horizontalHeader().setSectionsClickable(False)
            tbl.viewport().setCursor(Qt.PointingHandCursor)

        self.resizeDocks([dock_tools, dock_watchlist], [320, 320], Qt.Horizontal)
        self.resizeDocks([dock_val, dock_insiders], [340, 340], Qt.Horizontal)
        self.resizeDocks([dock_news], [280], Qt.Vertical)

        # Initial Updates
        self.run_update()
        self.run_macro_update()
        self.run_watchlist_update()
        self.watchlist_timer.start()

    # --- WATCHLIST TIMER & UPDATES ---
    def on_watchlist_interval_change(self, idx):
        intervals = [60000, 180000, 300000, 600000, 900000, 1800000]
        ms = intervals[idx]
        self.watchlist_timer.setInterval(ms)

    def run_watchlist_update(self):
        self.wl_refresh_btn.setText("UPDATING...")
        self.wl_refresh_btn.setEnabled(False)
        
        self.wl_thread = QThread()
        self.wl_worker = WatchlistWorker(WATCHLIST_DATA)
        self.wl_worker.moveToThread(self.wl_thread)
        self.wl_thread.started.connect(self.wl_worker.run)
        self.wl_worker.finished.connect(self.on_watchlist_ready)
        self.wl_worker.error.connect(self.on_watchlist_error)
        self.wl_thread.start()

    @Slot(list)
    def on_watchlist_ready(self, results):
        self.wl_thread.quit()
        self.wl_thread.wait()
        self.wl_refresh_btn.setText("REFRESH WATCHLIST NOW")
        self.wl_refresh_btn.setEnabled(True)
        self.raw_watchlist_results = results
        self.apply_watchlist_filters()

    @Slot(str)
    def on_watchlist_error(self, err_msg):
        self.wl_thread.quit()
        self.wl_thread.wait()
        self.wl_refresh_btn.setText("REFRESH WATCHLIST NOW")
        self.wl_refresh_btn.setEnabled(True)
        print(f"Watchlist Error: {err_msg}")

    def apply_watchlist_filters(self):
        selected_cat = self.wl_cat_filter.currentText()
        search_query = self.wl_search.text().strip().lower()

        filtered = []
        for cat, name, ticker, price, pct in self.raw_watchlist_results:
            if selected_cat != "All Categories" and cat != selected_cat:
                continue
            if search_query and (search_query not in name.lower() and search_query not in ticker.lower()):
                continue
            filtered.append((cat, name, ticker, price, pct))

        self.table_watchlist.setRowCount(len(filtered))
        for r, (cat, name, ticker, price, pct) in enumerate(filtered):
            item_cat = create_readonly_item(cat)
            self.table_watchlist.setItem(r, 0, item_cat)
            
            item_name = create_readonly_item(name)
            self.table_watchlist.setItem(r, 1, item_name)
            
            t_item = create_readonly_item(ticker)
            t_item.setFont(QFont("Inter", 9, QFont.Bold))
            self.table_watchlist.setItem(r, 2, t_item)
            
            p_str = f"${price:,.2f}" if price > 0 else "N/A"
            item_price = create_readonly_item(p_str)
            self.table_watchlist.setItem(r, 3, item_price)
            
            pct_str = f"{pct:+.2f}%" if price > 0 else "N/A"
            pct_item = create_readonly_item(pct_str)
            pct_item.setData(Qt.DisplayRole, pct_str)
            self.table_watchlist.setItem(r, 4, pct_item)

    def on_watchlist_item_clicked(self, item):
        row = item.row()
        ticker = self.table_watchlist.item(row, 2).text().strip()
        if ticker:
            self.ticker_entry.setText(ticker)
            self.run_update()

    # --- MACRO UPDATES ---
    def run_macro_update(self):
        fred_key = self.fred_entry.text().strip()
        self.macro_btn.setText("LOADING...")
        self.macro_btn.setEnabled(False)
        
        self.macro_thread = QThread()
        self.macro_worker = MacroWorker(fred_key)
        self.macro_worker.moveToThread(self.macro_thread)
        self.macro_thread.started.connect(self.macro_worker.run)
        self.macro_worker.finished.connect(self.on_macro_ready)
        self.macro_worker.error.connect(self.on_macro_error)
        self.macro_thread.start()
    
    def on_macro_ready(self, macro_data):
        self.macro_thread.quit()
        self.macro_thread.wait()
        self.macro_btn.setText("LOAD MACRO DATA")
        self.macro_btn.setEnabled(True)
        
        self.macro_table.setRowCount(len(macro_data))
        for r, (metric, val) in enumerate(macro_data):
            item_metric = create_readonly_item(metric)
            item_metric.setForeground(QBrush(QColor("#64748b")))
            item_metric.setFont(QFont("Inter", 9, QFont.Bold))
            
            item_val = create_readonly_item(val)
            if "Error" in str(val) or "Required" in str(val):
                item_val.setForeground(QBrush(QColor("#ef4444")))
            else:
                item_val.setForeground(QBrush(QColor("#f8fafc")))
                
            self.macro_table.setItem(r, 0, item_metric)
            self.macro_table.setItem(r, 1, item_val)
    
    def on_macro_error(self, err_msg):
        self.macro_thread.quit()
        self.macro_thread.wait()
        self.macro_btn.setText("LOAD MACRO DATA")
        self.macro_btn.setEnabled(True)
        print(f"Macro Error: {err_msg}")

    # --- MAIN TICKER UPDATES ---
    def run_update(self):
        ticker = self.ticker_entry.text().strip().upper()
        fmp_key = self.fmp_entry.text().strip()
        if not ticker:
            return
        
        self.tv_chart.load_chart(symbol=ticker)

        self.exec_btn.setText("CALCULATING...")
        self.exec_btn.setEnabled(False)
        
        self.worker_thread = QThread()
        self.worker = DataWorker(ticker, fmp_key)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_data_ready)
        self.worker.error.connect(self.on_error)
        self.worker_thread.start()

    @Slot(dict)
    def on_data_ready(self, data):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.exec_btn.setText("Fetch Data")
        self.exec_btn.setEnabled(True)
        
        self.populate_valuation(data['valuation'])
        self.populate_insiders(data['insiders'])
        self.populate_news(data['feed_items'])

    @Slot(str)
    def on_error(self, err_msg):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.exec_btn.setText("Fetch Data")
        self.exec_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", err_msg)

    def populate_valuation(self, val_data):
        self.table_val.setRowCount(len(val_data))
        for r, (metric, val) in enumerate(val_data):
            item_metric = create_readonly_item(metric)
            item_metric.setForeground(QBrush(QColor("#64748b")))
            item_metric.setFont(QFont("Inter", 10, QFont.Bold))
            
            item_val = create_readonly_item(val)
            if metric == "Margin of Safety":
                item_val.setData(Qt.DisplayRole, str(val))
            
            self.table_val.setItem(r, 0, item_metric)
            self.table_val.setItem(r, 1, item_val)

    def populate_insiders(self, insiders):
        self.table_insiders.setRowCount(len(insiders))
        for r, row in enumerate(insiders):
            for c, val in enumerate(row):
                item = create_readonly_item(val)
                self.table_insiders.setItem(r, c, item)

    def populate_news(self, items):
        self.table_news.setRowCount(len(items))
        for idx, (dt, src, sent, title, link) in enumerate(items):
            item_dt = create_readonly_item(dt)
            self.table_news.setItem(idx, 0, item_dt)
            
            item_src = create_readonly_item(src)
            item_src.setData(Qt.DisplayRole, src)
            self.table_news.setItem(idx, 1, item_src)
            
            item_sent = create_readonly_item(sent)
            self.table_news.setItem(idx, 2, item_sent)
            
            t_item = create_readonly_item(title)
            t_item.setData(Qt.UserRole, link)
            t_item.setForeground(QBrush(QColor("#38bdf8")))
            self.table_news.setItem(idx, 3, t_item)

    def on_news_cell_clicked(self, row, col):
        if col == 3:
            url = self.table_news.item(row, col).data(Qt.UserRole)
            if url:
                QDesktopServices.openUrl(QUrl(url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = ProTerminal()
    terminal.showMaximized()
    sys.exit(app.exec())