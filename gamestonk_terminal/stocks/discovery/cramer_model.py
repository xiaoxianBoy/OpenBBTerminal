"""Cramer Model"""
__docformat__ = "numpy"

import re

import pandas as pd
import requests
import numpy as np
import yfinance as yf
from bs4 import BeautifulSoup

from gamestonk_terminal.helper_funcs import get_user_agent


def get_cramer_daily(inverse: bool = True) -> pd.DataFrame:
    """Scrape the daily recommendations of Jim Cramer

    Parameters
    ----------
    inverse: bool
        Whether to include inverse

    Returns
    -------
    pd.DataFrame
        Datafreme of daily Cramer recommendations
    """
    cramer_link = "https://madmoney.thestreet.com/screener/index.cfm"
    r = requests.get(cramer_link, headers={"User-Agent": get_user_agent()})
    if r.status_code != 200:
        return pd.DataFrame()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find_all("table")[0]
    trs = table.find_all("tr")
    recs = {
        "1": "Sell",
        "2": "Sell",
        "3": "Hold",
        "4": "Buy",
        "5": "Buy",
    }

    rec = []

    for tr in trs[1:]:
        rec.append(recs[tr.find_all("td")[3].find("img")["src"][-5]])

    df = pd.read_html("https://madmoney.thestreet.com/screener/index.cfm")[0]
    df["Symbol"] = df.Company.apply(lambda x: re.findall(r"[\w]+", x)[-1])
    last_price = []
    for ticker in df.Symbol:
        last_price.append(
            round(
                yf.download(ticker, period="1d", interval="1h", progress=False)[
                    "Close"
                ][-1],
                2,
            )
        )
    df["LastPrice"] = last_price
    df["Price"] = df.Price.apply(lambda x: float(x.strip("$")))
    df = df.drop(columns=["Segment", "Call", "Portfolio"])
    df["Change (%)"] = 100 * np.round((df["LastPrice"] - df["Price"]) / df.LastPrice, 4)
    df["Recommendation"] = rec
    df["Company"] = df.apply(lambda x: x.Company.replace(f"({x.Symbol})", ""), axis=1)
    cols = [
        "Date",
        "Company",
        "Symbol",
        "Price",
        "LastPrice",
        "Change (%)",
        "Recommendation",
    ]
    if inverse:
        df["InverseCramer"] = df["Recommendation"].apply(
            lambda x: ["Buy", "Sell"][x == "Buy"]
        )
        cols.append("InverseCramer")
    return df[cols]