"""This module provides a dictionary between exchange codes.

Unfortunately, the exchange codes used by Yahoo Finance (from which all market data related to prices and volume is obtained) and pandas_market_calendars are not the same. This dictionary translates between them.
"""

YFINANCE_TO_MCAL = {

    # ─────────────────────────
    # United States – Equities
    # ─────────────────────────
    "NasdaqGS": "NASDAQ",
    "NasdaqGM": "NASDAQ",
    "NasdaqCM": "NASDAQ",

    "NYSE": "NYSE",
    "BATS": "BATS",
    "IEX": "IEX",

    # Some ETFs / indices
    "DJI": "NYSE",
    "DJIA": "NYSE",

    # ─────────────────────────
    # Canada
    # ─────────────────────────
    "TSX": "TSX",
    "TSXV": "TSXV",

    # ─────────────────────────
    # United Kingdom
    # ─────────────────────────
    "LSE": "LSE",

    # ─────────────────────────
    # Europe
    # ─────────────────────────
    "XETRA": "XETR",
    "Frankfurt": "XFRA",
    "Paris": "XPAR",
    "Amsterdam": "XAMS",
    "Milan": "XMIL",
    "Madrid": "XMAD",
    "Swiss": "XSWX",
    "Stockholm": "XSTO",
    "Oslo": "XOSL",
    "Copenhagen": "XCSE",
    "Helsinki": "XHEL",
    "Vienna": "XWBO",
    "Warsaw": "XWAR",
    "Prague": "XPRA",
    "Budapest": "XBUD",

    # ─────────────────────────
    # Asia / Pacific
    # ─────────────────────────
    "JPX": "JPX",
    "Tokyo": "XTKS",

    "HKSE": "HKEX",
    "Shanghai": "SSE",
    "Shenzhen": "SSE",  # Yahoo does not distinguish calendars

    "ASX": "ASX",
    "NSE": "XNSE",
    "BSE": "BSE",

    "Korea": "XKRX",
    "TelAviv": "TASE",
    "Singapore": "XSES",
    "Jakarta": "XIDX",
    "KualaLumpur": "XKLS",
    "Bangkok": "XBKK",
    "Istanbul": "XIST",

    # ─────────────────────────
    # Latin America
    # ─────────────────────────
    "SaoPaulo": "B3",
    "Mexico": "XMEX",
    "BuenosAires": "XBUE",
    "Santiago": "XSGO",
    "Lima": "XLIM",

    # ─────────────────────────
    # Forex
    # ─────────────────────────
    "FX": "24/5",

    # ─────────────────────────
    # Crypto
    # ─────────────────────────
    "CCC": "24/7"
}