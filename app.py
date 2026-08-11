# -*- coding: utf-8 -*-
"""
CANSLIM TERMINAL  v4.0
윌리엄 오닐(William J. O'Neil) 기법 통합 투자 참고 터미널

구성
  대시보드 · 시장(3지수 FTD/분산일/매수적합도) · 개별종목(베이스~매도신호)
  환율(기간별 전략/평균분석/환전시기) · 뉴스(신뢰기관 필터+시사점)
  누적 스캔 · 정밀 보강 · 사용 가이드

실행:  streamlit run app.py
"""
from __future__ import annotations

import json
import math
import os
import re
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

st.set_page_config(page_title="CANSLIM TERMINAL", page_icon="■",
                   layout="wide", initial_sidebar_state="expanded")

try:
    import FinanceDataReader as fdr
    HAS_FDR = True
except Exception:
    HAS_FDR = False
try:
    import yfinance as yf
    HAS_YF = True
except Exception:
    HAS_YF = False
try:
    from pykrx import stock as krx
    HAS_KRX = True
except Exception:
    HAS_KRX = False


# ════════════════════════════════════════════════════════════════════════════
# 디자인 — 밝은 리서치 노트 스타일 (가시성 우선)
# ════════════════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Serif+KR:wght@600;700&display=swap');

:root{
  --paper:#FAF9F6; --card:#FFFFFF; --wash:#F3F0EA; --line:#E2DED5; --line2:#CFC9BC;
  --ink:#16181C; --ink2:#4E555D; --ink3:#7A828B;
  --accent:#8A5A00; --accent-bg:#FDF6E7;
  --up:#0B7A52; --up-bg:#E9F5F0; --down:#B3261E; --down-bg:#FBECEA;
  --info:#1F4E79; --info-bg:#ECF2F8;
}
html, body, [class*="css"], .stApp{ font-family:'Pretendard',system-ui,sans-serif; }
.stApp{ background:var(--paper); color:var(--ink); }
section[data-testid="stSidebar"]{ background:var(--card); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] *{ color:var(--ink); }
[data-testid="stHeader"]{ background:transparent; }
.block-container{ padding-top:2rem; max-width:1400px; }

h1,h2,h3{ color:var(--ink); }
.stTabs [data-baseweb="tab-list"]{ gap:2px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"]{ background:transparent; color:var(--ink3); font-weight:600;
  font-size:.86rem; padding:.55rem 1rem; border-radius:6px 6px 0 0; }
.stTabs [aria-selected="true"]{ background:var(--card); color:var(--accent);
  border:1px solid var(--line); border-bottom:2px solid var(--accent); }

.mono{ font-family:'IBM Plex Mono',monospace; font-variant-numeric:tabular-nums; }

.masthead{ border-bottom:2px solid var(--ink); padding:.1rem 0 .7rem; margin-bottom:1.1rem; }
.masthead h1{ font-family:'Noto Serif KR',serif; font-size:1.5rem; font-weight:700;
  letter-spacing:-.02em; margin:0; color:var(--ink); }
.masthead .sub{ font-family:'IBM Plex Mono',monospace; font-size:.68rem; letter-spacing:.18em;
  text-transform:uppercase; color:var(--ink3); margin-top:.3rem; }

.step{ display:flex; align-items:baseline; gap:.7rem; margin:1.8rem 0 .7rem;
  border-top:1px solid var(--line2); padding-top:.75rem; }
.step .no{ font-family:'IBM Plex Mono',monospace; font-size:.68rem; font-weight:600;
  color:var(--accent); letter-spacing:.1em; min-width:72px; }
.step .ti{ font-family:'Noto Serif KR',serif; font-size:1.05rem; font-weight:700; color:var(--ink); }
.step .note{ font-size:.75rem; color:var(--ink3); margin-left:auto; text-align:right; }

.card{ background:var(--card); border:1px solid var(--line); border-radius:8px;
  padding:.85rem 1rem; height:100%; box-shadow:0 1px 2px rgba(20,20,20,.04); }
.card .k{ font-family:'IBM Plex Mono',monospace; font-size:.64rem; letter-spacing:.12em;
  text-transform:uppercase; color:var(--ink3); }
.card .v{ font-family:'IBM Plex Mono',monospace; font-size:1.22rem; font-weight:600;
  margin-top:.2rem; color:var(--ink); line-height:1.25; }
.card .d{ font-size:.73rem; color:var(--ink2); margin-top:.25rem; line-height:1.5; }

.big{ background:var(--card); border:1px solid var(--line); border-left:5px solid var(--accent);
  border-radius:8px; padding:1.1rem 1.3rem; }
.big .k{ font-family:'IBM Plex Mono',monospace; font-size:.66rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--ink3); }
.big .v{ font-family:'Noto Serif KR',serif; font-size:1.8rem; font-weight:700; margin:.2rem 0; }
.big .d{ font-size:.82rem; color:var(--ink2); line-height:1.6; }

.tag{ display:inline-block; font-family:'IBM Plex Mono',monospace; font-size:.69rem;
  padding:.16rem .5rem; border-radius:4px; letter-spacing:.03em; font-weight:600; }
.t-pass{ background:var(--up-bg); color:var(--up); border:1px solid #A8D5C2; }
.t-fail{ background:var(--down-bg); color:var(--down); border:1px solid #EFB8B2; }
.t-warn{ background:var(--accent-bg); color:var(--accent); border:1px solid #E5CE9A; }
.t-idle{ background:var(--wash); color:var(--ink2); border:1px solid var(--line2); }
.t-info{ background:var(--info-bg); color:var(--info); border:1px solid #B9CDE0; }
.up{color:var(--up);} .down{color:var(--down);} .amb{color:var(--accent);}
.mut{color:var(--ink3);} .ink2{color:var(--ink2);}

.read{ background:var(--accent-bg); border:1px solid #EBDCB8; border-radius:8px;
  padding:.85rem 1rem; margin:.7rem 0 .3rem; font-size:.84rem; line-height:1.75; color:var(--ink); }
.read b{ color:var(--accent); }
.read .h{ font-family:'IBM Plex Mono',monospace; font-size:.63rem; letter-spacing:.15em;
  color:var(--accent); text-transform:uppercase; display:block; margin-bottom:.4rem; font-weight:600; }
.oneil{ background:var(--info-bg); border:1px solid #C6D8E7; }
.oneil .h{ color:var(--info); } .oneil b{ color:var(--info); }

.ev{ font-family:'IBM Plex Mono',monospace; font-size:.72rem; color:var(--ink2);
  padding:.16rem 0; border-bottom:1px dotted var(--line); }
.ev b{ color:var(--ink); font-weight:600; }

.xs{ position:relative; height:78px; background:var(--card); border:1px solid var(--line);
  border-radius:8px; margin:.6rem 0 1rem; }
.xs .zone{ position:absolute; top:0; bottom:0; background:rgba(138,90,0,.10);
  border-left:1px solid var(--accent); border-right:1px dashed rgba(138,90,0,.45); }
.xs .lvl{ position:absolute; top:8px; bottom:8px; width:1px; background:var(--line2); }
.xs .lbl{ position:absolute; top:7px; font-family:'IBM Plex Mono',monospace; font-size:.62rem;
  color:var(--ink3); transform:translateX(-50%); white-space:nowrap; }
.xs .val{ position:absolute; bottom:9px; font-family:'IBM Plex Mono',monospace; font-size:.66rem;
  color:var(--ink2); transform:translateX(-50%); white-space:nowrap; }
.xs .now{ position:absolute; top:0; bottom:0; width:2px; background:var(--ink); }

table.chk{ width:100%; border-collapse:collapse; font-size:.81rem; background:var(--card);
  border:1px solid var(--line); border-radius:8px; overflow:hidden; }
table.chk th{ font-family:'IBM Plex Mono',monospace; font-size:.63rem; letter-spacing:.1em;
  text-transform:uppercase; color:var(--ink3); text-align:left; background:var(--wash);
  border-bottom:1px solid var(--line); padding:.45rem .6rem; font-weight:600; }
table.chk td{ border-bottom:1px solid var(--line); padding:.45rem .6rem;
  vertical-align:top; color:var(--ink); }
table.chk td.n{ font-family:'IBM Plex Mono',monospace; }
table.chk td.m{ color:var(--ink2); font-size:.76rem; }
table.chk tr:last-child td{ border-bottom:none; }

.news{ background:var(--card); border:1px solid var(--line); border-radius:8px;
  padding:.7rem .9rem; margin-bottom:.5rem; }
.news .src{ font-family:'IBM Plex Mono',monospace; font-size:.64rem; color:var(--accent);
  letter-spacing:.06em; font-weight:600; }
.news .ti{ font-size:.87rem; font-weight:600; margin:.2rem 0; line-height:1.45; }
.news .ti a{ color:var(--ink); text-decoration:none; }
.news .ti a:hover{ color:var(--accent); text-decoration:underline; }
.news .mt{ font-size:.71rem; color:var(--ink3); }

.hint{ font-size:.78rem; color:var(--ink2); line-height:1.65; }
.quote{ border-left:3px solid var(--line2); padding:.15rem 0 .15rem .8rem;
  font-size:.77rem; color:var(--ink3); margin:.6rem 0; line-height:1.65; }
.bar{ height:9px; background:var(--wash); border-radius:5px; overflow:hidden;
  border:1px solid var(--line); margin-top:.35rem; }
.bar > div{ height:100%; }
div[data-testid="stMetricValue"]{ font-family:'IBM Plex Mono',monospace; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# 차트 팔레트 (밝은 배경 기준)
P_INK, P_INK2, P_LINE = "#16181C", "#4E555D", "#E2DED5"
P_ACC, P_UP, P_DOWN, P_INFO = "#8A5A00", "#0B7A52", "#B3261E", "#1F4E79"
P_BG = "#FFFFFF"

US_INDICES = [("^DJI", "다우존스"), ("^GSPC", "S&P 500"), ("^IXIC", "나스닥")]
KR_INDICES = [("KS11", "코스피"), ("KQ11", "코스닥")]

WATCH_DEFAULT = ["NVDA", "TSLA", "GEV", "TSM", "VRT", "DELL", "SKHY",
                 "AMD", "MRVL", "BE", "CRDO", "MU", "WDC", "SNDK"]
WATCH_FILE = "watchlist.json"

UNIVERSE_US = """AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO LLY JPM V UNH XOM MA JNJ PG COST HD ABBV
WMT NFLX CRM BAC KO PEP AMD ADBE TMO LIN MRK CVX ACN MCD CSCO ABT ORCL DHR WFC TXN
INTU IBM QCOM NOW GE CAT AMGN PFE UNP ISRG SPGI RTX BKNG HON UBER PGR LOW T
BLK SYK AMAT ELV TJX VRTX MDT LMT ADI PLD REGN SCHW MU C BSX CB ETN MMC ADP
KLAC PANW SNPS CDNS MRVL CRWD FTNT ANET DELL SMCI ON MCHP NXPI TER ENPH FSLR GEV VRT CRDO WDC
COIN SHOP ABNB DASH SNOW DDOG NET ZS OKTA TTD ROKU PINS SPOT PLTR RBLX U TEAM MDB HUBS
CEG VST NRG TLN BE PWR NEE DUK SO AEP SLB HAL OXY COP EOG PSX MPC VLO FANG DVN
TSM ASML ARM AZN NVO SHEL BABA JD PDD SE NU MELI STLA TM SONY UL SAP TTE RIO BHP
DE BA GD NOC LHX EMR ITW PH ROK CMI FDX UPS DAL UAL MAR HLT CMG SBUX NKE LULU
DIS CMCSA VZ TMUS ORLY AZO ROST DG DLTR KR SYY MNST KDP STZ GIS K HSY CL KMB""".split()

SECTOR_ETF = {"Technology": "XLK", "Communication Services": "XLC", "Consumer Cyclical": "XLY",
              "Consumer Defensive": "XLP", "Energy": "XLE", "Financial Services": "XLF",
              "Healthcare": "XLV", "Industrials": "XLI", "Basic Materials": "XLB",
              "Real Estate": "XLRE", "Utilities": "XLU"}

# 뉴스 신뢰 기관 화이트리스트
TRUSTED_US = ["reuters", "bloomberg", "wall street journal", "wsj", "financial times",
              "barron", "cnbc", "associated press", "ap news", "investor's business daily",
              "investors business daily", "marketwatch", "yahoo finance", "the economist",
              "nikkei", "forbes", "business insider", "axios", "fortune"]
TRUSTED_KR = ["연합뉴스", "한국경제", "매일경제", "서울경제", "이데일리", "머니투데이",
              "파이낸셜뉴스", "조선비즈", "아시아경제", "헤럴드경제", "뉴시스", "더벨",
              "전자신문", "한겨레", "중앙일보", "동아일보", "KBS", "MBC", "SBS"]

NEWS_TOPICS = [
    ("실적·가이던스", ["실적", "영업이익", "매출", "어닝", "가이던스", "컨센서스", "흑자", "적자",
                   "earnings", "revenue", "guidance", "profit", "beats", "misses", "eps"], "C·A"),
    ("신제품·기술", ["신제품", "출시", "개발", "양산", "특허", "차세대",
                  "launch", "unveil", "new product", "next-gen", "chip", "model"], "N"),
    ("수주·계약", ["수주", "계약", "공급", "파트너", "협력", "납품",
                 "contract", "deal", "order", "partnership", "supply agreement"], "N"),
    ("증설·투자", ["증설", "설비투자", "공장", "capex", "capacity", "fab", "plant", "expansion"], "A"),
    ("애널리스트", ["목표주가", "투자의견", "상향", "하향", "매수의견",
                 "price target", "upgrade", "downgrade", "analyst", "rating"], "L"),
    ("기관·수급", ["지분", "매입", "매도", "자사주", "배당", "액면",
                "stake", "buyback", "dividend", "institutional", "hedge fund"], "I"),
    ("M&A", ["인수", "합병", "매각", "지분인수", "acquire", "merger", "acquisition", "spin"], "N"),
    ("규제·소송", ["규제", "소송", "제재", "조사", "과징금", "리콜", "관세",
                "lawsuit", "regulator", "probe", "fine", "recall", "tariff", "antitrust", "ban"], "리스크"),
    ("공급망·비용", ["공급망", "원자재", "가격인상", "감산", "재고",
                  "supply chain", "shortage", "inventory", "price hike", "cost"], "리스크"),
    ("인사·조직", ["대표", "사임", "선임", "구조조정", "감원",
                "ceo", "resign", "appoint", "layoff", "restructur"], "리스크"),
]
POS_WORDS = ["상향", "호조", "최대", "신기록", "돌파", "수주", "흑자전환", "급증", "확대", "성공",
             "beat", "record", "surge", "upgrade", "raise", "strong", "win", "approval", "jump"]
NEG_WORDS = ["하향", "부진", "감소", "적자", "소송", "리콜", "제재", "축소", "지연", "우려",
             "miss", "cut", "downgrade", "fall", "plunge", "delay", "probe", "lawsuit", "weak"]


# ════════════════════════════════════════════════════════════════════════════
# 유틸
# ════════════════════════════════════════════════════════════════════════════
def is_kr_code(t):
    t = str(t).strip()
    return t.isdigit() and len(t) == 6


def kr_tick(p):
    if p < 2000: return 1
    if p < 5000: return 5
    if p < 20000: return 10
    if p < 50000: return 50
    if p < 200000: return 100
    if p < 500000: return 500
    return 1000


def round_tick(p, market, up=True):
    if p is None or (isinstance(p, float) and (np.isnan(p) or np.isinf(p))):
        return p
    if market != "KR":
        return round(float(p), 2)
    t = kr_tick(p)
    return int((math.ceil(p / t) if up else math.floor(p / t)) * t)


def fmt(v, market="KR", dec=None):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "—"
    if market == "KR":
        return f"{v:,.0f}"
    return f"{v:,.{2 if dec is None else dec}f}"


def unit(m):
    return "원" if m == "KR" else "$"


def pct(v, dec=1, sign=True):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "—"
    return f"{v:+.{dec}f}%" if sign else f"{v:.{dec}f}%"


def num(v, dec=1):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "—"
    return f"{v:,.{dec}f}"


def tag(t, k="idle"):
    return f'<span class="tag t-{k}">{t}</span>'


def verdict(ok, yes="충족", no="미충족"):
    return tag(yes if ok else no, "pass" if ok else "fail")


def step_header(no, title, note=""):
    st.markdown(f'<div class="step"><div class="no">{no}</div><div class="ti">{title}</div>'
                f'<div class="note">{note}</div></div>', unsafe_allow_html=True)


def card(k, v, d="", cls=""):
    return (f'<div class="card"><div class="k">{k}</div><div class="v {cls}">{v}</div>'
            f'<div class="d">{d}</div></div>')


def bigcard(k, v, d="", cls=""):
    return (f'<div class="big"><div class="k">{k}</div><div class="v {cls}">{v}</div>'
            f'<div class="d">{d}</div></div>')


def read_box(text, head="해석", style=""):
    cls = "read oneil" if style == "oneil" else "read"
    st.markdown(f'<div class="{cls}"><span class="h">{head}</span>{text}</div>',
                unsafe_allow_html=True)


def table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="chk"><tr>{th}</tr>{tb}</table>'


def evidence(items):
    """근거 목록 — (라벨, 측정값, 기준, 충족여부)"""
    out = []
    for lab, meas, std, ok in items:
        mark = '<span class="up">충족</span>' if ok else '<span class="down">미달</span>'
        out.append(f'<div class="ev">[{mark}] <b>{lab}</b> · 측정 {meas} · 기준 {std}</div>')
    return "".join(out)


def bar(v, maxv=100, color=None):
    color = color or P_ACC
    w = max(0, min(100, v / maxv * 100))
    return f'<div class="bar"><div style="width:{w}%;background:{color}"></div></div>'


def naive(df):
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df = df.copy()
        df.index = df.index.tz_localize(None)
    return df


def safe(v, d=None):
    try:
        f = float(v)
        return d if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return d


# ════════════════════════════════════════════════════════════════════════════
# 데이터 레이어
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def load_price(ticker):
    """상장 이후 전 구간 일봉. (df, market, name, log)"""
    t = str(ticker).strip().upper()
    log = []
    if is_kr_code(t):
        df, src = None, ""
        if HAS_FDR:
            try:
                d = fdr.DataReader(t)
                if d is not None and len(d) > 60:
                    df, src = naive(d), "FinanceDataReader"
            except Exception as e:
                log.append(("일봉", "재시도", f"FDR: {type(e).__name__}"))
        if df is None and HAS_KRX:
            try:
                d = krx.get_market_ohlcv("19950101", datetime.today().strftime("%Y%m%d"), t)
                d = d.rename(columns={"시가": "Open", "고가": "High", "저가": "Low",
                                      "종가": "Close", "거래량": "Volume"})
                if len(d) > 60:
                    df, src = naive(d), "pykrx"
            except Exception as e:
                log.append(("일봉", "실패", f"pykrx: {type(e).__name__}"))
        if df is None:
            return None, "KR", t, log
        name = t
        if HAS_KRX:
            try:
                nm = krx.get_market_ticker_name(t)
                if nm:
                    name = f"{nm} ({t})"
            except Exception:
                pass
        log.append(("일봉", "성공", f"{src} · {len(df):,}일 ({df.index[0]:%Y-%m-%d}~)"))
        return df, "KR", name, log

    df, src, name = None, "", t
    if HAS_YF:
        for how in ("history", "download"):
            try:
                if how == "history":
                    d = yf.Ticker(t).history(period="max", auto_adjust=True)
                else:
                    d = yf.download(t, period="max", progress=False, auto_adjust=True)
                    if isinstance(d.columns, pd.MultiIndex):
                        d.columns = d.columns.droplevel(1)
                if d is not None and len(d) > 60:
                    df, src = naive(d), f"yfinance({how})"
                    break
            except Exception as e:
                log.append(("일봉", "재시도", f"yfinance {how}: {type(e).__name__}"))
    if df is None and HAS_FDR:
        try:
            d = fdr.DataReader(t)
            if d is not None and len(d) > 60:
                df, src = naive(d), "FinanceDataReader"
        except Exception as e:
            log.append(("일봉", "실패", f"FDR: {type(e).__name__}"))
    if df is None:
        return None, "US", t, log
    try:
        nm = yf.Ticker(t).info.get("shortName")
        if nm:
            name = f"{nm} ({t})"
    except Exception:
        pass
    log.append(("일봉", "성공", f"{src} · {len(df):,}일 ({df.index[0]:%Y-%m-%d}~)"))
    return df, "US", name, log


@st.cache_data(ttl=900, show_spinner=False)
def load_indices(market):
    """시장 지수 — 미국은 다우/S&P/나스닥 3종"""
    out, log = {}, []
    start = (datetime.today() - timedelta(days=1300)).strftime("%Y-%m-%d")
    for code, nm in (KR_INDICES if market == "KR" else US_INDICES):
        got = None
        if market == "KR" and HAS_FDR:
            try:
                got = naive(fdr.DataReader(code, start))
            except Exception:
                pass
        if got is None and HAS_YF:
            try:
                d = yf.Ticker(code).history(start=start, auto_adjust=False)
                got = naive(d) if d is not None and not d.empty else None
            except Exception:
                pass
        if got is None and HAS_FDR and market != "KR":
            try:
                alt = {"^DJI": "DJI", "^GSPC": "US500", "^IXIC": "IXIC"}.get(code)
                if alt:
                    got = naive(fdr.DataReader(alt, start))
            except Exception:
                pass
        if got is not None and len(got) > 150 and "Volume" in got.columns:
            out[nm] = got
            log.append((f"지수 {nm}", "성공", f"{len(got):,}일"))
        elif got is not None and len(got) > 150:
            got = got.copy()
            got["Volume"] = np.nan
            out[nm] = got
            log.append((f"지수 {nm}", "부분", "거래량 없음 — 분산일 판정 제한"))
        else:
            log.append((f"지수 {nm}", "실패", "소스 응답 없음"))
    return out, log


def _to_num(x):
    try:
        s = str(x).replace(",", "").replace("%", "").replace("원", "").strip()
        if s in ("", "-", "nan", "None"):
            return None
        return float(s)
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_kr_fund(ticker):
    F = {k: None for k in ["q_eps", "q_eps_prev", "y_eps", "y_eps_prev2", "q_sales", "roe",
                           "debt", "opm", "npm", "per", "pbr", "psr", "peg", "mktcap",
                           "eps_ttm", "bps", "div", "shares", "sector", "inst", "insider",
                           "float", "fper"]}
    F.update({"table": None, "q_series": None, "y_series": None, "q_tab": None,
              "y_tab": None, "log": [], "src": []})
    raw = None
    try:
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        html = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}).text
        for t in pd.read_html(html):
            cols = [" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
            if "연간" in " ".join(cols) and "분기" in " ".join(cols):
                t = t.copy(); t.columns = cols; raw = t
                break
    except Exception as e:
        F["log"].append(("KR 실적표", "실패", f"네이버 접속 불가: {type(e).__name__}"))

    if raw is not None:
        F["table"] = raw
        F["src"].append("네이버 기업실적분석")
        F["log"].append(("KR 실적표", "성공", "네이버 기업실적분석"))
        key = raw.columns[0]
        raw[key] = raw[key].astype(str)

        def row(nm):
            m = raw[raw[key].str.replace(" ", "").str.contains(nm, na=False)]
            return m.iloc[0] if len(m) else None

        ycol = [c for c in raw.columns[1:] if "연간" in c and "(E)" not in c]
        qcol = [c for c in raw.columns[1:] if "분기" in c and "(E)" not in c]

        def series(rn, cols):
            r = row(rn)
            if r is None:
                return None
            return pd.Series({c.split()[-1]: _to_num(r[c]) for c in cols}).dropna()

        def multi(names, cols):
            d = {}
            for nm in names:
                s = series(nm, cols)
                if s is not None and len(s):
                    d[nm] = s
            if not d:
                return None
            t = pd.DataFrame(d).T
            t.columns = [str(c) for c in t.columns]
            return t

        MET = ["매출액", "영업이익", "당기순이익", "EPS", "ROE", "영업이익률", "부채비율"]
        F["q_tab"] = multi(MET, qcol)
        F["y_tab"] = multi(MET, ycol)
        for t in (F["q_tab"], F["y_tab"]):
            if t is not None and "당기순이익" in t.index:
                t.rename(index={"당기순이익": "순이익"}, inplace=True)
        F["q_series"], F["y_series"] = series("EPS", qcol), series("EPS", ycol)
        qs, ys = F["q_series"], F["y_series"]
        if qs is not None and len(qs) >= 5:
            F["q_eps"], F["q_eps_prev"] = float(qs.iloc[-1]), float(qs.iloc[-5])
        if ys is not None and len(ys) >= 2:
            F["y_eps"], F["y_eps_prev2"] = float(ys.iloc[-1]), float(ys.iloc[-2])
        sq = series("매출액", qcol)
        if sq is not None and len(sq) >= 5 and sq.iloc[-5] > 0:
            F["q_sales"] = float(sq.iloc[-1] / sq.iloc[-5] - 1) * 100
        for k, nm in [("roe", "ROE"), ("debt", "부채비율"), ("opm", "영업이익률"),
                      ("npm", "순이익률"), ("per", "PER"), ("pbr", "PBR")]:
            s = series(nm, ycol)
            if s is not None and len(s):
                F[k] = float(s.iloc[-1])

    if HAS_KRX:
        try:
            end = datetime.today().strftime("%Y%m%d")
            st0 = (datetime.today() - timedelta(days=20)).strftime("%Y%m%d")
            f = krx.get_market_fundamental(st0, end, ticker)
            if f is not None and not f.empty:
                F["per"] = F["per"] or safe(f["PER"].iloc[-1])
                F["pbr"] = F["pbr"] or safe(f["PBR"].iloc[-1])
                F["eps_ttm"], F["bps"] = safe(f["EPS"].iloc[-1]), safe(f["BPS"].iloc[-1])
                F["div"] = safe(f["DIV"].iloc[-1])
                if F["roe"] is None and F["bps"]:
                    F["roe"] = F["eps_ttm"] / F["bps"] * 100
                F["src"].append("pykrx(KRX 공시)")
                F["log"].append(("KR 밸류에이션", "성공", "pykrx"))
            cap = krx.get_market_cap(st0, end, ticker)
            if cap is not None and not cap.empty:
                F["mktcap"] = safe(cap["시가총액"].iloc[-1])
                F["shares"] = safe(cap["상장주식수"].iloc[-1])
        except Exception as e:
            F["log"].append(("KR 밸류에이션", "실패", type(e).__name__))
    return F


def _us_tab(stmt):
    """yfinance 손익계산서 → 지표×기간 테이블(한글 지표명)"""
    mp = {"Total Revenue": "매출액", "Operating Income": "영업이익",
          "Net Income": "순이익", "Diluted EPS": "EPS"}
    rows = {}
    for eng, kor in mp.items():
        hit = [r for r in stmt.index if str(r) == eng or eng in str(r)]
        if hit:
            s = stmt.loc[hit[0]].astype(float)
            rows[kor] = {c.strftime("%Y-%m") if hasattr(c, "strftime") else str(c): v
                         for c, v in s.items()}
    if not rows:
        return None
    t = pd.DataFrame(rows).T
    return t[sorted(t.columns)]


@st.cache_data(ttl=3600, show_spinner=False)
def load_us_fund(ticker):
    F = {k: None for k in ["q_eps", "q_eps_prev", "y_eps", "y_eps_prev2", "q_sales", "roe",
                           "debt", "opm", "npm", "per", "fper", "pbr", "psr", "peg", "mktcap",
                           "inst", "insider", "float", "shares", "sector", "industry",
                           "eps_ttm", "bps", "div", "next_earnings"]}
    F.update({"table": None, "q_series": None, "y_series": None, "q_tab": None,
              "y_tab": None, "log": [], "src": []})
    if not HAS_YF:
        return F
    tk = yf.Ticker(ticker)
    info = {}
    for _ in range(2):
        try:
            info = tk.info or {}
            if len(info) > 5:
                break
        except Exception:
            continue
    if info:
        F["per"], F["fper"] = safe(info.get("trailingPE")), safe(info.get("forwardPE"))
        F["pbr"], F["psr"] = safe(info.get("priceToBook")), safe(info.get("priceToSalesTrailing12Months"))
        F["peg"] = safe(info.get("trailingPegRatio")) or safe(info.get("pegRatio"))
        F["mktcap"] = safe(info.get("marketCap"))
        F["roe"] = (safe(info.get("returnOnEquity")) or 0) * 100 or None
        F["opm"] = (safe(info.get("operatingMargins")) or 0) * 100 or None
        F["npm"] = (safe(info.get("profitMargins")) or 0) * 100 or None
        F["debt"] = safe(info.get("debtToEquity"))
        F["inst"] = (safe(info.get("heldPercentInstitutions")) or 0) * 100 or None
        F["insider"] = (safe(info.get("heldPercentInsiders")) or 0) * 100 or None
        F["float"], F["shares"] = safe(info.get("floatShares")), safe(info.get("sharesOutstanding"))
        F["sector"], F["industry"] = info.get("sector"), info.get("industry")
        F["div"] = (safe(info.get("dividendYield")) or 0) or None
        F["src"].append("yfinance info")
        F["log"].append(("US 기업정보", "성공", "yfinance info"))
    else:
        F["log"].append(("US 기업정보", "실패", "info 응답 없음(요청 제한 가능)"))
    try:
        cal = tk.calendar
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if ed:
                F["next_earnings"] = pd.to_datetime(ed[0] if isinstance(ed, list) else ed)
        elif cal is not None and not cal.empty and "Earnings Date" in cal.index:
            F["next_earnings"] = pd.to_datetime(cal.loc["Earnings Date"].iloc[0])
    except Exception:
        pass
    try:
        q = tk.quarterly_income_stmt
        if q is not None and not q.empty:
            q = q.iloc[:, ::-1]
            er = [r for r in q.index if "Diluted EPS" in str(r)]
            if er:
                s = q.loc[er[0]].astype(float).dropna()
                F["q_series"] = s
                if len(s) >= 5:
                    F["q_eps"], F["q_eps_prev"] = float(s.iloc[-1]), float(s.iloc[-5])
            rv = [r for r in q.index if str(r) == "Total Revenue"]
            if rv:
                s = q.loc[rv[0]].astype(float).dropna()
                if len(s) >= 5 and s.iloc[-5] > 0:
                    F["q_sales"] = float(s.iloc[-1] / s.iloc[-5] - 1) * 100
            keep = [r for r in q.index if str(r) in
                    ("Total Revenue", "Operating Income", "Net Income", "Diluted EPS")]
            if keep:
                F["table"] = q.loc[keep]
                F["q_tab"] = _us_tab(q)
            F["src"].append("yfinance 분기 손익")
            F["log"].append(("US 분기실적", "성공", "quarterly_income_stmt"))
    except Exception as e:
        F["log"].append(("US 분기실적", "실패", type(e).__name__))
    try:
        a = tk.income_stmt
        if a is not None and not a.empty:
            a = a.iloc[:, ::-1]
            r = [x for x in a.index if "Diluted EPS" in str(x)]
            if r:
                s = a.loc[r[0]].astype(float).dropna()
                F["y_series"] = s
                if len(s) >= 2:
                    F["y_eps"], F["y_eps_prev2"] = float(s.iloc[-1]), float(s.iloc[-2])
            F["y_tab"] = _us_tab(a)
    except Exception:
        pass
    return F


@st.cache_data(ttl=3600, show_spinner=False)
def load_kr_flow(ticker, days=60):
    if not HAS_KRX:
        return None
    try:
        end = datetime.today().strftime("%Y%m%d")
        st0 = (datetime.today() - timedelta(days=days * 2)).strftime("%Y%m%d")
        return krx.get_market_trading_value_by_date(st0, end, ticker).tail(days)
    except Exception:
        return None


@st.cache_data(ttl=21600, show_spinner=False)
def load_rs_universe(market):
    try:
        if market == "KR":
            if not HAS_KRX:
                return None
            today, base = datetime.today(), {}
            for k, d in [("r3", 92), ("r6", 183), ("r9", 274), ("r12", 365)]:
                ch = krx.get_market_price_change((today - timedelta(days=d)).strftime("%Y%m%d"),
                                                 today.strftime("%Y%m%d"), market="ALL")
                base[k] = ch["등락률"]
            return pd.DataFrame(base).dropna()
        if not HAS_YF:
            return None
        px = yf.download(UNIVERSE_US, period="400d", progress=False,
                         auto_adjust=True)["Close"].dropna(how="all", axis=1)
        out = {}
        for k, n in [("r3", 63), ("r6", 126), ("r9", 189), ("r12", 252)]:
            if len(px) > n:
                out[k] = (px.iloc[-1] / px.iloc[-n - 1] - 1) * 100
        return pd.DataFrame(out).dropna()
    except Exception:
        return None


@st.cache_data(ttl=21600, show_spinner=False)
def load_sector_rank(market, sector=None):
    try:
        if market == "US" and HAS_YF and sector in SECTOR_ETF:
            px = yf.download(list(SECTOR_ETF.values()), period="200d", progress=False,
                             auto_adjust=True)["Close"].dropna(how="all", axis=1)
            r = ((px.iloc[-1] / px.iloc[-126] - 1) * 100).sort_values(ascending=False)
            etf = SECTOR_ETF[sector]
            if etf in r.index:
                inv = {v: k for k, v in SECTOR_ETF.items()}
                return {"rank": int(list(r.index).index(etf)) + 1, "total": len(r),
                        "ret": float(r[etf]), "label": f"{sector} ({etf})",
                        "top": [inv.get(x, x) for x in r.index[:3]]}
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_fx():
    """USD/KRW 장기 시계열 + 달러인덱스"""
    log, fx, dxy = [], None, None
    start = (datetime.today() - timedelta(days=365 * 11)).strftime("%Y-%m-%d")
    if HAS_FDR:
        try:
            d = fdr.DataReader("USD/KRW", start)
            if d is not None and len(d) > 500:
                fx = naive(d)
                log.append(("환율 USD/KRW", "성공", f"FDR · {len(fx):,}일"))
        except Exception as e:
            log.append(("환율 USD/KRW", "재시도", f"FDR: {type(e).__name__}"))
    if fx is None and HAS_YF:
        try:
            d = yf.Ticker("KRW=X").history(start=start, auto_adjust=False)
            if d is not None and len(d) > 500:
                fx = naive(d)
                log.append(("환율 USD/KRW", "성공", f"yfinance · {len(fx):,}일"))
        except Exception as e:
            log.append(("환율 USD/KRW", "실패", type(e).__name__))
    if HAS_YF:
        try:
            d = yf.Ticker("DX-Y.NYB").history(period="3y", auto_adjust=False)
            if d is not None and len(d) > 200:
                dxy = naive(d)
                log.append(("달러인덱스", "성공", "yfinance"))
        except Exception:
            log.append(("달러인덱스", "실패", "선택 항목"))
    return fx, dxy, log


@st.cache_data(ttl=1800, show_spinner=False)
def load_news(ticker, market, limit=40):
    """신뢰 기관 뉴스만 수집"""
    items, log = [], []
    trusted = TRUSTED_KR if market == "KR" else TRUSTED_US

    if HAS_YF:
        cands = [ticker]
        if market == "KR":
            cands = [f"{ticker}.KS", f"{ticker}.KQ"]
        for c in cands:
            try:
                raw = yf.Ticker(c).news or []
            except Exception:
                raw = []
            for n in raw[:limit]:
                ct = n.get("content") if isinstance(n.get("content"), dict) else n
                title = ct.get("title") or n.get("title")
                prov = ct.get("provider") or {}
                pub = (prov.get("displayName") if isinstance(prov, dict) else None) \
                    or n.get("publisher") or ""
                url = n.get("link")
                if not url:
                    cu = ct.get("canonicalUrl") or ct.get("clickThroughUrl") or {}
                    url = cu.get("url") if isinstance(cu, dict) else None
                ts = n.get("providerPublishTime") or ct.get("pubDate")
                try:
                    when = (datetime.fromtimestamp(ts) if isinstance(ts, (int, float))
                            else pd.to_datetime(ts).tz_localize(None))
                except Exception:
                    when = None
                if title and pub:
                    items.append({"title": str(title), "pub": str(pub),
                                  "url": url, "when": when})
            if items:
                break
        if items:
            log.append(("뉴스", "성공", f"yfinance · 원본 {len(items)}건"))

    if market == "KR" and not items:
        try:
            url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1"
            html = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).text
            links = dict(re.findall(r'href="(/item/news_read[^"]+)"[^>]*>\s*([^<]{5,})', html))
            for t in pd.read_html(html):
                cols = [str(c) for c in t.columns]
                if any("정보제공" in c for c in cols) and any("제목" in c for c in cols):
                    tcol = [c for c in cols if "제목" in c][0]
                    pcol = [c for c in cols if "정보제공" in c][0]
                    dcol = [c for c in cols if "날짜" in c]
                    for _, r in t.iterrows():
                        ttl = str(r[tcol]).strip()
                        if ttl in ("nan", ""):
                            continue
                        when = None
                        if dcol:
                            try:
                                when = pd.to_datetime(str(r[dcol[0]]))
                            except Exception:
                                pass
                        href = next((k for k, v in links.items() if v.strip()[:15] in ttl), None)
                        items.append({"title": ttl, "pub": str(r[pcol]).strip(),
                                      "url": ("https://finance.naver.com" + href) if href else None,
                                      "when": when})
            if items:
                log.append(("뉴스", "성공", f"네이버 금융 · 원본 {len(items)}건"))
        except Exception as e:
            log.append(("뉴스", "실패", f"네이버: {type(e).__name__}"))

    seen, keep = set(), []
    for it in items:
        low = it["pub"].lower()
        if not any(s in low for s in trusted):
            continue
        k = it["title"][:40]
        if k in seen:
            continue
        seen.add(k)
        keep.append(it)
    keep.sort(key=lambda x: x["when"] or datetime(1970, 1, 1), reverse=True)
    if not keep and items:
        log.append(("뉴스 필터", "부분", f"수집 {len(items)}건 중 신뢰기관 0건"))
    elif keep:
        log.append(("뉴스 필터", "성공", f"신뢰기관 {len(keep)}건 선별"))
    return keep[:25], log


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ① 시장 — FTD · 분산일 · 매수 적합도
# ════════════════════════════════════════════════════════════════════════════
def distribution_days(df, lookback=25):
    d = df.tail(lookback + 1).copy()
    if d["Volume"].isna().all():
        return []
    d["chg"] = d["Close"].pct_change() * 100
    last = float(d["Close"].iloc[-1])
    out = []
    for i in range(1, len(d)):
        if d["chg"].iloc[i] <= -0.2 and d["Volume"].iloc[i] > d["Volume"].iloc[i - 1]:
            if last < float(d["Close"].iloc[i]) * 1.05:
                out.append({"date": d.index[i], "chg": float(d["chg"].iloc[i]),
                            "close": float(d["Close"].iloc[i])})
    return out


def detect_ftd(df, min_gain=1.2, corr_pct=4.0, lookback=520):
    d = df.tail(lookback).copy()
    d["chg"] = d["Close"].pct_change() * 100
    novol = d["Volume"].isna().all()
    dd = (d["Close"] / d["Close"].cummax() - 1) * 100
    below = (dd <= -corr_pct).values
    if not below.any():
        return {"state": "no_correction", "max_dd": float(dd.min()), "date": None,
                "cur_dd": float(dd.iloc[-1])}
    s = int(np.where(below)[0][-1])
    while s > 0 and dd.values[s - 1] < -0.5:
        s -= 1
    low_pos = s + int(np.argmin(d["Close"].values[s:]))
    low_close = float(d["Close"].iloc[low_pos])
    ftd, i = None, low_pos + 1
    while i < len(d):
        if d["Close"].iloc[i] < low_close:
            low_pos, low_close = i, float(d["Close"].iloc[i])
            i += 1
            continue
        n = i - low_pos + 1
        volok = True if novol else bool(d["Volume"].iloc[i] > d["Volume"].iloc[i - 1])
        if n >= 4 and d["chg"].iloc[i] >= min_gain and volok:
            ftd = {"date": d.index[i], "gain": float(d["chg"].iloc[i]), "day": n,
                   "low_date": d.index[low_pos], "low_close": low_close}
            break
        i += 1
    if ftd is None:
        return {"state": "rally_attempt", "low_date": d.index[low_pos], "date": None,
                "low_close": low_close, "rally_day": len(d) - low_pos,
                "max_dd": float(dd.min()), "cur_dd": float(dd.iloc[-1])}
    post = d.loc[ftd["date"]:]
    ftd.update({"state": "failed" if bool((post["Close"] < ftd["low_close"]).any()) else "confirmed",
                "since": int((d.index[-1] - ftd["date"]).days),
                "ret_since": float(d["Close"].iloc[-1] / d.loc[ftd["date"], "Close"] - 1) * 100,
                "max_dd": float(dd.min()), "cur_dd": float(dd.iloc[-1])})
    return ftd


def index_state(idf, min_gain, corr_pct):
    ftd = detect_ftd(idf, min_gain, corr_pct)
    dds = distribution_days(idf)
    c = idf["Close"]
    px = float(c.iloc[-1])
    ma50 = float(c.rolling(50).mean().iloc[-1]) if len(idf) > 50 else np.nan
    ma200 = float(c.rolling(200).mean().iloc[-1]) if len(idf) > 200 else np.nan
    ab50, ab200 = px > ma50, px > ma200
    chg = float(c.iloc[-1] / c.iloc[-2] - 1) * 100
    n = len(dds)
    if not ab200:
        label, kind, why = "조정 국면", "fail", "지수가 200일선 아래"
    elif ftd["state"] in ("confirmed", "no_correction") and n <= 3:
        label, kind, why = "확정된 상승세", "pass", "FTD 유효 · 분산일 관리 중"
    elif ftd["state"] in ("confirmed", "no_correction") and n <= 5:
        label, kind, why = "압박받는 상승세", "warn", f"분산일 {n}개 누적"
    elif ftd["state"] == "rally_attempt":
        label, kind, why = "랠리 시도 중", "warn", "FTD 미확인"
    else:
        label, kind, why = "조정 국면", "fail", "FTD 실패 또는 분산 과다"
    return {"ftd": ftd, "dds": dds, "dd_n": n, "ma50": ma50, "ma200": ma200,
            "ab50": ab50, "ab200": ab200, "chg": chg, "px": px,
            "label": label, "kind": kind, "why": why, "df": idf}


def buy_window(states, breadth=None):
    """오늘이 매수하기 좋은 날인가 — 0~100 적합도"""
    ks = [s["kind"] for s in states.values()]
    kmap = {"pass": 40, "warn": 20, "fail": 0}
    s_regime = np.mean([kmap[k] for k in ks])

    dd_avg = np.mean([s["dd_n"] for s in states.values()])
    if dd_avg <= 2: s_dd = 20
    elif dd_avg <= 3: s_dd = 14
    elif dd_avg <= 4: s_dd = 8
    elif dd_avg <= 5: s_dd = 4
    else: s_dd = 0

    sinces = [s["ftd"].get("since") for s in states.values()
              if s["ftd"].get("state") == "confirmed" and s["ftd"].get("since") is not None]
    if sinces:
        d0 = min(sinces)
        if d0 <= 3: s_ftd, ftd_txt = 11, f"FTD 후 {d0}일 — 확인 직후"
        elif d0 <= 35: s_ftd, ftd_txt = 15, f"FTD 후 {d0}일 — 신규 돌파 집중 구간"
        elif d0 <= 70: s_ftd, ftd_txt = 10, f"FTD 후 {d0}일 — 중반부"
        else: s_ftd, ftd_txt = 6, f"FTD 후 {d0}일 — 상승세 후반"
    else:
        allnc = all(s["ftd"].get("state") == "no_correction" for s in states.values())
        s_ftd = 12 if allnc else 0
        ftd_txt = "조정 없이 상승 지속" if allnc else "유효한 FTD 없음"

    trend = np.mean([(1 if s["ab50"] else 0) + (1 if s["ab200"] else 0)
                     for s in states.values()]) / 2
    s_trend = trend * 15

    chg_avg = np.mean([s["chg"] for s in states.values()])
    if chg_avg <= -1.5: s_day = 0
    elif chg_avg < 0: s_day = 6
    elif chg_avg <= 2: s_day = 10
    else: s_day = 7

    total = int(round(s_regime + s_dd + s_ftd + s_trend + s_day))
    if total >= 75: grade, kind = "적극 매수 가능", "pass"
    elif total >= 55: grade, kind = "선별 매수", "warn"
    elif total >= 35: grade, kind = "소극 · 관망", "warn"
    else: grade, kind = "신규 매수 보류", "fail"

    parts = [("시장 국면", f"{s_regime:.0f}/40",
              " · ".join(f'{k} {v["label"]}' for k, v in states.items())),
             ("분산일", f"{s_dd}/20", f"지수 평균 {dd_avg:.1f}개 (6개 이상 위험)"),
             ("FTD 경과", f"{s_ftd}/15", ftd_txt),
             ("추세 정렬", f"{s_trend:.0f}/15",
              f'50·200일선 상회 비율 {trend*100:.0f}%'),
             ("당일 시장", f"{s_day}/10", f"지수 평균 {pct(chg_avg,2)}")]
    if breadth is not None:
        parts.append(("시장 폭(참고)", "—", f'3개월 상승 종목 비율 {breadth:.0f}%'))
    return {"score": total, "grade": grade, "kind": kind, "parts": parts}


def buy_window_series(states, days=120):
    """최근 구간 매수 적합도 추이 (분산일·추세·당일 기준 근사)"""
    try:
        frames = []
        for nm, s in states.items():
            d = s["df"].tail(days + 260).copy()
            d["chg"] = d["Close"].pct_change() * 100
            d["ma50"] = d["Close"].rolling(50).mean()
            d["ma200"] = d["Close"].rolling(200).mean()
            novol = d["Volume"].isna().all()
            ddflag = ((d["chg"] <= -0.2) &
                      ((d["Volume"] > d["Volume"].shift(1)) if not novol else True)).astype(int)
            d["ddn"] = ddflag.rolling(25).sum()
            sc = pd.Series(0.0, index=d.index)
            sc += np.where(d["Close"] > d["ma200"], 25, 0)
            sc += np.where(d["Close"] > d["ma50"], 20, 0)
            sc += np.clip(20 - d["ddn"].fillna(0) * 3.5, 0, 20)
            sc += np.where(d["chg"] > 0, 10, np.where(d["chg"] > -1.5, 5, 0))
            frames.append(sc.tail(days))
        out = pd.concat(frames, axis=1).mean(axis=1).dropna()
        return (out * 100 / 75).clip(0, 100)
    except Exception:
        return None


def breadth_pct(uni):
    if uni is None or uni.empty or "r3" not in uni.columns:
        return None
    return float((uni["r3"] > 0).mean() * 100)


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ② 베이스 (주봉 기준)
# ════════════════════════════════════════════════════════════════════════════
def to_weekly(df):
    return df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min",
                                     "Close": "last", "Volume": "sum"}).dropna()


def zigzag(w, pctv=8.0):
    hi_a, lo_a = w["High"].values, w["Low"].values
    piv, d = [], 0
    hi, hp, lo, lp = hi_a[0], 0, lo_a[0], 0
    for i in range(1, len(w)):
        if d >= 0 and hi_a[i] > hi:
            hi, hp = hi_a[i], i
        if d <= 0 and lo_a[i] < lo:
            lo, lp = lo_a[i], i
        if d >= 0 and lo_a[i] <= hi * (1 - pctv / 100):
            piv.append((hp, "H", hi)); d = -1; lo, lp = lo_a[i], i
        elif d <= 0 and hi_a[i] >= lo * (1 + pctv / 100):
            piv.append((lp, "L", lo)); d = 1; hi, hp = hi_a[i], i
    return piv


def _daily_date(dfd, week_end, kind, back=1):
    seg = dfd.loc[week_end - pd.Timedelta(days=7 * back):week_end]
    if seg.empty:
        return week_end
    return seg["High"].idxmax() if kind == "H" else seg["Low"].idxmin()


def build_bases(dfd, zp=8.0):
    w = to_weekly(dfd)
    if len(w) < 20:
        return [], w
    bases, used = [], -1
    for hp, typ, hv in zigzag(w, zp):
        if typ != "H" or hp <= used:
            continue
        after = w.iloc[hp + 1:]
        if len(after) < 3:
            break
        bo = np.where(after["Close"].values > hv)[0]
        completed = len(bo) > 0
        endpos = hp + 1 + int(bo[0]) if completed else len(w) - 1
        seg = w.iloc[hp:endpos + 1]
        lowv = float(seg["Low"].min())
        lowpos = hp + int(np.argmin(seg["Low"].values))
        depth = (hv - lowv) / hv * 100
        weeks = endpos - hp
        if depth < 7 or depth > 72 or weeks < 3:
            continue
        start_d = _daily_date(dfd, w.index[hp], "H")
        low_d = _daily_date(dfd, w.index[lowpos], "L")
        end_d = dfd.index[-1]
        if completed:
            cx = dfd.loc[low_d:]
            cxi = cx.index[cx["Close"] > hv]
            end_d = cxi[0] if len(cxi) else _daily_date(dfd, w.index[endpos], "H")
        pre = dfd.loc[:start_d].tail(160)
        prior = (hv / float(pre["Low"].min()) - 1) * 100 if len(pre) > 30 else np.nan
        rng = hv - lowv
        u_ratio = int((seg["Low"] <= lowv + rng * 0.33).sum()) / max(1, len(seg)) * 100
        li = max(1, lowpos - hp)
        lseg, rseg = seg.iloc[:li], seg.iloc[li:]
        lv = float(lseg["Volume"].mean()) if len(lseg) else np.nan
        vol_bal = float(rseg["Volume"].mean()) / lv if lv and lv > 0 and len(rseg) else np.nan
        bases.append({"start": start_d, "low_date": low_d, "end": end_d,
                      "left_high": float(hv), "low": lowv, "depth": depth,
                      "weeks": float(weeks), "completed": completed, "prior_gain": prior,
                      "u_ratio": u_ratio, "vol_bal": vol_bal})
        used = endpos
    return bases, w


def count_bases(bases):
    cnt, prev = 0, None
    for b in bases:
        cnt = 1 if (prev is not None and b["low"] < prev) else cnt + 1
        b["count"] = cnt
        prev = b["low"]
    return bases


def detect_handle(dfd, base):
    seg = dfd.loc[base["low_date"]:]
    if len(seg) < 8:
        return None
    lh, low = base["left_high"], base["low"]
    if float(seg["High"].max()) < low + (lh - low) * 0.60:
        return None
    p = int(np.argmax(seg["High"].values))
    hseg = seg.iloc[p:]
    if len(hseg) < 4:
        return None
    h_high = float(hseg["High"].iloc[0])
    h_low = float(hseg["Low"].min())
    depth = (h_high - h_low) / h_high * 100
    vma = dfd["Volume"].rolling(50).mean()
    bv = float(vma.loc[hseg.index[0]]) if not np.isnan(vma.loc[hseg.index[0]]) else np.nan
    dry = float(hseg["Volume"].mean()) / bv if bv and bv > 0 else np.nan
    ma50 = dfd["Close"].rolling(50).mean()
    lowd = hseg["Low"].idxmin()
    above50 = (h_low >= float(ma50.loc[lowd]) * 0.98) if len(dfd) > 50 and not np.isnan(ma50.loc[lowd]) else False
    half = len(hseg) // 2
    wedge = (float(hseg["Low"].iloc[half:].mean()) > float(hseg["Low"].iloc[:half].mean())
             and depth < 4)
    return {"start": seg.index[p], "high": h_high, "low": h_low, "low_date": lowd,
            "depth": depth, "days": len(hseg), "dry": dry,
            "ok_depth": 3 <= depth <= 20, "ok_days": 5 <= len(hseg) <= 60,
            "ok_pos": h_low >= (lh + low) / 2, "ok_dry": (not np.isnan(dry)) and dry < 1.0,
            "ok_ma50": above50, "wedge": wedge}


def classify(dfd, base, handle):
    depth, weeks = base["depth"], base["weeks"]
    lh, low = base["left_high"], base["low"]
    rng = lh - low
    pre = dfd.loc[:base["start"]].tail(60)
    run = (lh / float(pre["Low"].min()) - 1) * 100 if len(pre) > 15 else 0
    if run >= 60 and depth <= 25 and 2.5 <= weeks <= 8:
        return "하이 타이트 플래그", "4~8주 급등 후 3~5주 얕은 조정. 가장 강하지만 가장 드묾"
    seg = dfd.loc[base["start"]:base["end"]]
    if rng > 0 and len(seg) > 20:
        lv = seg["Low"]
        isl = lv == lv.rolling(9, center=True, min_periods=9).min()
        cand = [i for i in np.where(isl.fillna(False).values)[0] if lv.iloc[i] <= low + rng * 0.40]
        merged = []
        for i in cand:
            if merged and i - merged[-1] < 6:
                if lv.iloc[i] < lv.iloc[merged[-1]]:
                    merged[-1] = i
            else:
                merged.append(i)
        if len(merged) >= 2 and merged[-1] - merged[0] >= 8:
            peak = float(seg["High"].iloc[merged[0]:merged[-1] + 1].max())
            tail = float(seg["High"].iloc[merged[-1]:].max())
            if peak >= low + rng * 0.45 and tail >= peak * 0.90 and weeks >= 6:
                return "이중 바닥 (W)", "두 번째 저점이 첫 저점을 살짝 이탈하는 형태가 정석"
    if depth <= 15 and weeks >= 4:
        return "플랫 베이스", "5주 이상 · 깊이 15% 이내. 2차 베이스로 자주 출현"
    if weeks >= 6 and handle is not None:
        return "컵 위드 핸들", "오닐 대표 패턴. 핸들 고점이 피봇"
    if weeks >= 6:
        return "컵 (핸들 미형성)", "핸들 없이 좌측 고점을 바로 치면 실패율 상승"
    if weeks >= 3:
        return "짧은 조정", "정식 베이스 기준(5주) 미달 — 신뢰도 낮음"
    return "베이스 미형성", ""


def base_flaws(base, handle, btype):
    f = []
    if base["depth"] > 35:
        f.append(("깊이 과다", f'{base["depth"]:.0f}%', "33% 이하 (약세장 50%)"))
    if base["weeks"] < 5 and btype != "하이 타이트 플래그":
        f.append(("기간 부족", f'{base["weeks"]:.0f}주', "5주 이상 (컵 7주)"))
    if base["u_ratio"] < 15 and base["weeks"] >= 6:
        f.append(("V자형", f'저점권 체류 {base["u_ratio"]:.0f}%', "15% 이상 (U자형)"))
    if not np.isnan(base["vol_bal"]) and base["vol_bal"] < 0.8:
        f.append(("우측 거래량 부족", f'{base["vol_bal"]:.2f}배', "0.8배 이상"))
    if not np.isnan(base["prior_gain"]) and base["prior_gain"] < 30:
        f.append(("선행 상승 부족", pct(base["prior_gain"]), "+30% 이상"))
    if base.get("count", 1) >= 3:
        f.append(("후기 베이스", f'{base["count"]}차', "1~2차"))
    if handle:
        if handle["depth"] > 20:
            f.append(("핸들 과대", f'{handle["depth"]:.0f}%', "8~12%"))
        if not handle["ok_pos"]:
            f.append(("핸들 위치 불량", "베이스 하단", "상단 절반"))
        if handle["wedge"]:
            f.append(("쐐기형 핸들", "하락 없이 좁아짐", "완만한 하락 드리프트"))
        if not handle["ok_dry"]:
            f.append(("핸들 거래량", num(handle["dry"], 2) + "배", "1.0배 미만"))
    return f


def analyze_base(dfd, market, zp=8.0):
    bases, w = build_bases(dfd, zp)
    if not bases:
        return None
    bases = count_bases(bases)
    cur = bases[-1]
    handle = detect_handle(dfd, cur) if not cur["completed"] else None
    btype, note = classify(dfd, cur, handle)
    flaws = base_flaws(cur, handle, btype)
    if handle and handle["ok_depth"] and handle["ok_pos"] and not handle["wedge"]:
        pv_raw, pv_src = handle["high"], "핸들 고점"
    else:
        pv_raw, pv_src = cur["left_high"], "베이스 좌측 고점"
    pivot = round_tick(pv_raw * 1.001 if market == "KR" else pv_raw + 0.10, market, up=True)
    price = float(dfd["Close"].iloc[-1])
    gap = (price / pivot - 1) * 100
    since_end = (dfd.index[-1] - cur["end"]).days
    if cur["completed"] and since_end > 5:
        stage, kind = "직전 베이스 돌파 완료 — 신규 매수 구간 아님", "fail"
    elif gap < -10:
        stage, kind = "베이스 형성 중 — 관망", "idle"
    elif gap < -1:
        stage, kind = "피봇 접근 — 돌파 대기", "warn"
    elif gap <= 5:
        stage, kind = "매수 가능 구간", "pass"
    else:
        stage, kind = "연장(Extended) — 추격 금지", "fail"
    vma = dfd["Volume"].rolling(50).mean()
    bo_day, bo_vol = None, None
    tail = dfd.tail(20)
    for i in range(1, len(tail)):
        if tail["Close"].iloc[i] > pivot >= tail["Close"].iloc[i - 1]:
            bo_day = tail.index[i]
            v = float(vma.loc[bo_day]) if not np.isnan(vma.loc[bo_day]) else np.nan
            bo_vol = float(tail["Volume"].iloc[i]) / v if v and v > 0 else np.nan
    # 과거 돌파 성공률
    wins, tries = 0, 0
    for b in bases[:-1]:
        if not b["completed"]:
            continue
        after = dfd.loc[b["end"]:].head(120)
        if len(after) < 10:
            continue
        tries += 1
        if float(after["Close"].max()) / b["left_high"] - 1 >= 0.20:
            wins += 1
    return {"bases": bases, "cur": cur, "handle": handle, "type": btype, "note": note,
            "flaws": flaws, "pivot": pivot, "pivot_src": pv_src, "gap": gap, "stage": stage,
            "kind": kind, "bo_day": bo_day, "bo_vol": bo_vol, "weekly": w,
            "win": (wins, tries)}


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ③ 지표
# ════════════════════════════════════════════════════════════════════════════
def rets(df):
    o = {}
    for k, n in [("r1", 21), ("r3", 63), ("r6", 126), ("r9", 189), ("r12", 252)]:
        o[k] = ((float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-n - 1]) - 1) * 100
                if len(df) > n else np.nan)
    return o


def rs_rating(df, uni):
    r = rets(df)
    if any(np.isnan(r[k]) for k in ("r3", "r6", "r9", "r12")):
        return None, r
    sc = 0.4 * r["r3"] + 0.2 * (r["r6"] + r["r9"] + r["r12"])
    if uni is None or uni.empty:
        return None, r
    u = 0.4 * uni["r3"] + 0.2 * (uni["r6"] + uni["r9"] + uni["r12"])
    return min(99, int(round((u < sc).mean() * 98)) + 1), r


def rs_line(df, idx):
    j = df[["Close"]].join(idx[["Close"]], rsuffix="_i", how="inner").dropna()
    if len(j) < 120:
        return None, None
    line = j["Close"] / j["Close_i"]
    return line, bool(line.iloc[-1] >= line.tail(252).max() * 0.995)


def ma_stack(df):
    c = df["Close"]
    m = {n: (float(c.rolling(n).mean().iloc[-1]) if len(df) >= n else np.nan)
         for n in (10, 21, 50, 150, 200)}
    px = float(c.iloc[-1])
    ok = (not np.isnan(m[200])) and px > m[50] > m[150] > m[200]
    up200 = len(df) > 225 and m[200] > float(c.rolling(200).mean().iloc[-22])
    return m, ok, up200


def accumulation(df, days=50):
    d = df.tail(days + 1)
    vma = float(df["Volume"].rolling(50).mean().iloc[-1])
    up = d[(d["Close"] > d["Close"].shift(1)) & (d["Volume"] > vma)]
    dn = d[(d["Close"] < d["Close"].shift(1)) & (d["Volume"] > vma)]
    ratio = len(up) / max(1, len(dn))
    g = "A" if ratio >= 2 else "B" if ratio >= 1.3 else "C" if ratio >= 0.8 else "D" if ratio >= 0.5 else "E"
    return len(up), len(dn), ratio, g


def atr_pct(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"].shift(1)
    tr = pd.concat([h - l, (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
    a = tr.rolling(n).mean().iloc[-1]
    return float(a / df["Close"].iloc[-1] * 100)


def beta_mdd(df, idx):
    beta = np.nan
    try:
        j = df[["Close"]].join(idx[["Close"]], rsuffix="_i", how="inner").dropna().tail(252)
        r1, r2 = j["Close"].pct_change().dropna(), j["Close_i"].pct_change().dropna()
        if len(r1) > 100 and r2.var() > 0:
            beta = float(np.cov(r1, r2)[0][1] / r2.var())
    except Exception:
        pass
    c = df["Close"]
    mdd = float(((c / c.cummax()) - 1).min() * 100)
    win = c.tail(504)
    mdd2 = float(((win / win.cummax()) - 1).min() * 100)
    return beta, mdd, mdd2


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ④ 오닐 고점 / 저점 / 매도 신호
# ════════════════════════════════════════════════════════════════════════════
def topping_signals(df, base, ma):
    """오닐 고점 신호 — 강세 속에서 파는 신호 (근거 수치 포함)"""
    out = []
    c, v = df["Close"], df["Volume"]
    px = float(c.iloc[-1])
    vma = float(v.rolling(50).mean().iloc[-1])

    r15 = float(c.iloc[-1] / c.iloc[-16] - 1) * 100 if len(c) > 16 else np.nan
    out.append(("클라이맥스 급등", r15 >= 25, f"3주 수익률 {pct(r15)}", "25% 이상이면 과열",
                "2~3주 만에 25~50% 급등하면 상승의 마지막 국면일 확률이 높습니다"))

    if not np.isnan(ma[200]) and ma[200] > 0:
        ext = (px / ma[200] - 1) * 100
        out.append(("200일선 이격", ext >= 70, f"{pct(ext)}", "70% 이상이면 과열",
                    "200일선에서 70~100% 벌어지면 되돌림 위험이 커집니다"))

    if len(df) > 60:
        seg = df.tail(60)
        day_gain = seg["Close"].pct_change() * 100
        biggest = float(day_gain.max())
        recent = float(day_gain.iloc[-1])
        is_max = recent >= biggest * 0.999 and recent > 0
        out.append(("최대 상승일 출현", is_max, f"당일 {pct(recent)} / 60일 최대 {pct(biggest)}",
                    "돌파 이후 최대 상승일", "상승 후반의 최대 상승일은 흔히 천장 신호입니다"))
        vmax = float(seg["Volume"].max())
        vd = seg["Volume"].idxmax()
        vol_top = (df.index[-1] - vd).days <= 5 and float(seg.loc[vd, "Close"]) < float(seg.loc[vd, "Open"])
        out.append(("최대 거래량 음봉", vol_top,
                    f'{vd:%Y-%m-%d} 거래량 {vmax/max(vma,1):.1f}배', "최근 5일 내 발생 시 경고",
                    "최대 거래량이 터졌는데 종가가 밀리면 기관이 넘기고 있다는 뜻입니다"))

    if len(df) > 5:
        gap = float(df["Open"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
        hi52 = float(df["High"].tail(252).max())
        exh = gap >= 3 and px >= hi52 * 0.95
        out.append(("소진 갭(Exhaustion Gap)", exh, f"당일 갭 {pct(gap)}", "고점권 +3% 이상 갭",
                    "긴 상승 뒤 위로 뜬 갭은 마지막 매수세가 몰린 자리일 수 있습니다"))

    w = to_weekly(df).tail(3)
    if len(w) >= 2:
        rng_ok = all((w["High"] - w["Low"]) / w["Low"] * 100 > 8) and \
            abs(float(w["Close"].iloc[-1] / w["Close"].iloc[0] - 1)) * 100 < 3
        out.append(("레일로드 트랙", bool(rng_ok), "2주 큰 변동·진전 없음", "변동폭 8%+ & 순변화 3% 미만",
                    "크게 오르내렸는데 제자리면 매수와 매도가 팽팽히 맞선 상태입니다"))
    return out


def bottoming_signals(df, base, ma):
    """오닐 저점/바닥 신호 — 반등 시작의 근거"""
    out = []
    c, v = df["Close"], df["Volume"]
    px = float(c.iloc[-1])
    vma = float(v.rolling(50).mean().iloc[-1])

    if base:
        low = base["cur"]["low"]
        seg = df.loc[base["cur"]["low_date"]:]
        under = float(seg["Low"].min()) <= low * 1.001
        rallied = px > low * 1.05
        out.append(("언더컷 & 랠리", bool(under and rallied),
                    f'저점 {fmt(low)} 이탈 후 현재 {pct((px/low-1)*100)}',
                    "저점 이탈 뒤 5% 이상 반등",
                    "저점을 살짝 깨고 올라오면 약한 손이 털린 것으로 오히려 좋은 신호입니다"))
    w = to_weekly(df).tail(3)
    if len(w) >= 3:
        closes = w["Close"].values
        tight = all(abs(closes[i] / closes[i - 1] - 1) * 100 <= 1.5 for i in range(1, len(closes)))
        out.append(("3주 타이트", bool(tight),
                    f'주간 종가 변동 {max(abs(closes[i]/closes[i-1]-1)*100 for i in range(1,len(closes))):.1f}%',
                    "주간 변동 1.5% 이내", "주가가 좁게 붙으면 매도 물량이 말랐다는 뜻입니다"))
    if len(df) > 60:
        r10 = df.tail(10)
        dry = float(r10["Volume"].mean()) / vma
        out.append(("거래량 건조", dry < 0.75, f"{dry:.2f}배", "50일 평균의 0.75배 미만",
                    "팔 사람이 없어 거래가 마르는 것은 바닥권의 전형적 모습입니다"))
        big_up = r10[(r10["Close"] > r10["Open"]) & (r10["Volume"] > vma * 1.5)]
        out.append(("대량 매수 출현", len(big_up) > 0, f"최근 10일 중 {len(big_up)}일",
                    "거래량 1.5배 이상 상승일", "거래가 마른 뒤 대량 상승일이 나오면 기관 진입 신호입니다"))
    if not np.isnan(ma[50]):
        supp = px >= ma[50] * 0.98 and px <= ma[50] * 1.05
        out.append(("50일선 지지", bool(supp), f'현재가/50일선 {px/ma[50]*100:.1f}%',
                    "50일선 -2%~+5% 구간", "상승 종목이 50일선에서 받쳐지면 추가 매수 자리입니다"))
    return out


def sell_pressure(df, ma, topping, base):
    """매도 압력 종합 — 0~100 (높을수록 매도 우위)"""
    score, reasons = 0, []
    px = float(df["Close"].iloc[-1])
    vma = float(df["Volume"].rolling(50).mean().iloc[-1])

    n_top = sum(1 for t in topping if t[1])
    score += min(48, n_top * 16)
    if n_top:
        reasons.append(f"고점 신호 {n_top}건 발생")

    if not np.isnan(ma[50]) and px < ma[50]:
        heavy = df.tail(10)
        hv = heavy[(heavy["Close"] < heavy["Close"].shift(1)) & (heavy["Volume"] > vma * 1.3)]
        if len(hv):
            score += 25
            reasons.append("대량 거래를 동반한 50일선 이탈")
        else:
            score += 12
            reasons.append("50일선 아래")
    if not np.isnan(ma[200]) and px < ma[200]:
        score += 20
        reasons.append("200일선 이탈 — 장기 추세 훼손")

    up_n, dn_n, ratio, g = accumulation(df)
    if ratio < 0.8:
        score += 12
        reasons.append(f"분산 우위 (매집 {up_n} vs 분산 {dn_n})")

    if base and base["cur"]:
        if px < base["cur"]["low"]:
            score += 15
            reasons.append("베이스 저점 이탈")
        elif base["handle"] and px < base["handle"]["low"]:
            score += 10
            reasons.append("핸들 저점 이탈")

    score = int(min(100, score))
    if score >= 65: act, kind = "전량 매도 검토", "fail"
    elif score >= 45: act, kind = "절반 익절 / 비중 축소", "warn"
    elif score >= 25: act, kind = "보유 · 경계", "warn"
    else: act, kind = "보유 유지", "pass"
    return {"score": score, "action": act, "kind": kind, "reasons": reasons}


def eight_week_rule(df, base):
    """돌파 후 3주 내 20% 이상 상승 시 8주 보유 규칙"""
    if not base or base["bo_day"] is None:
        return None
    bo = base["bo_day"]
    seg = df.loc[bo:]
    if len(seg) < 3:
        return None
    w3 = seg.head(16)
    gain = float(w3["Close"].max() / float(df.loc[bo, "Close"]) - 1) * 100
    days = (df.index[-1] - bo).days
    if gain >= 20 and days <= 21:
        return {"on": True, "gain": gain, "until": bo + pd.Timedelta(days=56),
                "msg": "돌파 후 3주 내 20% 이상 상승 — 8주 보유 규칙 적용 대상"}
    return {"on": False, "gain": gain, "days": days,
            "msg": "8주 보유 규칙 미해당 (일반 익절 규칙 적용)"}


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑤ 등급 · 시나리오
# ════════════════════════════════════════════════════════════════════════════
def growth_pct(cur, prev):
    if cur is None or prev is None or prev == 0:
        return None
    if prev < 0:
        return 999.0 if cur > 0 else None
    return (cur / prev - 1) * 100


def eps_rating(q, y):
    if q is None and y is None:
        return None
    def curve(g):
        if g is None:
            return 50
        g = min(g, 300)
        if g <= 0:
            return max(5, 30 + g / 4)
        return min(99, 50 + 49 * (1 - math.exp(-g / 60)))
    return int(round(0.6 * curve(q) + 0.4 * curve(y)))


def smr_grade(sales, opm, roe):
    if all(v is None for v in (sales, opm, roe)):
        return None
    pts = 0
    for v, good, ok in [(sales, 25, 12), (opm, 18, 10), (roe, 17, 10)]:
        if v is None:
            continue
        pts += 2 if v >= good else (1 if v >= ok else 0)
    return "ABCDE"[max(0, min(4, 4 - pts))]


G2N = {"A": 90, "B": 75, "C": 55, "D": 35, "E": 20}


def composite(eps_r, rs_r, smr, ad, base_ok, m_ok):
    p, w = [], []
    if eps_r: p.append(eps_r); w.append(0.30)
    if rs_r: p.append(rs_r); w.append(0.30)
    if smr: p.append(G2N[smr]); w.append(0.15)
    if ad: p.append(G2N[ad]); w.append(0.10)
    p.append(85 if base_ok else 40); w.append(0.10)
    p.append(85 if m_ok else 40); w.append(0.05)
    return int(round(sum(a * b for a, b in zip(p, w)) / sum(w)))


def scenario(binfo, price, market, ma, capital, risk_pct, atrp=None):
    if binfo is None:
        return None
    pv, kind, handle = binfo["pivot"], binfo["kind"], binfo["handle"]
    if kind == "pass":
        entry, mode = round_tick(price, market, up=True), "즉시 진입 가능 (피봇 위 5% 이내)"
    elif kind == "warn":
        entry, mode = pv, "조건부 — 피봇 돌파 확인 후 진입"
    elif kind == "idle":
        entry, mode = pv, "대기 — 베이스 완성 후 피봇 돌파 시"
    else:
        entry, mode = None, "신규 진입 구간 아님"
    if entry is None:
        alt = round_tick(ma[50], market, up=False) if not np.isnan(ma[50]) else None
        return {"mode": mode, "entry": None, "alt": alt, "kind": kind}
    hard = entry * 0.92
    struct = handle["low"] if handle else binfo["cur"]["low"]
    stop = round_tick(max(hard, struct * 0.99) if struct and struct > hard else hard,
                      market, up=False)
    stop_pct = (stop / entry - 1) * 100
    t1, t2 = round_tick(entry * 1.20, market, False), round_tick(entry * 1.25, market, False)
    rr = abs(20 / stop_pct) if stop_pct else np.nan
    qty = risk_amt = pos_amt = None
    if capital and capital > 0:
        risk_amt = capital * risk_pct / 100
        per = entry - stop
        if per > 0:
            qty = max(0, min(int(risk_amt // per), int(capital * 0.25 // entry)))
            pos_amt = qty * entry
    atr_note = None
    if atrp:
        need = atrp * 2.5
        atr_note = ("적정" if abs(stop_pct) >= need else "타이트",
                    f"일간 변동성(ATR) {atrp:.1f}% × 2.5 = {need:.1f}% vs 손절폭 {abs(stop_pct):.1f}%")
    return {"mode": mode, "entry": entry, "stop": stop, "stop_pct": stop_pct, "t1": t1,
            "t2": t2, "rr": rr, "qty": qty, "risk_amt": risk_amt, "pos_amt": pos_amt,
            "kind": kind, "buy_hi": round_tick(pv * 1.05, market, False), "atr": atr_note}


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑥ 환율
# ════════════════════════════════════════════════════════════════════════════
def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return float((100 - 100 / (1 + rs)).iloc[-1])


def fx_analysis(fx):
    c = fx["Close"].dropna()
    cur = float(c.iloc[-1])
    avgs, dev = {}, {}
    for lab, n in [("1개월", 21), ("6개월", 126), ("1년", 252), ("2년", 504), ("3년", 756)]:
        if len(c) > n:
            a = float(c.tail(n).mean())
            avgs[lab] = a
            dev[lab] = (cur / a - 1) * 100
    w3 = c.tail(756)
    pctile = float((w3 < cur).mean() * 100) if len(w3) > 100 else np.nan
    w1 = c.tail(252)
    hi52, lo52 = float(w1.max()), float(w1.min())
    band = (cur - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else np.nan
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    ma120 = float(c.rolling(120).mean().iloc[-1])
    trend = "상승(원화 약세)" if ma20 > ma60 > ma120 else \
            "하락(원화 강세)" if ma20 < ma60 < ma120 else "혼조"
    r = rsi(c)
    vol = float(c.pct_change().tail(252).std() * math.sqrt(252) * 100)

    plans = []
    # 1개월 — 단기 모멘텀
    if cur > ma20 and r > 65:
        v1 = ("환전 보류", "fail", f"20일선 위 + RSI {r:.0f} 과열 — 단기 고점 위험")
    elif cur < ma20 and r < 40:
        v1 = ("소액 분할 환전", "pass", f"20일선 아래 + RSI {r:.0f} — 단기 저가권")
    else:
        v1 = ("중립 · 소액 분할", "warn", f"20일선 대비 {pct((cur/ma20-1)*100)} · RSI {r:.0f}")
    plans.append(("1개월", "단기 모멘텀", v1))
    # 3개월 — 6개월 평균 회귀
    d6 = dev.get("6개월", np.nan)
    if not np.isnan(d6):
        if d6 <= -2: v2 = ("적극 환전", "pass", f"6개월 평균 대비 {pct(d6)} — 평균 이하")
        elif d6 <= 2: v2 = ("분할 환전", "warn", f"6개월 평균 대비 {pct(d6)} — 평균권")
        else: v2 = ("환전 축소", "fail", f"6개월 평균 대비 {pct(d6)} — 평균 이상")
        plans.append(("3개월", "평균 회귀", v2))
    # 6개월 — 1년 평균 + 백분위
    d12 = dev.get("1년", np.nan)
    if not np.isnan(d12):
        if d12 <= -3: v3 = ("적극 환전", "pass", f"1년 평균 대비 {pct(d12)}")
        elif d12 <= 3: v3 = ("분할 환전", "warn", f"1년 평균 대비 {pct(d12)}")
        else: v3 = ("환전 축소", "fail", f"1년 평균 대비 {pct(d12)}")
        plans.append(("6개월", "중기 밴드", v3))
    # 1년 — 3년 백분위
    if not np.isnan(pctile):
        if pctile <= 30: v4 = ("적극 환전", "pass", f"3년 백분위 {pctile:.0f}% — 하위권")
        elif pctile <= 70: v4 = ("분할 환전", "warn", f"3년 백분위 {pctile:.0f}% — 중간권")
        else: v4 = ("최소 환전", "fail", f"3년 백분위 {pctile:.0f}% — 상위권(비쌈)")
        plans.append(("1년", "장기 위치", v4))

    if np.isnan(pctile): now_ratio, guide = 30, "데이터 부족 — 균등 분할"
    elif pctile <= 20: now_ratio, guide = 70, "3년래 최저권 — 필요분 대부분 지금 환전"
    elif pctile <= 40: now_ratio, guide = 50, "평균 이하 — 절반 환전 후 추가 하락 시 보충"
    elif pctile <= 60: now_ratio, guide = 30, "평균권 — 3분의 1만 환전하고 분할 대기"
    elif pctile <= 80: now_ratio, guide = 15, "평균 이상 — 최소한만 환전"
    else: now_ratio, guide = 5, "3년래 최고권 — 급하지 않으면 대기"

    trig = []
    for lab in ("1년", "2년", "3년"):
        if lab in avgs and avgs[lab] < cur:
            trig.append((f"{lab} 평균 도달", avgs[lab], f"{pct((avgs[lab]/cur-1)*100)} 하락 시"))
    return {"cur": cur, "avgs": avgs, "dev": dev, "pctile": pctile, "band": band,
            "hi52": hi52, "lo52": lo52, "ma20": ma20, "ma60": ma60, "ma120": ma120,
            "trend": trend, "rsi": r, "vol": vol, "plans": plans,
            "now_ratio": now_ratio, "guide": guide, "triggers": trig, "series": c}


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑦ 뉴스 해석
# ════════════════════════════════════════════════════════════════════════════
def classify_news(items):
    for it in items:
        t = it["title"].lower()
        topics = []
        for name, kws, canslim in NEWS_TOPICS:
            if any(k.lower() in t for k in kws):
                topics.append((name, canslim))
        it["topics"] = topics or [("일반", "—")]
        pos = sum(1 for w in POS_WORDS if w.lower() in t)
        neg = sum(1 for w in NEG_WORDS if w.lower() in t)
        it["tone"] = "긍정" if pos > neg else ("부정" if neg > pos else "중립")
    return items


def news_insight(items, binfo, q_g, rating):
    if not items:
        return ["신뢰 기관 뉴스가 수집되지 않았습니다. 종목 IR 페이지나 공시를 직접 확인하세요."]
    cnt = {}
    for it in items:
        for nm, cs in it["topics"]:
            cnt[nm] = cnt.get(nm, 0) + 1
    tones = [it["tone"] for it in items]
    pos, neg = tones.count("긍정"), tones.count("부정")
    out = []
    top = sorted(cnt.items(), key=lambda x: -x[1])[:3]
    out.append("최근 뉴스 " + str(len(items)) + "건 중 가장 많은 주제는 "
               + ", ".join(f"{k}({v}건)" for k, v in top) + "입니다.")
    if pos > neg * 1.5:
        out.append(f"논조는 긍정 {pos} : 부정 {neg}으로 우호적입니다. "
                   "다만 뉴스가 좋을 때 주가가 이미 반영된 경우가 많으니, 베이스 위치로 확인하세요.")
    elif neg > pos:
        out.append(f"논조는 부정 {neg} : 긍정 {pos}으로 부담이 있습니다. "
                   "악재가 주가에 반영되는 중인지 베이스 저점 이탈 여부를 함께 보세요.")
    else:
        out.append(f"논조는 긍정 {pos} : 부정 {neg}으로 균형 상태입니다.")
    if cnt.get("실적·가이던스"):
        out.append("실적 관련 뉴스가 있습니다 — CANSLIM의 C·A에 직접 영향을 줍니다. "
                   "수치는 반드시 공시 원문으로 대조하세요.")
    if cnt.get("규제·소송") or cnt.get("공급망·비용"):
        out.append("규제·소송 또는 비용 관련 뉴스가 있습니다. 오닐은 이런 뉴스 자체보다 "
                   "그 뉴스에 주가와 거래량이 어떻게 반응했는지를 봤습니다. "
                   "악재에도 저점이 유지되면 오히려 강한 신호입니다.")
    if cnt.get("애널리스트"):
        out.append("목표주가·투자의견 변경 뉴스가 있습니다. 오닐은 애널리스트 의견을 매매 근거로 삼지 "
                   "말라고 했습니다. 실제 거래량과 기관 매집 흔적으로 판단하세요.")
    if cnt.get("신제품·기술") or cnt.get("수주·계약"):
        out.append("신제품·수주 뉴스는 CANSLIM의 N(새로운 것)에 해당합니다. "
                   "오닐이 말한 대박 종목의 공통점은 '새로운 무언가'였습니다.")
    if binfo:
        if binfo["kind"] == "fail" and binfo["gap"] > 5:
            out.append("현재 주가는 피봇에서 연장된 구간입니다. 좋은 뉴스가 나와도 "
                       "지금 진입은 손절 위험이 큽니다.")
        elif binfo["kind"] in ("warn", "idle"):
            out.append(f'베이스 형성 중이며 피봇은 {fmt(binfo["pivot"])}입니다. '
                       "뉴스보다 거래량을 동반한 피봇 돌파가 실제 진입 신호입니다.")
    if rating and rating < 80:
        out.append(f"뉴스 흐름과 별개로 RS가 {rating}으로 기준(80) 미달입니다. "
                   "시장이 이 종목을 아직 주도주로 인정하지 않고 있다는 뜻입니다.")
    return out


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑧ 정밀 보강 진단
# ════════════════════════════════════════════════════════════════════════════
def extra_diagnostics(df, market, binfo, fnd, idx, capital, ma):
    d = {}
    px = float(df["Close"].iloc[-1])
    d["atr"] = atr_pct(df)
    beta, mdd_all, mdd2y = beta_mdd(df, idx) if idx is not None else (np.nan, np.nan, np.nan)
    d["beta"], d["mdd_all"], d["mdd2y"] = beta, mdd_all, mdd2y
    val = (df["Close"] * df["Volume"]).tail(20).mean()
    d["turnover"] = float(val)
    d["liq_ok"] = val > (1e9 if market == "KR" else 2e7)
    if capital:
        d["order_ratio"] = (capital * 0.25) / val * 100 if val else np.nan
    else:
        d["order_ratio"] = np.nan
    ne = fnd.get("next_earnings")
    d["earn_days"] = int((pd.Timestamp(ne) - pd.Timestamp(datetime.today())).days) if ne is not None else None
    o, c = df["Open"], df["Close"].shift(1)
    g = ((o / c - 1) * 100).dropna()
    d["gap_p95"] = float(g.abs().quantile(0.95)) if len(g) > 100 else np.nan
    if binfo:
        w, t = binfo["win"]
        d["win_rate"] = (w / t * 100) if t else None
        d["win_txt"] = f"{w}/{t}회" if t else "이력 없음"
    else:
        d["win_rate"], d["win_txt"] = None, "이력 없음"
    if fnd.get("shares") and fnd.get("float"):
        d["float_ratio"] = fnd["float"] / fnd["shares"] * 100
    else:
        d["float_ratio"] = None
    d["dist_ma50"] = (px / ma[50] - 1) * 100 if not np.isnan(ma[50]) else np.nan
    return d


def final_checklist(m_ok, c_ok, a_ok, n_ok, s_ok, l_ok, i_ok, base_ok, binfo, sp, diag):
    rows = [("시장이 확정 상승세인가", m_ok, "STEP 0 시장 국면"),
            ("분기 EPS가 25% 이상 늘었는가", c_ok, "STEP 3 실적"),
            ("연간 이익 또는 ROE가 기준을 넘는가", a_ok, "STEP 3 실적"),
            ("52주 고점 15% 이내이고 이평 정배열인가", n_ok, "STEP 1 추세"),
            ("거래량이 매집 우위인가", s_ok, "STEP 6 수급"),
            ("RS가 80 이상인가", l_ok, "STEP 5 상대강도"),
            ("기관·외국인이 사고 있는가", i_ok, "STEP 6 수급"),
            ("결함 없는 1~2차 베이스인가", base_ok, "STEP 2 베이스"),
            ("지금 가격이 매수 구간(피봇~+5%)인가",
             bool(binfo and binfo["kind"] == "pass"), "STEP 2 피봇"),
            ("매도 압력이 낮은가(45 미만)", bool(sp and sp["score"] < 45), "STEP 9 매도신호"),
            ("유동성이 충분한가", bool(diag.get("liq_ok")), "정밀 보강 · 거래대금"),
            ("실적 발표까지 5일 이상 남았는가",
             (diag.get("earn_days") is None or diag["earn_days"] > 5), "정밀 보강 · 이벤트")]
    return rows


# ════════════════════════════════════════════════════════════════════════════
# 차트 (밝은 배경)
# ════════════════════════════════════════════════════════════════════════════
def _layout(fig, h, legend=True):
    fig.update_layout(template="plotly_white", height=h, margin=dict(l=10, r=70, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=P_BG,
                      showlegend=legend, legend=dict(orientation="h", y=1.09,
                                                     font=dict(size=10, color=P_INK2)),
                      font=dict(family="IBM Plex Mono", size=10, color=P_INK2),
                      xaxis_rangeslider_visible=False, hovermode="x unified")
    fig.update_xaxes(gridcolor=P_LINE, linecolor=P_LINE, zeroline=False)
    fig.update_yaxes(gridcolor=P_LINE, linecolor=P_LINE, zeroline=False)
    return fig


def index_chart(s, nm):
    idx, ftd, dds = s["df"], s["ftd"], s["dds"]
    d = idx.tail(280)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[.76, .24],
                        vertical_spacing=.04)
    fig.add_trace(go.Scatter(x=d.index, y=d["Close"], mode="lines", name=nm,
                             line=dict(color=P_INK, width=1.6)), row=1, col=1)
    for n, c in [(50, P_ACC), (200, P_INFO)]:
        if len(idx) > n:
            fig.add_trace(go.Scatter(x=d.index, y=idx["Close"].rolling(n).mean().loc[d.index],
                                     mode="lines", name=f"{n}일",
                                     line=dict(color=c, width=1.1, dash="dot")), row=1, col=1)
    if dds:
        xs = [r["date"] for r in dds if r["date"] in d.index]
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=[d.loc[x, "Close"] for x in xs], mode="markers",
                                     name="분산일", marker=dict(color=P_DOWN, size=8,
                                                              symbol="triangle-down")), row=1, col=1)
    if ftd.get("date") is not None and ftd["date"] in d.index:
        fig.add_trace(go.Scatter(x=[ftd["date"]], y=[d.loc[ftd["date"], "Close"]],
                                 mode="markers+text", name="FTD", text=["FTD"],
                                 textposition="top center", textfont=dict(color=P_UP, size=11),
                                 marker=dict(color=P_UP, size=13, symbol="star")), row=1, col=1)
    if ftd.get("low_date") is not None and ftd["low_date"] in d.index:
        fig.add_vline(x=ftd["low_date"], line=dict(color=P_INK2, width=1, dash="dash"), row=1, col=1)
    if not d["Volume"].isna().all():
        fig.add_trace(go.Bar(x=d.index, y=d["Volume"], name="거래량",
                             marker=dict(color="#D5D0C6")), row=2, col=1)
    return _layout(fig, 320)


def buywin_chart(series):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines", name="매수 적합도",
                             line=dict(color=P_ACC, width=1.8), fill="tozeroy",
                             fillcolor="rgba(138,90,0,.10)"))
    for y, c, t in [(75, P_UP, "적극"), (55, P_ACC, "선별"), (35, P_DOWN, "보류")]:
        fig.add_hline(y=y, line=dict(color=c, width=1, dash="dot"),
                      annotation_text=t, annotation_position="right",
                      annotation_font=dict(size=9, color=c))
    fig.update_yaxes(range=[0, 100])
    return _layout(fig, 230, legend=False)


def stock_chart(dfd, weekly, binfo, market, rsl, use_weekly):
    src = weekly if use_weekly else dfd
    d = src.tail(160 if use_weekly else 320)
    rows = 3 if rsl is not None else 2
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        row_heights=[.60, .18, .22] if rows == 3 else [.76, .24],
                        vertical_spacing=.035)
    fig.add_trace(go.Candlestick(x=d.index, open=d["Open"], high=d["High"], low=d["Low"],
                                 close=d["Close"], name="주가",
                                 increasing=dict(line=dict(color=P_UP), fillcolor=P_UP),
                                 decreasing=dict(line=dict(color=P_DOWN), fillcolor=P_DOWN)),
                  row=1, col=1)
    mas = [(10, P_ACC), (30, P_INFO), (40, "#7A5C9E")] if use_weekly else \
          [(50, P_ACC), (150, P_INFO), (200, "#7A5C9E")]
    for p, c in mas:
        if len(src) >= p:
            fig.add_trace(go.Scatter(x=d.index, y=src["Close"].rolling(p).mean().loc[d.index],
                                     mode="lines", name=f'{p}{"주" if use_weekly else "일"}',
                                     line=dict(color=c, width=1.1)), row=1, col=1)
    if binfo:
        b, pv = binfo["cur"], binfo["pivot"]
        fig.add_vrect(x0=b["start"], x1=b["end"], fillcolor="rgba(138,90,0,.06)",
                      line_width=0, row=1, col=1)
        fig.add_vline(x=b["low_date"], line=dict(color=P_INK2, width=1, dash="dot"), row=1, col=1)
        fig.add_hline(y=pv, line=dict(color=P_ACC, width=1.5),
                      annotation_text=f"피봇 {fmt(pv, market)}", annotation_position="right",
                      annotation_font=dict(color=P_ACC, size=10), row=1, col=1)
        fig.add_hrect(y0=pv, y1=pv * 1.05, fillcolor="rgba(138,90,0,.13)", line_width=0, row=1, col=1)
        fig.add_hline(y=pv * 0.92, line=dict(color=P_DOWN, width=1, dash="dot"),
                      annotation_text="-8% 손절", annotation_position="right",
                      annotation_font=dict(color=P_DOWN, size=10), row=1, col=1)
        if binfo["handle"]:
            fig.add_vrect(x0=binfo["handle"]["start"], x1=d.index[-1],
                          fillcolor="rgba(11,122,82,.07)", line_width=0, row=1, col=1)
    vma = src["Volume"].rolling(10 if use_weekly else 50).mean().loc[d.index]
    fig.add_trace(go.Bar(x=d.index, y=d["Volume"], name="거래량",
                         marker=dict(color=[P_UP if c >= o else P_DOWN
                                            for c, o in zip(d["Close"], d["Open"])], opacity=.35)),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=vma, mode="lines", name="거래량 평균",
                             line=dict(color=P_ACC, width=1.1)), row=2, col=1)
    if rsl is not None:
        r = rsl.loc[rsl.index.intersection(d.index)]
        fig.add_trace(go.Scatter(x=r.index, y=r.values, mode="lines", name="RS 라인(지수 대비)",
                                 line=dict(color=P_INFO, width=1.3)), row=3, col=1)
    return _layout(fig, 600 if rows == 3 else 480)


def fx_chart(c, a):
    d = c.tail(760)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d.index, y=d.values, mode="lines", name="USD/KRW",
                             line=dict(color=P_INK, width=1.5)))
    for lab, col in [("1년", P_ACC), ("3년", P_INFO)]:
        if lab in a["avgs"]:
            fig.add_hline(y=a["avgs"][lab], line=dict(color=col, width=1, dash="dot"),
                          annotation_text=f'{lab} 평균 {a["avgs"][lab]:,.0f}',
                          annotation_position="right", annotation_font=dict(size=9, color=col))
    fig.add_hline(y=a["cur"], line=dict(color=P_DOWN, width=1.2),
                  annotation_text=f'현재 {a["cur"]:,.0f}', annotation_position="right",
                  annotation_font=dict(size=10, color=P_DOWN))
    return _layout(fig, 300, legend=False)


def cross_section(binfo, price, market):
    b, pv = binfo["cur"], binfo["pivot"]
    lo, hi = b["low"], max(pv * 1.10, price * 1.02)
    span = max(hi - lo, 1e-9)

    def x(v):
        return max(2, min(98, (v - lo) / span * 100))

    parts = [f'<div class="zone" style="left:{x(pv)}%;width:{max(0.8, x(pv*1.05)-x(pv))}%"></div>']
    marks = [("베이스 저점", b["low"]), ("좌측 고점", b["left_high"]), ("피봇", pv)]
    if binfo["handle"]:
        marks.insert(1, ("핸들 저점", binfo["handle"]["low"]))
    for lab, v in marks:
        parts += [f'<div class="lvl" style="left:{x(v)}%"></div>',
                  f'<div class="lbl" style="left:{x(v)}%">{lab}</div>',
                  f'<div class="val" style="left:{x(v)}%">{fmt(v, market)}</div>']
    parts += [f'<div class="now" style="left:{x(price)}%"></div>',
              f'<div class="lbl" style="left:{x(price)}%;top:auto;bottom:27px;color:#16181C;'
              f'font-weight:700">현재가 {fmt(price, market)}</div>']
    return '<div class="xs">' + "".join(parts) + "</div>"


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑨ 변동성 · 신뢰구간 (80%)
# ════════════════════════════════════════════════════════════════════════════
Z80 = 1.2816   # 표준정규 80% 양측 신뢰구간


def volatility_profile(df, conf=0.80):
    """로그수익률 표준편차 기반 기간별 변동 범위 + 이력 분위수 대조"""
    z = Z80 if abs(conf - 0.80) < 1e-6 else float(abs(np.percentile(np.random.RandomState(0).normal(size=200000), (1 - conf) / 2 * 100)))
    lr = np.log(df["Close"]).diff().dropna()
    if len(lr) < 120:
        return None
    win = lr.tail(252)
    sd, mu = float(win.std()), float(win.mean())
    rows = []
    for lab, n in [("1일", 1), ("1주", 5), ("1개월", 21), ("3개월", 63),
                   ("6개월", 126), ("1년", 252)]:
        s, m = sd * math.sqrt(n), mu * n
        lo = (math.exp(m - z * s) - 1) * 100
        hi = (math.exp(m + z * s) - 1) * 100
        elo = ehi = np.nan
        h = (df["Close"].pct_change(n).dropna() * 100)
        if len(h) > max(60, n * 2):
            elo, ehi = float(h.quantile((1 - conf) / 2)), float(h.quantile(1 - (1 - conf) / 2))
        rows.append({"기간": lab, "일수": n, "sigma": s * 100, "lo": lo, "hi": hi,
                     "elo": elo, "ehi": ehi})
    s_ = df["Close"]
    fmin = s_[::-1].rolling(21, min_periods=2).min()[::-1]
    fmax = s_[::-1].rolling(61, min_periods=2).max()[::-1]
    hit_stop = float(((fmin / s_ - 1) <= -0.08).mean() * 100)
    hit_tgt = float(((fmax / s_ - 1) >= 0.20).mean() * 100)
    ann = sd * math.sqrt(252) * 100
    sd60 = float(lr.tail(60).std() * math.sqrt(252) * 100)
    return {"sd_daily": sd * 100, "ann": ann, "ann60": sd60, "mu": mu * 100,
            "rows": rows, "skew": float(win.skew()), "kurt": float(win.kurtosis()),
            "hit_stop": hit_stop, "hit_tgt": hit_tgt, "z": z, "conf": conf,
            "regime": "확대" if sd60 > ann * 1.15 else ("축소" if sd60 < ann * 0.85 else "안정")}


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑩ 재무 이력 (최근 3분기 · 최근 3년)
# ════════════════════════════════════════════════════════════════════════════
def growth_table(tab, lag, last=3, metrics=("매출액", "영업이익", "순이익", "EPS")):
    """tab: DataFrame(index=지표, columns=기간 오름차순) → 최근 N기 성장률"""
    if tab is None or tab.empty:
        return None, None
    cols = list(tab.columns)
    if len(cols) < lag + 1:
        lag_use, kind = 1, "직전 대비"
    else:
        lag_use, kind = lag, "전년 동기 대비"
    rows = []
    for c_i in range(len(cols) - last, len(cols)):
        if c_i < 0:
            continue
        per = cols[c_i]
        rec = {"기간": per}
        for m in metrics:
            if m not in tab.index:
                continue
            cur = safe(tab.loc[m, per])
            rec[m] = cur
            prev = safe(tab.loc[m, cols[c_i - lag_use]]) if c_i - lag_use >= 0 else None
            rec[m + "증감"] = growth_pct(cur, prev)
        rows.append(rec)
    return pd.DataFrame(rows), kind


def _clean(vals):
    out = []
    for v in vals:
        if v is None:
            continue
        try:
            f = float(v)
        except Exception:
            continue
        if np.isnan(f) or np.isinf(f):
            continue
        out.append(f)
    return out


def fin_history(fnd):
    """3분기 · 3년 재무 이력과 오닐 기준 판정"""
    out = {"q": None, "y": None, "q_kind": "", "y_kind": "",
           "q_pass": None, "y_pass": None, "accel": None, "notes": []}
    q_tab, y_tab = fnd.get("q_tab"), fnd.get("y_tab")
    q, qk = growth_table(q_tab, 4, 3)
    y, yk = growth_table(y_tab, 1, 3)
    out["q"], out["q_kind"] = q, qk
    out["y"], out["y_kind"] = y, yk
    if q is not None and "EPS증감" in q.columns:
        g = _clean(q["EPS증감"].tolist())
        if g:
            out["q_pass"] = sum(1 for v in g if v >= 25)
            out["q_n"] = len(g)
            if len(g) >= 2:
                out["accel"] = g[-1] > g[0]
            out["q_list"] = g
    if y is not None and "EPS증감" in y.columns:
        g = _clean(y["EPS증감"].tolist())
        if g:
            out["y_pass"] = sum(1 for v in g if v > 0)
            out["y_n"] = len(g)
            out["y_list"] = g
    return out


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑪ 공포탐욕지수
# ════════════════════════════════════════════════════════════════════════════
def _scale(v, lo, hi):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(max(0, min(100, (v - lo) / (hi - lo) * 100)))


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_cnn_fng():
    try:
        r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                         timeout=8, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"})
        j = r.json()
        fg = j.get("fear_and_greed", {})
        return {"score": float(fg.get("score")), "rating": fg.get("rating"),
                "prev_close": safe(fg.get("previous_close")),
                "week": safe(fg.get("previous_1_week")), "month": safe(fg.get("previous_1_month"))}
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _fng_market_data(market):
    out = {}
    if not HAS_YF:
        return out
    try:
        syms = ["^VIX", "TLT", "HYG", "LQD"] if market == "US" else ["^VIX"]
        px = yf.download(syms, period="1y", progress=False, auto_adjust=True)["Close"]
        if isinstance(px, pd.Series):
            px = px.to_frame(syms[0])
        out["px"] = naive(px.dropna(how="all"))
    except Exception:
        pass
    return out


def fear_greed(market, states, uni, fx=None):
    """CNN 방식을 준용한 자체 산출 (0=극단적 공포 · 100=극단적 탐욕)"""
    comps, aux = [], _fng_market_data(market)
    px = aux.get("px")

    lead = None
    for nm, s in states.items():
        if market == "US" and nm == "S&P 500":
            lead = s["df"]
        elif market == "KR" and nm == "코스피":
            lead = s["df"]
    if lead is None and states:
        lead = list(states.values())[0]["df"]

    if lead is not None and len(lead) > 130:
        c = lead["Close"]
        mom = float(c.iloc[-1] / c.rolling(125).mean().iloc[-1] - 1) * 100
        comps.append(("주가 모멘텀", _scale(mom, -6, 6),
                      f'지수가 125일 평균 대비 {pct(mom)}', "평균 위 = 탐욕"))

    if px is not None and "^VIX" in px.columns:
        v = px["^VIX"].dropna()
        if len(v) > 60:
            vp = float((v < v.iloc[-1]).mean() * 100)
            comps.append(("변동성 (VIX)", 100 - vp,
                          f'VIX {v.iloc[-1]:.1f} · 1년 백분위 {vp:.0f}%', "낮은 변동성 = 탐욕"))
    elif lead is not None and len(lead) > 260:
        rv = np.log(lead["Close"]).diff().rolling(20).std() * math.sqrt(252) * 100
        cur, hist = float(rv.iloc[-1]), rv.tail(252).dropna()
        vp = float((hist < cur).mean() * 100)
        comps.append(("변동성 (실현)", 100 - vp,
                      f'20일 실현변동성 {cur:.1f}% · 1년 백분위 {vp:.0f}%', "낮은 변동성 = 탐욕"))

    br = breadth_pct(uni)
    if br is not None:
        comps.append(("시장 폭", _scale(br, 25, 75),
                      f'3개월 상승 종목 비율 {br:.0f}%', "많이 오를수록 탐욕"))
    if uni is not None and not uni.empty and "r12" in uni.columns:
        st12 = float((uni["r12"] > 0).mean() * 100)
        comps.append(("주가 강도", _scale(st12, 30, 80),
                      f'1년 상승 종목 비율 {st12:.0f}%', "신고가권 종목이 많을수록 탐욕"))

    if px is not None and lead is not None and "TLT" in px.columns:
        try:
            eq = float(lead["Close"].iloc[-1] / lead["Close"].iloc[-21] - 1) * 100
            bd = float(px["TLT"].iloc[-1] / px["TLT"].iloc[-21] - 1) * 100
            comps.append(("안전자산 선호", _scale(eq - bd, -6, 6),
                          f'주식 {pct(eq)} vs 장기국채 {pct(bd)} (20일)', "주식 우위 = 탐욕"))
        except Exception:
            pass
    elif fx is not None and lead is not None:
        try:
            eq = float(lead["Close"].iloc[-1] / lead["Close"].iloc[-21] - 1) * 100
            fxr = float(fx["Close"].iloc[-1] / fx["Close"].iloc[-21] - 1) * 100
            comps.append(("안전자산 선호", _scale(eq - fxr, -6, 6),
                          f'코스피 {pct(eq)} vs 원달러 {pct(fxr)} (20일)', "원화 강세+주가 상승 = 탐욕"))
        except Exception:
            pass

    if px is not None and "HYG" in px.columns and "LQD" in px.columns:
        try:
            h = float(px["HYG"].iloc[-1] / px["HYG"].iloc[-21] - 1) * 100
            l = float(px["LQD"].iloc[-1] / px["LQD"].iloc[-21] - 1) * 100
            comps.append(("정크본드 수요", _scale(h - l, -2.5, 2.5),
                          f'하이일드 {pct(h)} vs 우량채 {pct(l)} (20일)', "위험채권 선호 = 탐욕"))
        except Exception:
            pass

    vals = [c[1] for c in comps if c[1] is not None]
    if not vals:
        return None
    score = int(round(float(np.mean(vals))))
    if score <= 24: label, kind = "극단적 공포", "down"
    elif score <= 44: label, kind = "공포", "warn"
    elif score <= 55: label, kind = "중립", "idle"
    elif score <= 75: label, kind = "탐욕", "warn"
    else: label, kind = "극단적 탐욕", "down"
    return {"score": score, "label": label, "kind": kind, "comps": comps,
            "cnn": fetch_cnn_fng() if market == "US" else None}


# ════════════════════════════════════════════════════════════════════════════
# 엔진 ⑫ 내 투자 관리
# ════════════════════════════════════════════════════════════════════════════
PORT_FILE = "portfolio.json"
LAST_FILE = "last_ticker.json"


def load_json_file(path, default):
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception:
        pass


def load_portfolio():
    if "port" not in st.session_state:
        st.session_state["port"] = load_json_file(PORT_FILE, {"open": [], "closed": []})
    p = st.session_state["port"]
    p.setdefault("open", []); p.setdefault("closed", [])
    return p


def save_portfolio(p):
    st.session_state["port"] = p
    save_json_file(PORT_FILE, p)


def position_review(h, zp=8.0):
    """보유 종목 1건에 대한 오늘의 전략"""
    tk = h["ticker"]
    df, market, name, _ = load_price(tk)
    if df is None or len(df) < 200:
        return {"ok": False, "ticker": tk, "name": tk}
    df = df[~df.index.duplicated(keep="last")].sort_index()
    px = float(df["Close"].iloc[-1])
    buy = float(h["price"])
    qty = float(h.get("qty") or 0)
    bdate = pd.to_datetime(h["date"])
    ret = (px / buy - 1) * 100
    held = int((df.index[-1] - bdate).days)
    ma, ma_ok, _u = ma_stack(df)
    binfo = analyze_base(df, market, zp)
    top = topping_signals(df, binfo, ma)
    sp = sell_pressure(df, ma, top, binfo)
    stop = round_tick(buy * 0.92, market, up=False)
    t1, t2 = round_tick(buy * 1.20, market, False), round_tick(buy * 1.25, market, False)
    peak = float(df.loc[bdate:, "Close"].max()) if len(df.loc[bdate:]) else px
    peak_ret = (peak / buy - 1) * 100
    dd_from_peak = (px / peak - 1) * 100
    eight = (peak_ret >= 20 and held <= 21)
    below50 = (not np.isnan(ma[50])) and px < ma[50]
    below200 = (not np.isnan(ma[200])) and px < ma[200]

    if ret <= -7:
        act, kind, why = "즉시 손절", "fail", f"매수가 대비 {pct(ret)} — 오닐 -7~8% 원칙 도달"
    elif sp["score"] >= 65:
        act, kind, why = "전량 매도 검토", "fail", "매도 압력 " + str(sp["score"]) + "점 · " + (sp["reasons"][0] if sp["reasons"] else "")
    elif ret <= -4 and below50:
        act, kind, why = "손절 준비", "warn", f"{pct(ret)} · 50일선 이탈 — 반등 실패 시 정리"
    elif eight:
        act, kind, why = "8주 보유 (익절 금지)", "pass", f"3주 내 최고 {pct(peak_ret)} 달성 — 오닐 8주 규칙 대상"
    elif sp["score"] >= 45:
        act, kind, why = "절반 익절", "warn", "매도 압력 " + str(sp["score"]) + "점"
    elif ret >= 25:
        act, kind, why = "2차 익절 구간", "warn", f"{pct(ret)} — 잔량 정리 또는 50일선 추적"
    elif ret >= 20:
        act, kind, why = "1차 익절 구간", "warn", f"{pct(ret)} — 절반 이상 실현 검토"
    elif below200:
        act, kind, why = "비중 축소", "fail", "200일선 아래 — 장기 추세 훼손"
    elif ret > 0 and not below50:
        act, kind, why = "보유 유지", "pass", f"{pct(ret)} · 50일선 위 유지"
    else:
        act, kind, why = "보유 · 관찰", "idle", f"{pct(ret)} · 손절선 {fmt(stop, market)} 유지"

    r_mult = ret / 8.0
    return {"ok": True, "ticker": tk, "name": name.split(" (")[0], "market": market,
            "price": px, "buy": buy, "qty": qty, "ret": ret, "held": held,
            "date": bdate, "stop": stop, "t1": t1, "t2": t2, "peak_ret": peak_ret,
            "dd_from_peak": dd_from_peak, "sp": sp, "act": act, "kind": kind, "why": why,
            "ma50": ma[50], "ma200": ma[200], "below50": below50, "below200": below200,
            "binfo": binfo, "r_mult": r_mult, "value": px * qty, "cost": buy * qty,
            "pl": (px - buy) * qty, "top": top}


# ════════════════════════════════════════════════════════════════════════════
# 관심종목 저장 (누적)
# ════════════════════════════════════════════════════════════════════════════
def load_watchlist():
    if "watch" in st.session_state:
        return st.session_state["watch"]
    lst = list(WATCH_DEFAULT)
    try:
        if os.path.exists(WATCH_FILE):
            with open(WATCH_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, list) and saved:
                lst = saved
    except Exception:
        pass
    st.session_state["watch"] = lst
    return lst


def save_watchlist(lst):
    st.session_state["watch"] = lst
    try:
        with open(WATCH_FILE, "w", encoding="utf-8") as f:
            json.dump(lst, f, ensure_ascii=False)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
# 사이드바
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="masthead"><h1>CANSLIM</h1>'
                '<div class="sub">O\'Neil Terminal v3</div></div>', unsafe_allow_html=True)
    _last = load_json_file(LAST_FILE, {}).get("ticker", "NVDA")
    ticker_in = st.text_input("종목코드 / 티커", value=_last,
                              help="한국 6자리 숫자(005930) · 해외 티커(NVDA)")
    st.caption(f"마지막 조회 종목이 자동 저장됩니다 (현재 기본값 {_last})")
    st.markdown("---")
    capital = st.number_input("투자 가능 금액", min_value=0, value=0, step=1000000,
                              help="0이면 수량 계산을 생략합니다")
    risk_pct = st.slider("1회 최대 손실 허용 (%)", 0.5, 3.0, 1.5, 0.1)
    st.markdown("---")
    with st.expander("판정 파라미터"):
        zig_pct = st.slider("베이스 최소 조정폭 (%)", 5.0, 15.0, 8.0, 0.5)
        min_gain = st.slider("FTD 최소 상승률 (%)", 0.8, 2.5, 1.2, 0.1)
        corr_pct = st.slider("조정 인식 하락폭 (%)", 3.0, 10.0, 4.0, 0.5)
    use_weekly = st.checkbox("차트 주봉 보기", value=True)
    st.markdown("---")
    st.markdown(f'<div class="hint mono">FDR {"OK" if HAS_FDR else "X"} · '
                f'YF {"OK" if HAS_YF else "X"} · KRX {"OK" if HAS_KRX else "X"}<br>'
                f'{datetime.now():%Y-%m-%d %H:%M} 기준</div>', unsafe_allow_html=True)

TK = ticker_in.strip().upper()
TABS = st.tabs(["  대시보드  ", "  시장  ", "  환율  ", "  개별종목  ", "  분석보강  ",
                "  뉴스  ", "  종목스캔  ", "  my투자  ", "  사용 가이드  "])


# ════════════════════════════════════════════════════════════════════════════
# 공통 데이터 로드 (탭 간 공유)
# ════════════════════════════════════════════════════════════════════════════
def build_context(tk):
    ctx = {"ok": False, "log": []}
    if not tk:
        return ctx
    dfd, market, name, log = load_price(tk)
    if dfd is None or len(dfd) < 120:
        ctx["log"] = log
        ctx["name"] = tk
        return ctx
    dfd = dfd[~dfd.index.duplicated(keep="last")].sort_index()
    idxs, ilog = load_indices(market)
    fnd = load_kr_fund(tk) if market == "KR" else load_us_fund(tk)
    states = {nm: index_state(idf, min_gain, corr_pct) for nm, idf in idxs.items()}
    uni = load_rs_universe(market)
    bw = buy_window(states, breadth_pct(uni)) if states else None
    lead_nm = max(states, key=lambda k: {"pass": 2, "warn": 1, "fail": 0}[states[k]["kind"]]) \
        if states else None
    lead = states[lead_nm]["df"] if lead_nm else None
    binfo = analyze_base(dfd, market, zig_pct)
    ma, ma_ok, up200 = ma_stack(dfd)
    rating, r = rs_rating(dfd, uni)
    rsl, rs_new = rs_line(dfd, lead) if lead is not None else (None, None)
    ctx.update({"ok": True, "df": dfd, "market": market, "name": name, "log": log + ilog + fnd.get("log", []),
                "idxs": idxs, "states": states, "bw": bw, "lead": lead, "lead_nm": lead_nm,
                "fnd": fnd, "binfo": binfo, "ma": ma, "ma_ok": ma_ok, "up200": up200,
                "rating": rating, "rets": r, "rsl": rsl, "rs_new": rs_new, "uni": uni,
                "price": float(dfd["Close"].iloc[-1])})
    return ctx


CTX = build_context(TK)

if CTX.get("ok") and TK:
    save_json_file(LAST_FILE, {"ticker": TK, "at": datetime.now().isoformat(timespec="seconds")})
    _wl = load_watchlist()
    if TK not in _wl:
        save_watchlist(_wl + [TK])


def derive(ctx, q_over=None, y_over=None):
    """CANSLIM 항목 판정 (탭 공용)"""
    if not ctx.get("ok"):
        return {}
    df, fnd, binfo, ma = ctx["df"], ctx["fnd"], ctx["binfo"], ctx["ma"]
    price = ctx["price"]
    q_g = q_over if q_over is not None else growth_pct(fnd.get("q_eps"), fnd.get("q_eps_prev"))
    y_g = y_over if y_over is not None else growth_pct(fnd.get("y_eps"), fnd.get("y_eps_prev2"))
    roe, opm, q_sales = fnd.get("roe"), fnd.get("opm"), fnd.get("q_sales")
    hi52 = float(df["High"].tail(252).max())
    gap52 = (price / hi52 - 1) * 100
    up_n, dn_n, ad_ratio, ad_grade = accumulation(df)
    m_ok = bool(ctx["bw"] and ctx["bw"]["kind"] == "pass")
    c_ok = q_g is not None and q_g >= 25
    a_ok = (y_g is not None and y_g >= 25) or (roe or 0) >= 17
    n_ok = gap52 >= -15 and ctx["ma_ok"]
    s_ok = ad_ratio >= 1.0
    l_ok = ctx["rating"] is not None and ctx["rating"] >= 80
    if ctx["market"] == "KR":
        flow = load_kr_flow(TK)
        i_ok = False
        fo20 = in20 = None
        if flow is not None and not flow.empty:
            def gc(*ks):
                for k in ks:
                    if k in flow.columns:
                        return flow[k]
                return None
            fo, ins = gc("외국인합계", "외국인"), gc("기관합계", "기관")
            fo20 = float(fo.tail(20).sum()) / 1e8 if fo is not None else None
            in20 = float(ins.tail(20).sum()) / 1e8 if ins is not None else None
            i_ok = (fo20 or 0) > 0 or (in20 or 0) > 0
        else:
            i_ok = ad_ratio >= 1.3
        flowinfo = {"flow": flow, "fo20": fo20, "in20": in20}
    else:
        inst = fnd.get("inst")
        i_ok = inst is not None and 15 <= inst <= 90
        flowinfo = {"flow": None, "inst": inst}
    base_ok = bool(binfo and len(binfo["flaws"]) <= 1 and binfo["cur"]["depth"] <= 35
                   and binfo["cur"]["weeks"] >= 5 and binfo["cur"]["count"] <= 2)
    checks = [("M", "시장이 확정 상승세", m_ok, 15),
              ("C", "분기 EPS +25% 이상", c_ok, 15),
              ("A", "연간 EPS +25% 또는 ROE 17%+", a_ok, 10),
              ("N", "52주 고점 -15% 이내 + 정배열", n_ok, 10),
              ("S", "거래량 매집 우위", s_ok, 10),
              ("L", "RS 80 이상", l_ok, 15),
              ("I", "기관·외국인 매수 우위", i_ok, 10),
              ("B", "결함 없는 1~2차 베이스", base_ok, 15)]
    score = sum(w for _, _, ok, w in checks if ok)
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    top = topping_signals(df, binfo, ma)
    bot = bottoming_signals(df, binfo, ma)
    sp = sell_pressure(df, ma, top, binfo)
    eps_r = eps_rating(200 if q_g == 999 else q_g, 200 if y_g == 999 else y_g)
    smr = smr_grade(q_sales, opm, roe)
    comp = composite(eps_r, ctx["rating"], smr, ad_grade, base_ok, m_ok)
    return {"q_g": q_g, "y_g": y_g, "roe": roe, "opm": opm, "q_sales": q_sales,
            "hi52": hi52, "gap52": gap52, "up_n": up_n, "dn_n": dn_n,
            "ad_ratio": ad_ratio, "ad_grade": ad_grade, "m_ok": m_ok, "c_ok": c_ok,
            "a_ok": a_ok, "n_ok": n_ok, "s_ok": s_ok, "l_ok": l_ok, "i_ok": i_ok,
            "base_ok": base_ok, "checks": checks, "score": score, "grade": grade,
            "top": top, "bot": bot, "sp": sp, "eps_r": eps_r, "smr": smr, "comp": comp,
            "flowinfo": flowinfo}


D = derive(CTX) if CTX.get("ok") else {}


# ════════════════════════════════════════════════════════════════════════════
# TAB 0 — 대시보드
# ════════════════════════════════════════════════════════════════════════════
with TABS[0]:
    if not CTX.get("ok"):
        st.error("시세를 가져오지 못했습니다. 한국 종목은 6자리 숫자(005930), 해외는 티커(NVDA)로 "
                 "입력하세요.")
        if CTX.get("log"):
            st.markdown(table(["항목", "상태", "내용"], CTX["log"]), unsafe_allow_html=True)
    else:
        df, market, price = CTX["df"], CTX["market"], CTX["price"]
        chg = (price / float(df["Close"].iloc[-2]) - 1) * 100
        st.markdown(
            f'<div class="masthead"><h1>{CTX["name"]} '
            f'<span class="mono amb" style="font-size:1.05rem">{fmt(price, market)}'
            f'{unit(market)}</span> <span class="mono {"up" if chg>=0 else "down"}" '
            f'style="font-size:.9rem">{pct(chg,2)}</span></h1>'
            f'<div class="sub">오늘의 브리핑 · {df.index[-1]:%Y-%m-%d} 종가 기준 · '
            f'데이터 {df.index[0]:%Y-%m-%d}부터 {len(df):,}거래일</div></div>',
            unsafe_allow_html=True)

        bw, binfo = CTX["bw"], CTX["binfo"]
        c = st.columns(4)
        if bw:
            c[0].markdown(bigcard("오늘 매수 적합도", f'{bw["score"]}<span style="font-size:.9rem">/100</span>',
                                  bw["grade"] + bar(bw["score"]),
                                  "up" if bw["kind"] == "pass" else ("amb" if bw["kind"] == "warn" else "down")),
                          unsafe_allow_html=True)
        else:
            c[0].markdown(bigcard("오늘 매수 적합도", "—", "지수 데이터 없음"), unsafe_allow_html=True)
        c[1].markdown(bigcard("종목 상태", binfo["stage"].split(" —")[0] if binfo else "베이스 없음",
                              (f'{binfo["type"]} · 피봇 {fmt(binfo["pivot"], market)} '
                               f'({pct(binfo["gap"])})' if binfo else "매수 기준점 없음"),
                              "up" if (binfo and binfo["kind"] == "pass") else
                              ("amb" if (binfo and binfo["kind"] == "warn") else "down")),
                      unsafe_allow_html=True)
        c[2].markdown(bigcard("CANSLIM 스코어", f'{D["score"]}<span style="font-size:.9rem">/100</span>',
                              f'{D["grade"]}등급 · RS {CTX["rating"] or "—"}' + bar(D["score"]),
                              "up" if D["score"] >= 65 else ("amb" if D["score"] >= 50 else "down")),
                      unsafe_allow_html=True)
        c[3].markdown(bigcard("매도 압력", f'{D["sp"]["score"]}<span style="font-size:.9rem">/100</span>',
                              D["sp"]["action"] + bar(D["sp"]["score"],
                                                      color=P_DOWN if D["sp"]["score"] >= 45 else P_UP),
                              "down" if D["sp"]["score"] >= 45 else "up"), unsafe_allow_html=True)

        step_header("TODAY", "오늘 무엇을 할 것인가")
        acts = []
        if bw and bw["kind"] == "fail":
            acts.append(("신규 매수 보류", "fail",
                         f'시장 적합도 {bw["score"]}점 — ' + bw["parts"][0][2]))
        if binfo and binfo["kind"] == "pass" and D["score"] >= 65 and bw and bw["kind"] != "fail":
            acts.append(("매수 실행 검토", "pass",
                         f'피봇 {fmt(binfo["pivot"], market)} 위 매수 구간 · 스코어 {D["score"]}점'))
        if binfo and binfo["kind"] == "warn":
            acts.append(("돌파 감시", "warn",
                         f'피봇 {fmt(binfo["pivot"], market)} 돌파 + 거래량 50일 평균 1.4배 이상 확인'))
        if binfo and binfo["kind"] == "idle":
            acts.append(("관망", "idle", f'피봇까지 {pct(binfo["gap"])} — 베이스 형성 진행 중'))
        if binfo and binfo["kind"] == "fail":
            acts.append(("추격 매수 금지", "fail", binfo["stage"]))
        if D["sp"]["score"] >= 45:
            acts.append(("보유분 점검", "fail", " · ".join(D["sp"]["reasons"][:2]) or "매도 압력 상승"))
        if not acts:
            acts.append(("특이사항 없음", "idle", "기존 계획 유지"))
        st.markdown(table(["조치", "구분", "근거"],
                          [[a, tag(a, k), why] for a, k, why in acts]), unsafe_allow_html=True)

        cc = st.columns([1.3, 1])
        with cc[0]:
            if CTX["states"]:
                rows = []
                for nm, s in CTX["states"].items():
                    f = s["ftd"]
                    ft = f'{f["date"]:%m-%d} ({f["day"]}일차)' if f.get("date") is not None else "없음"
                    rows.append([nm, tag(s["label"], s["kind"]), ft, f'{s["dd_n"]}개',
                                 "위" if s["ab200"] else "아래", pct(s["chg"], 2)])
                st.markdown(table(["지수", "국면", "FTD", "분산일", "200일선", "당일"], rows),
                            unsafe_allow_html=True)
        with cc[1]:
            if market == "US":
                fx, dxy, fxlog = load_fx()
                if fx is not None:
                    a = fx_analysis(fx)
                    st.markdown(card("USD/KRW", f'{a["cur"]:,.1f}',
                                     f'3년 백분위 {a["pctile"]:.0f}% · 1년 평균 대비 '
                                     f'{pct(a["dev"].get("1년"))}<br>권장 환전 비중 {a["now_ratio"]}%',
                                     "up" if a["pctile"] <= 40 else ("amb" if a["pctile"] <= 70 else "down")),
                                unsafe_allow_html=True)
            else:
                st.markdown(card("업종·수급", D["ad_grade"] + " 등급",
                                 f'매집 {D["up_n"]}일 vs 분산 {D["dn_n"]}일'), unsafe_allow_html=True)

        news, nlog = load_news(TK, market)
        if news:
            step_header("NEWS", f"신뢰 기관 최신 뉴스 {len(news)}건", "전체는 뉴스 탭에서")
            for it in classify_news(news)[:3]:
                when = f'{it["when"]:%Y-%m-%d}' if it["when"] is not None else ""
                link = f'<a href="{it["url"]}" target="_blank">{it["title"]}</a>' if it["url"] else it["title"]
                st.markdown(f'<div class="news"><div class="src">{it["pub"]} · {when}</div>'
                            f'<div class="ti">{link}</div>'
                            f'<div class="mt">{" · ".join(t[0] for t in it["topics"])} · 논조 {it["tone"]}</div>'
                            f'</div>', unsafe_allow_html=True)

        read_box(
            f'오닐 방식은 순서가 정해져 있습니다. <b>① 시장 → ② 베이스 → ③ 상대강도 → ④ 실적 → ⑤ 진입가</b>. '
            f'오늘 시장 적합도는 <b>{bw["score"] if bw else "—"}점({bw["grade"] if bw else "판정불가"})</b>, '
            f'이 종목은 <b>{binfo["stage"] if binfo else "베이스 없음"}</b>, '
            f'CANSLIM 스코어는 <b>{D["score"]}점</b>입니다. '
            f'{"세 가지가 모두 정렬되어 있으니 개별종목 탭에서 진입가와 수량을 확인하세요." if (bw and bw["kind"]!="fail" and binfo and binfo["kind"]=="pass" and D["score"]>=65) else "하나라도 어긋나면 기다리는 것이 오닐의 원칙입니다. 매수 기회는 다시 옵니다."}',
            "오늘의 판단", "oneil")


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — 시장
# ════════════════════════════════════════════════════════════════════════════
with TABS[1]:
    if not CTX.get("ok") or not CTX["states"]:
        st.warning("지수 데이터를 불러오지 못했습니다.")
    else:
        states, bw = CTX["states"], CTX["bw"]
        st.markdown('<div class="masthead"><h1>시장 방향 (M)</h1><div class="sub">'
                    'Follow-Through Day · Distribution Days · Buy Window</div></div>',
                    unsafe_allow_html=True)

        cols = st.columns(len(states))
        for (nm, s), col in zip(states.items(), cols):
            f = s["ftd"]
            if f.get("date") is not None:
                ftxt = (f'{f["date"]:%Y-%m-%d} · 저점 {f["day"]}일차 {pct(f["gain"],2)}<br>'
                        f'경과 {f.get("since","?")}일 · 이후 {pct(f.get("ret_since"))}')
            elif f["state"] == "rally_attempt":
                ftxt = f'FTD 미발생 · 랠리 {f.get("rally_day","?")}일차<br>저점 {f["low_date"]:%Y-%m-%d}'
            else:
                ftxt = f'조정 없이 상승 지속<br>최대 조정 {pct(f.get("max_dd"))}'
            cls = "up" if s["kind"] == "pass" else ("amb" if s["kind"] == "warn" else "down")
            col.markdown(card(nm, f'<span class="{cls}">{s["label"]}</span>',
                              f'{ftxt}<br>분산일 <b>{s["dd_n"]}개</b> · '
                              f'50일선 {"위" if s["ab50"] else "아래"} · '
                              f'200일선 {"위" if s["ab200"] else "아래"}'), unsafe_allow_html=True)

        step_header("BUY WINDOW", "오늘은 매수하기 좋은 날인가", "5개 항목 100점 환산")
        c = st.columns([1, 2])
        c[0].markdown(bigcard("매수 적합도", f'{bw["score"]}<span style="font-size:1rem">/100</span>',
                              f'<b>{bw["grade"]}</b>' + bar(bw["score"]),
                              "up" if bw["kind"] == "pass" else ("amb" if bw["kind"] == "warn" else "down")),
                      unsafe_allow_html=True)
        c[1].markdown(table(["항목", "점수", "근거"],
                            [[a, f'<span class="mono">{b}</span>', d] for a, b, d in bw["parts"]]),
                      unsafe_allow_html=True)

        series = buy_window_series(states)
        if series is not None and len(series) > 20:
            st.markdown('<div class="hint">최근 120일 매수 적합도 추이 — 추세·분산일·당일 등락 기준 '
                        '근사값입니다. 선이 75 위에 머무는 구간이 오닐이 말한 신규 매수 창입니다.</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(buywin_chart(series), use_container_width=True)

        read_box(
            '오닐은 지수를 매일 봤습니다. 이유는 하나입니다. <b>시장이 조정일 때 산 종목은 4개 중 3개가 '
            '실패</b>하기 때문입니다. 세 가지만 보면 됩니다.<br><br>'
            '<b>① FTD</b> — 하락이 멈춘 저점에서 4일 이상 지난 뒤, 지수가 크게 오르면서 거래량까지 늘어난 날. '
            '"조정이 끝났다"는 시장의 확인 도장입니다. 저점을 다시 깨면 무효가 됩니다.<br>'
            '<b>② 분산일</b> — 지수가 떨어졌는데 거래량은 늘어난 날. 기관이 팔았다는 흔적입니다. '
            '25일 안에 6개가 쌓이면 상승세는 끝났다고 봅니다.<br>'
            '<b>③ 200일선</b> — 지수가 그 아래면 무조건 방어입니다.<br><br>'
            f'오늘 적합도는 <b>{bw["score"]}점 · {bw["grade"]}</b>입니다.',
            "오닐의 시장 읽기", "oneil")

        step_header("FEAR & GREED", "공포탐욕지수", "군중이 어디에 서 있는가")
        fg = fear_greed(CTX["market"], states, CTX["uni"],
                        load_fx()[0] if CTX["market"] == "KR" else None)
        if fg is None:
            st.markdown('<div class="hint">공포탐욕지수 산출에 필요한 데이터를 '
                        '가져오지 못했습니다.</div>', unsafe_allow_html=True)
        else:
            fc = st.columns([1, 2])
            gauge = ("극단적 공포 ◀ 공포 ◀ 중립 ▶ 탐욕 ▶ 극단적 탐욕")
            gcol = P_DOWN if fg["kind"] == "down" else (P_ACC if fg["kind"] == "warn" else P_UP)
            fc[0].markdown(bigcard("공포탐욕지수 (자체 산출)",
                                   f'{fg["score"]}<span style="font-size:1rem">/100</span>',
                                   f'<b>{fg["label"]}</b>' + bar(fg["score"], color=gcol)
                                   + f'<div style="font-size:.68rem;margin-top:.3rem">{gauge}</div>',
                                   "down" if fg["kind"] == "down" else
                                   ("amb" if fg["kind"] == "warn" else "up")),
                           unsafe_allow_html=True)
            rows = [[a, f'<span class="mono">{v:.0f}</span>' if v is not None else "—", ev_, note]
                    for a, v, ev_, note in fg["comps"]]
            fc[1].markdown(table(["구성 항목", "점수", "측정값", "해석"], rows),
                           unsafe_allow_html=True)
            if fg.get("cnn"):
                cn = fg["cnn"]
                st.markdown(f'<div class="ev">참고 · CNN 공식 Fear &amp; Greed Index '
                            f'<b>{cn["score"]:.0f} ({cn["rating"]})</b> · 1주 전 '
                            f'{num(cn.get("week"),0)} · 1개월 전 {num(cn.get("month"),0)}</div>',
                            unsafe_allow_html=True)
            read_box(
                '공포탐욕지수는 <b>군중의 감정</b>을 숫자로 바꾼 것입니다. 0에 가까울수록 다들 무서워하고, '
                '100에 가까울수록 다들 낙관합니다.<br><br>'
                '오닐은 이 지수를 쓰지 않았지만 같은 이야기를 했습니다. '
                '<b>"모두가 사고 싶어 안달일 때가 팔 때"</b>라고요. 다만 주의할 점이 있습니다. '
                '공포지수가 낮다고 바로 사는 것은 오닐 방식이 아닙니다. 공포 구간에서는 '
                '<b>FTD가 뜰 때까지 기다렸다가</b> 사야 하고, 탐욕 구간에서는 <b>신규 매수 규모를 줄이고 '
                '보유 종목의 고점 신호</b>를 챙겨야 합니다.<br><br>'
                f'현재 <b>{fg["score"]}점 · {fg["label"]}</b>입니다. '
                + ("극단 구간이므로 평소보다 신중하게 접근하세요."
                   if fg["score"] <= 24 or fg["score"] >= 76
                   else "극단 구간은 아니므로 시장 국면(FTD·분산일) 판단을 우선하세요."),
                "공포탐욕지수 읽는 법", "oneil")

        for nm, s in states.items():
            with st.expander(f'{nm} 상세 차트 — 분산일 {s["dd_n"]}개'):
                st.plotly_chart(index_chart(s, nm), use_container_width=True)
                if s["dds"]:
                    rows = [[f'{r["date"]:%Y-%m-%d}', pct(r["chg"], 2), fmt(r["close"], "US")]
                            for r in s["dds"][::-1]]
                    st.markdown(table(["분산일", "등락률", "종가"], rows), unsafe_allow_html=True)
                else:
                    st.markdown('<div class="hint">유효한 분산일이 없습니다. 건강한 상승세입니다.</div>',
                                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — 개별종목
# ════════════════════════════════════════════════════════════════════════════
with TABS[3]:
    if not CTX.get("ok"):
        st.error("종목 데이터를 불러오지 못했습니다.")
    else:
        df, market, price, ma = CTX["df"], CTX["market"], CTX["price"], CTX["ma"]
        binfo, fnd = CTX["binfo"], CTX["fnd"]
        st.markdown(f'<div class="masthead"><h1>{CTX["name"]}</h1><div class="sub">'
                    f'STEP 1 추세 · 2 베이스 · 3 실적 · 4 밸류 · 5 상대강도 · 6 수급 · '
                    f'7 종합 · 8 시나리오 · 9 매도신호</div></div>', unsafe_allow_html=True)

        # STEP 1
        step_header("STEP 1", "N — 신고가와 추세 구조")
        hi52, lo52 = D["hi52"], float(df["Low"].tail(252).min())
        c = st.columns(4)
        c[0].markdown(card("52주 고점 대비", pct(D["gap52"]),
                           f'고점 {fmt(hi52, market)} · 사상최고 {fmt(float(df["High"].max()), market)}',
                           "up" if D["gap52"] >= -15 else "down"), unsafe_allow_html=True)
        c[1].markdown(card("52주 저점 대비", pct((price / lo52 - 1) * 100),
                           f'저점 {fmt(lo52, market)}',
                           "up" if (price / lo52 - 1) * 100 >= 30 else "mut"), unsafe_allow_html=True)
        c[2].markdown(card("이동평균", "정배열" if CTX["ma_ok"] else "미정렬",
                           f'50 {fmt(ma[50], market)} · 150 {fmt(ma[150], market)} · '
                           f'200 {fmt(ma[200], market)}', "up" if CTX["ma_ok"] else "down"),
                      unsafe_allow_html=True)
        c[3].markdown(card("200일선 방향", "상승" if CTX["up200"] else "하락/횡보",
                           "4~5개월 상승 추세 요구", "up" if CTX["up200"] else "down"),
                      unsafe_allow_html=True)
        st.markdown(evidence([("52주 고점 이격", pct(D["gap52"]), "-15% 이내", D["gap52"] >= -15),
                              ("이동평균 정배열", "주가>50>150>200" if CTX["ma_ok"] else "깨짐",
                               "정배열", CTX["ma_ok"]),
                              ("200일선 방향", "상승" if CTX["up200"] else "비상승", "상승", CTX["up200"])]),
                    unsafe_allow_html=True)

        # STEP 2 베이스
        step_header("STEP 2", "베이스 판정 (주봉 기준)")
        if binfo is None:
            st.markdown(tag("베이스 미형성", "fail") +
                        ' <span class="hint">매수 기준점(피봇)이 없습니다.</span>',
                        unsafe_allow_html=True)
        else:
            b, h = binfo["cur"], binfo["handle"]
            c = st.columns(4)
            c[0].markdown(card("베이스 유형", binfo["type"], binfo["note"], "amb"), unsafe_allow_html=True)
            c[1].markdown(card("깊이 / 기간", f'{b["depth"]:.1f}% / {b["weeks"]:.0f}주',
                               "정상 12~33% · 5주 이상",
                               "up" if b["depth"] <= 33 and b["weeks"] >= 5 else "down"),
                          unsafe_allow_html=True)
            c[2].markdown(card("베이스 차수", f'{b["count"]}차',
                               f'과거 돌파 성공 {binfo["win"][0]}/{binfo["win"][1]}회',
                               "up" if b["count"] <= 2 else "down"), unsafe_allow_html=True)
            c[3].markdown(card("피봇 (매수 기준가)", fmt(binfo["pivot"], market),
                               f'{binfo["pivot_src"]} · 현재가 {pct(binfo["gap"])}', "amb"),
                          unsafe_allow_html=True)
            tl = [["베이스 시작 (좌측 고점)", f'{b["start"]:%Y-%m-%d}', fmt(b["left_high"], market),
                   f'{(b["low_date"]-b["start"]).days}일간 하락'],
                  ["베이스 저점", f'{b["low_date"]:%Y-%m-%d}', fmt(b["low"], market),
                   f'고점 대비 {b["depth"]:.1f}% 하락']]
            if h:
                tl += [["핸들 시작", f'{h["start"]:%Y-%m-%d}', fmt(h["high"], market),
                        f'{h["days"]}거래일 · 깊이 {h["depth"]:.1f}%'],
                       ["핸들 저점", f'{h["low_date"]:%Y-%m-%d}', fmt(h["low"], market),
                        "이탈 시 베이스 실패"]]
            tl.append(["돌파 완성" if b["completed"] else "현재 (진행 중)",
                       f'{b["end"]:%Y-%m-%d}', fmt(price, market),
                       "베이스 완성" if b["completed"] else f'{b["weeks"]:.0f}주째 형성 중'])
            st.markdown(table(["시점", "날짜", "가격", "비고"], tl), unsafe_allow_html=True)
            st.markdown(cross_section(binfo, price, market), unsafe_allow_html=True)
            st.markdown(f'{tag(binfo["stage"], binfo["kind"])} '
                        f'<span class="hint">매수 구간 <b class="mono amb">'
                        f'{fmt(binfo["pivot"], market)} ~ {fmt(binfo["pivot"]*1.05, market)}</b></span>',
                        unsafe_allow_html=True)

            cc = st.columns(2)
            with cc[0]:
                rows = [["형태 품질(U/V)", f'{b["u_ratio"]:.0f}%', verdict(b["u_ratio"] >= 15),
                         "저점권 체류 15%+ = U자형"],
                        ["거래량 균형", num(b["vol_bal"], 2),
                         verdict(not np.isnan(b["vol_bal"]) and b["vol_bal"] >= 0.8),
                         "우측÷좌측 0.8배 이상"],
                        ["선행 상승", pct(b["prior_gain"]),
                         verdict(not np.isnan(b["prior_gain"]) and b["prior_gain"] >= 30), "+30% 이상"],
                        ["깊이", f'{b["depth"]:.1f}%', verdict(b["depth"] <= 33), "12~33%"]]
                st.markdown(table(["베이스 항목", "측정", "판정", "기준"], rows), unsafe_allow_html=True)
            with cc[1]:
                if h is None:
                    st.markdown('<div class="hint"><b>핸들 미형성.</b> 베이스 상단 회복 후 나타나는 '
                                '얕은 눌림이 핸들입니다. 핸들 없이 좌측 고점을 바로 돌파하면 '
                                '실패 확률이 높습니다.</div>', unsafe_allow_html=True)
                else:
                    rows = [["핸들 깊이", f'{h["depth"]:.1f}%', verdict(h["ok_depth"]), "8~12%"],
                            ["핸들 기간", f'{h["days"]}일', verdict(h["ok_days"]), "1주 이상"],
                            ["핸들 위치", "상단" if h["ok_pos"] else "하단", verdict(h["ok_pos"]),
                             "베이스 상단 절반"],
                            ["거래량 건조", num(h["dry"], 2), verdict(h["ok_dry"]), "1.0배 미만"],
                            ["50일선 지지", "지지" if h["ok_ma50"] else "이탈", verdict(h["ok_ma50"]),
                             "핸들 저점이 50일선 위"]]
                    st.markdown(table(["핸들 항목", "측정", "판정", "기준"], rows), unsafe_allow_html=True)

            if binfo["flaws"]:
                nf = len(binfo["flaws"])
                st.markdown(f'<br>{tag(str(nf) + "건 결함", "fail")}'
                            + table(["결함", "측정", "정상 기준"],
                                    [[a, f'<span class="mono">{b2}</span>', c2]
                                     for a, b2, c2 in binfo["flaws"]]), unsafe_allow_html=True)
            else:
                st.markdown(f'<br>{tag("결함 없음", "pass")} '
                            '<span class="hint">오닐이 지적한 결함 항목에 해당하지 않습니다.</span>',
                            unsafe_allow_html=True)

            if binfo["bo_day"] is not None:
                ok = binfo["bo_vol"] is not None and not np.isnan(binfo["bo_vol"]) and binfo["bo_vol"] >= 1.4
                st.markdown(f'<br>{tag("피봇 돌파 발생", "pass" if ok else "warn")} '
                            f'<span class="hint"><b>{binfo["bo_day"]:%Y-%m-%d}</b> · 당일 거래량 '
                            f'50일 평균의 <b class="mono">{num(binfo["bo_vol"],2)}배</b>. '
                            f'{"거래량 40% 이상 증가 — 유효한 돌파." if ok else "거래량 부족 — 가짜 돌파 위험."}'
                            f'</span>', unsafe_allow_html=True)

            read_box(
                f'이 종목은 <b>{b["start"]:%Y년 %m월 %d일}</b> 고점 {fmt(b["left_high"], market)}에서 베이스가 '
                f'시작돼 <b>{b["low_date"]:%Y년 %m월 %d일}</b> {fmt(b["low"], market)}까지 {b["depth"]:.0f}% '
                f'하락했고, 현재 <b>{b["weeks"]:.0f}주째 {binfo["type"]}</b> 형태입니다. '
                f'매수 기준가는 <b>{fmt(binfo["pivot"], market)}</b>({binfo["pivot_src"]})이며 '
                f'현재가는 그보다 {pct(binfo["gap"])} 위치입니다.<br><br>'
                f'과거 이 종목의 베이스 돌파 성공률은 <b>{binfo["win"][0]}/{binfo["win"][1]}회</b>였습니다'
                f'(돌파 후 120일 내 20% 이상 상승 기준). '
                f'{"결함이 없어 구조적으로 신뢰할 만합니다." if not binfo["flaws"] else "위 결함이 2건 이상이면 돌파해도 실패 확률이 높습니다."}')

            if len(binfo["bases"]) > 1:
                with st.expander(f'과거 베이스 이력 {len(binfo["bases"])}개'):
                    hist = []
                    for bb in binfo["bases"][-10:]:
                        after = df.loc[bb["end"]:].head(120)
                        fwd = ((float(after["Close"].max()) / bb["left_high"] - 1) * 100
                               if bb["completed"] and len(after) > 2 else None)
                        hist.append({"차수": f'{bb["count"]}차', "시작": bb["start"].strftime("%Y-%m-%d"),
                                     "저점": bb["low_date"].strftime("%Y-%m-%d"),
                                     "종료": bb["end"].strftime("%Y-%m-%d"), "주": round(bb["weeks"]),
                                     "깊이(%)": round(bb["depth"], 1),
                                     "상태": "돌파" if bb["completed"] else "진행중",
                                     "돌파후 최대(%)": None if fwd is None else round(fwd, 1)})
                    st.dataframe(pd.DataFrame(hist), use_container_width=True, hide_index=True)

        # STEP 3 실적 — 최근 3분기 · 최근 3년
        step_header("STEP 3", "C · A — 실적 성장 (최근 3분기 · 최근 3년)",
                    "오닐: 3분기 연속 +25% · 3년 연속 이익 증가")
        FH = fin_history(fnd)
        with st.expander("실적이 비어 있으면 직접 입력 (DART · 10-Q 기준)"):
            mc = st.columns(4)
            m_q = mc[0].number_input("최근 분기 EPS", value=0.0, format="%.2f")
            m_qp = mc[1].number_input("전년 동기 EPS", value=0.0, format="%.2f")
            m_y = mc[2].number_input("최근 연간 EPS", value=0.0, format="%.2f")
            m_yp = mc[3].number_input("전년 연간 EPS", value=0.0, format="%.2f")
        q_g = growth_pct(m_q, m_qp) if (m_q and m_qp) else D["q_g"]
        y_g = growth_pct(m_y, m_yp) if (m_y and m_yp) else D["y_g"]
        c_ok, a_ok = (q_g is not None and q_g >= 25), (y_g is not None and y_g >= 25)

        qp, qn = FH.get("q_pass"), FH.get("q_n", 0)
        yp, yn = FH.get("y_pass"), FH.get("y_n", 0)
        c = st.columns(4)
        c[0].markdown(card("C · 최근 분기 EPS", "흑자전환" if q_g == 999 else pct(q_g),
                           (f'3분기 중 <b>{qp}/{qn}분기</b>가 +25% 충족' if qp is not None
                            else "분기 이력 수집 실패"), "up" if c_ok else "down"),
                      unsafe_allow_html=True)
        c[1].markdown(card("A · 최근 연간 EPS", "흑자전환" if y_g == 999 else pct(y_g),
                           (f'3년 중 <b>{yp}/{yn}년</b>이 증가' if yp is not None
                            else "연간 이력 수집 실패"), "up" if a_ok else "down"),
                      unsafe_allow_html=True)
        c[2].markdown(card("분기 매출", pct(D["q_sales"]), "기준 +25%",
                           "up" if (D["q_sales"] or 0) >= 25 else "mut"), unsafe_allow_html=True)
        c[3].markdown(card("ROE / 영업이익률", f'{pct(D["roe"],0,False)} / {pct(D["opm"],0,False)}',
                           "ROE 17% 이상", "up" if (D["roe"] or 0) >= 17 else "mut"),
                      unsafe_allow_html=True)

        def _fin_rows(tab, market_):
            if tab is None or tab.empty:
                return None
            rows = []
            for _, r in tab.iterrows():
                per = r["기간"]
                cells = [f'<b>{per}</b>']
                for m in ("매출액", "영업이익", "순이익", "EPS"):
                    v, g = r.get(m), r.get(m + "증감")
                    if g is not None and isinstance(g, float) and np.isnan(g):
                        g = None
                    if v is None or (isinstance(v, float) and np.isnan(v)):
                        cells.append("—")
                        continue
                    if abs(v) >= 1e8:
                        vs = f'{v/1e8:,.0f}억' if market_ == "KR" else f'{v/1e9:,.2f}B'
                    elif abs(v) >= 1e4 and m != "EPS":
                        vs = f'{v:,.0f}'
                    else:
                        vs = f'{v:,.2f}' if abs(v) < 100 else f'{v:,.0f}'
                    if g is None:
                        cells.append(f'<span class="mono">{vs}</span>')
                    else:
                        cl = "up" if g >= 25 else ("ink2" if g >= 0 else "down")
                        gt = "흑자전환" if g == 999 else pct(g, 0)
                        cells.append(f'<span class="mono">{vs}</span><br>'
                                     f'<span class="mono {cl}" style="font-size:.72rem">{gt}</span>')
                rows.append(cells)
            return rows

        cc = st.columns(2)
        with cc[0]:
            st.markdown(f'<div class="hint" style="margin:.3rem 0"><b>최근 3분기</b> · '
                        f'증감은 {FH["q_kind"] or "—"}</div>', unsafe_allow_html=True)
            qr = _fin_rows(FH["q"], market)
            if qr:
                st.markdown(table(["분기", "매출액", "영업이익", "순이익", "EPS"], qr),
                            unsafe_allow_html=True)
                if FH.get("q_list"):
                    seq = " → ".join("흑자전환" if x == 999 else pct(x, 0) for x in FH["q_list"])
                    acc = FH.get("accel")
                    st.markdown(f'<div class="ev">분기 EPS 증가율 추이 <b>{seq}</b> '
                                + (tag("가속", "pass") if acc else tag("둔화", "warn")) + '</div>',
                                unsafe_allow_html=True)
            else:
                st.markdown('<div class="hint">분기 실적을 불러오지 못했습니다. '
                            '위 입력란에 공시 수치를 넣으면 판정에 반영됩니다.</div>',
                            unsafe_allow_html=True)
        with cc[1]:
            st.markdown('<div class="hint" style="margin:.3rem 0"><b>최근 3년</b> · '
                        '증감은 전년 대비 (가장 오래된 연도는 비교 대상이 없으면 공란)</div>',
                        unsafe_allow_html=True)
            yr = _fin_rows(FH["y"], market)
            if yr:
                st.markdown(table(["연도", "매출액", "영업이익", "순이익", "EPS"], yr),
                            unsafe_allow_html=True)
                if FH.get("y_list"):
                    seq = " → ".join("흑자전환" if x == 999 else pct(x, 0) for x in FH["y_list"])
                    st.markdown(f'<div class="ev">연간 EPS 증가율 추이 <b>{seq}</b></div>',
                                unsafe_allow_html=True)
            else:
                st.markdown('<div class="hint">연간 실적을 불러오지 못했습니다.</div>',
                            unsafe_allow_html=True)

        if FH.get("q_tab_extra") is None and fnd.get("y_tab") is not None:
            yt = fnd["y_tab"]
            extra = [m for m in ("ROE", "영업이익률", "부채비율") if m in yt.index]
            if extra:
                cols3 = list(yt.columns)[-3:]
                rows = [[m] + [f'<span class="mono">{num(safe(yt.loc[m, c]),1)}</span>'
                               for c in cols3] for m in extra]
                st.markdown("<br>" + table(["지표"] + cols3, rows), unsafe_allow_html=True)

        st.markdown(evidence([
            ("최근 분기 EPS 증가율", "흑자전환" if q_g == 999 else pct(q_g), "+25% 이상", c_ok),
            ("3분기 중 25% 충족", f'{qp}/{qn}분기' if qp is not None else "—",
             "3분기 모두", bool(qp is not None and qn and qp == qn)),
            ("연간 EPS 증가율", "흑자전환" if y_g == 999 else pct(y_g), "+25% 이상", a_ok),
            ("3년 연속 이익 증가", f'{yp}/{yn}년' if yp is not None else "—",
             "3년 모두", bool(yp is not None and yn and yp == yn)),
            ("분기 매출 증가율", pct(D["q_sales"]), "+25% 이상", (D["q_sales"] or 0) >= 25),
            ("ROE", pct(D["roe"], 1, False), "17% 이상", (D["roe"] or 0) >= 17)]),
            unsafe_allow_html=True)
        if fnd.get("table") is not None:
            with st.expander("원본 실적표"):
                st.dataframe(fnd["table"], use_container_width=True)
        read_box(
            f'오닐은 한 분기만 좋은 회사를 믿지 않았습니다. <b>최근 3분기가 연속으로 25% 이상</b> 늘고, '
            f'<b>최근 3년 연간 이익도 계속 늘어야</b> 합니다. 한 분기만 좋으면 일회성 이익일 수 있습니다.<br><br>'
            f'그리고 절대 수준보다 <b>증가율이 빨라지는지</b>가 중요합니다. '
            f'30% → 45% → 70%처럼 가속되는 회사가 대박 종목이 됩니다. 반대로 70% → 45% → 30%은 '
            f'숫자는 좋아 보여도 이미 정점을 지난 신호입니다.<br><br>'
            f'현재 분기는 {qp if qp is not None else "?"}/{qn if qn else "?"}분기가 기준을 넘었고, '
            f'연간은 {yp if yp is not None else "?"}/{yn if yn else "?"}년이 증가했습니다.')


        # STEP 4 밸류에이션
        step_header("STEP 4", "재무 · 밸류에이션")
        per, pbr, psr, debt = fnd.get("per"), fnd.get("pbr"), fnd.get("psr"), fnd.get("debt")
        peg = fnd.get("peg")
        if peg is None and per and y_g and y_g not in (0, 999) and y_g > 0:
            peg = per / y_g
        mc_v = fnd.get("mktcap")
        cap_txt = "—"
        if mc_v:
            cap_txt = (f'{mc_v/1e12:,.1f}조원' if market == "KR" and mc_v >= 1e12 else
                       f'{mc_v/1e8:,.0f}억원' if market == "KR" else f'${mc_v/1e9:,.1f}B')
        c = st.columns(5)
        c[0].markdown(card("PER / 선행 PER", f'{num(per,1)} / {num(fnd.get("fper"),1)}',
                           "오닐은 고PER을 결격으로 보지 않음"), unsafe_allow_html=True)
        c[1].markdown(card("PEG", num(peg, 2), "PER÷성장률 · 1.5 이하 양호",
                           "up" if (peg is not None and peg <= 1.5) else "mut"), unsafe_allow_html=True)
        c[2].markdown(card("PBR / PSR", f'{num(pbr,2)} / {num(psr,2)}', "자산·매출 대비"),
                      unsafe_allow_html=True)
        c[3].markdown(card("부채비율", num(debt, 0), "150 미만 양호",
                           "up" if (debt is not None and debt < 150) else "mut"), unsafe_allow_html=True)
        c[4].markdown(card("시가총액", cap_txt, "클수록 상승 탄력 둔화"), unsafe_allow_html=True)
        read_box('오닐은 <b>PER이 높다는 이유로 좋은 종목을 거르지 말라</b>고 했습니다. 실제 대박 종목들은 '
                 '상승 시작 시점에 이미 시장 평균보다 비쌌습니다. 대신 PEG와 부채비율은 봅니다. '
                 'PEG가 1 근처면 성장 속도 대비 값이 싸다는 뜻이고, 부채비율이 몇 년새 크게 늘었다면 '
                 '이익의 질을 의심해야 합니다. 밸류에이션은 <b>매수 여부가 아니라 리스크 크기</b>를 재는 도구입니다.')

        # STEP 5 상대강도
        step_header("STEP 5", "L — 주도주 여부")
        sect = load_sector_rank(market, fnd.get("sector"))
        r = CTX["rets"]
        c = st.columns(4)
        c[0].markdown(card("RS Rating", str(CTX["rating"]) if CTX["rating"] else "산출 불가",
                           "KRX 전종목 백분위" if market == "KR" else "유동성 상위군 백분위(근사)",
                           "up" if D["l_ok"] else "down"), unsafe_allow_html=True)
        c[1].markdown(card("기간 수익률", f'{pct(r["r3"],0)} / {pct(r["r6"],0)} / {pct(r["r12"],0)}',
                           "3개월 / 6개월 / 12개월"), unsafe_allow_html=True)
        c[2].markdown(card("RS 라인", "신고가" if CTX["rs_new"] else
                           ("미달" if CTX["rs_new"] is not None else "—"),
                           "주가보다 먼저 신고가면 강력 신호",
                           "up" if CTX["rs_new"] else "mut"), unsafe_allow_html=True)
        if sect:
            c[3].markdown(card("업종 순위", f'{sect["rank"]}위 / {sect["total"]}',
                               f'{sect["label"]}<br>상위 업종: {", ".join(sect["top"])}',
                               "up" if sect["rank"] <= 4 else "mut"), unsafe_allow_html=True)
        else:
            c[3].markdown(card("업종 순위", "—", "업종 데이터 미수집(국내 미지원)"), unsafe_allow_html=True)
        st.markdown(evidence([("RS Rating", str(CTX["rating"] or "—"), "80 이상", D["l_ok"]),
                              ("RS 라인 신고가", "신고가" if CTX["rs_new"] else "미달",
                               "돌파 전 신고가", bool(CTX["rs_new"])),
                              ("업종 순위", f'{sect["rank"]}위' if sect else "—",
                               "상위 4위 이내", bool(sect and sect["rank"] <= 4))]),
                    unsafe_allow_html=True)
        read_box('RS Rating은 <b>전체 종목 중 이 종목의 수익률 순위</b>입니다. 80이면 상위 20%. '
                 '오닐은 80 미만은 후보에서 아예 뺐고, 실제 성공한 돌파는 대부분 90 이상이었습니다. '
                 'RS 라인(주가÷지수)이 주가보다 먼저 신고가를 내면 시장을 앞서간다는 뜻으로 성공률이 크게 오릅니다.')

        # STEP 6 수급
        step_header("STEP 6", "S · I — 거래량과 기관 수급")
        vma50 = float(df["Volume"].rolling(50).mean().iloc[-1])
        vratio = float(df["Volume"].iloc[-1]) / vma50 if vma50 else np.nan
        c = st.columns(4)
        c[0].markdown(card("당일 거래량", f'{num(vratio,2)}배', "50일 평균 대비",
                           "up" if vratio >= 1.4 else "mut"), unsafe_allow_html=True)
        c[1].markdown(card("매집 / 분산일", f'{D["up_n"]} / {D["dn_n"]}',
                           f'A/D 등급 {D["ad_grade"]} · 최근 50일',
                           "up" if D["s_ok"] else "down"), unsafe_allow_html=True)
        fi = D["flowinfo"]
        if market == "KR":
            if fi.get("fo20") is not None or fi.get("in20") is not None:
                c[2].markdown(card("외국인 20일", f'{num(fi.get("fo20"),0)}억', "순매수 거래대금",
                                   "up" if (fi.get("fo20") or 0) > 0 else "down"), unsafe_allow_html=True)
                c[3].markdown(card("기관 20일", f'{num(fi.get("in20"),0)}억', "순매수 거래대금",
                                   "up" if (fi.get("in20") or 0) > 0 else "down"), unsafe_allow_html=True)
            else:
                c[2].markdown(card("기관/외국인", "수집 실패", "A/D 등급으로 대체 판정", "mut"),
                              unsafe_allow_html=True)
                c[3].markdown(card("대체 판정", D["ad_grade"], "거래량 패턴 기반"), unsafe_allow_html=True)
            if fi.get("flow") is not None:
                with st.expander("투자자별 일별 순매수"):
                    st.dataframe(fi["flow"].tail(25).iloc[::-1], use_container_width=True)
        else:
            c[2].markdown(card("기관 보유 비중", pct(fnd.get("inst"), 1, False), "15~90% 적정",
                               "up" if D["i_ok"] else "mut"), unsafe_allow_html=True)
            c[3].markdown(card("유통주식 / 내부자",
                               f'{num((fnd.get("float") or 0)/1e6,0)}M / {pct(fnd.get("insider"),1,False)}',
                               "유통량 적을수록 탄력 큼"), unsafe_allow_html=True)
        st.plotly_chart(stock_chart(df, binfo["weekly"] if binfo else to_weekly(df), binfo,
                                    market, CTX["rsl"], use_weekly), use_container_width=True)

        # STEP 7 종합
        step_header("STEP 7", "종합 등급")
        c = st.columns(5)
        c[0].markdown(card("Composite (근사)", str(D["comp"]), "종합 · 95+ 최상위",
                           "up" if D["comp"] >= 80 else ("amb" if D["comp"] >= 65 else "down")),
                      unsafe_allow_html=True)
        c[1].markdown(card("EPS Rating (근사)", str(D["eps_r"] or "—"), "이익 성장 순위"),
                      unsafe_allow_html=True)
        c[2].markdown(card("RS Rating", str(CTX["rating"] or "—"), "주가 상대강도"), unsafe_allow_html=True)
        c[3].markdown(card("SMR (근사)", D["smr"] or "—", "매출·마진·ROE"), unsafe_allow_html=True)
        c[4].markdown(card("A/D", D["ad_grade"], "매집·분산"), unsafe_allow_html=True)
        cc = st.columns([1, 2.3])
        cc[0].markdown(bigcard("CANSLIM 스코어",
                               f'{D["score"]}<span style="font-size:1rem">/100</span>',
                               f'{D["grade"]}등급' + bar(D["score"]),
                               "up" if D["score"] >= 65 else ("amb" if D["score"] >= 50 else "down")),
                       unsafe_allow_html=True)
        cc[1].markdown(table(["", "기준", "판정", "배점"],
                             [[f'<span class="mono amb">{k}</span>', d, verdict(ok),
                               f'<span class="mono mut">{w}</span>'] for k, d, ok, w in D["checks"]]),
                       unsafe_allow_html=True)

        # STEP 8 시나리오
        step_header("STEP 8", "매매 시나리오")
        atrp = atr_pct(df)
        sc = scenario(binfo, price, market, ma, capital, risk_pct, atrp)
        if sc is None:
            st.markdown('<div class="hint">베이스가 없어 진입 기준가를 제시할 수 없습니다.</div>',
                        unsafe_allow_html=True)
        elif sc["entry"] is None:
            st.markdown(f'{tag("신규 진입 구간 아님", "fail")} <span class="hint">{sc["mode"]}. '
                        f'추격 대신 <b class="mono amb">{fmt(sc["alt"], market)}</b>(50일선) 되돌림을 '
                        f'기다리거나 다음 베이스를 기다리세요.</span>', unsafe_allow_html=True)
            read_box('피봇 +5%를 넘긴 가격에 사는 것이 오닐 규칙에서 가장 흔한 실패 원인입니다. '
                     '진입가가 높아진 만큼 -8% 손절선이 베이스 안쪽으로 들어와, 정상적인 흔들림에도 '
                     '손절당하기 때문입니다. 늦었다면 사지 않는 것이 정답입니다.')
        else:
            rows = [["진입가", fmt(sc["entry"], market), sc["mode"]],
                    ["매수 허용 상한", fmt(sc["buy_hi"], market), "피봇 +5% · 이 위로는 추격 금지"],
                    ["손절가", f'{fmt(sc["stop"], market)} ({pct(sc["stop_pct"])})',
                     "진입가 -8%와 핸들/베이스 저점 중 타이트한 쪽"],
                    ["1차 익절", f'{fmt(sc["t1"], market)} (+20%)', "절반 이상 실현"],
                    ["2차 익절", f'{fmt(sc["t2"], market)} (+25%)', "잔량 정리 또는 50일선 이탈 시"],
                    ["손익비", f'1 : {num(sc["rr"],1)}', "2 이상 양호"]]
            if sc["qty"]:
                rows.append(["매수 수량", f'{sc["qty"]:,}주',
                             f'투입 {fmt(sc["pos_amt"], market)}{unit(market)} · 최대 손실 '
                             f'{fmt(sc["risk_amt"], market)}{unit(market)} (계좌의 {risk_pct}%)'])
            if sc["atr"]:
                rows.append(["손절폭 적정성", sc["atr"][0], sc["atr"][1]])
            st.markdown(table(["항목", "가격", "규칙"], rows), unsafe_allow_html=True)
            ew = eight_week_rule(df, binfo)
            if ew:
                st.markdown(f'<br>{tag("8주 보유 규칙", "pass" if ew["on"] else "idle")} '
                            f'<span class="hint">{ew["msg"]}'
                            + (f' · {ew["until"]:%Y-%m-%d}까지 보유' if ew["on"] else "")
                            + '</span>', unsafe_allow_html=True)
            if not D["m_ok"]:
                st.markdown(f'<br>{tag("시장 조건 미충족", "fail")} <span class="hint">'
                            '지수가 확정 상승세가 아닙니다. 베이스가 완벽해도 신규 매수는 보류가 원칙입니다.'
                            '</span>', unsafe_allow_html=True)

        # STEP 9 매도 신호
        step_header("STEP 9", "오닐의 고점 · 저점 신호", "보유 중이라면 여기부터")
        c = st.columns([1, 2])
        c[0].markdown(bigcard("매도 압력",
                              f'{D["sp"]["score"]}<span style="font-size:1rem">/100</span>',
                              f'<b>{D["sp"]["action"]}</b>'
                              + bar(D["sp"]["score"], color=P_DOWN if D["sp"]["score"] >= 45 else P_UP),
                              "down" if D["sp"]["score"] >= 45 else "up"), unsafe_allow_html=True)
        c[1].markdown(table(["산정 근거", ""],
                            [[x, ""] for x in (D["sp"]["reasons"] or ["특이 신호 없음"])]),
                      unsafe_allow_html=True)
        cc = st.columns(2)
        with cc[0]:
            st.markdown('<div class="hint" style="margin-bottom:.4rem"><b>고점 신호</b> — '
                        '강세 속에서 파는 신호</div>', unsafe_allow_html=True)
            st.markdown(table(["신호", "측정", "판정", "의미"],
                              [[a, f'<span class="mono">{m}</span>',
                                tag("발생", "fail") if ok else tag("없음", "pass"),
                                f'<span class="m">{why}</span>']
                               for a, ok, m, std, why in D["top"]]), unsafe_allow_html=True)
        with cc[1]:
            st.markdown('<div class="hint" style="margin-bottom:.4rem"><b>저점 · 바닥 신호</b> — '
                        '반등 시작의 근거</div>', unsafe_allow_html=True)
            st.markdown(table(["신호", "측정", "판정", "의미"],
                              [[a, f'<span class="mono">{m}</span>',
                                tag("확인", "pass") if ok else tag("미확인", "idle"),
                                f'<span class="m">{why}</span>']
                               for a, ok, m, std, why in D["bot"]]), unsafe_allow_html=True)
        read_box(
            '오닐의 매도는 두 종류입니다. <b>① 방어적 매도</b> — 매수가에서 7~8% 빠지면 이유 불문 매도. '
            '이건 손실을 작게 유지하는 규칙이라 예외가 없습니다. <b>② 공격적 매도</b> — 주가가 잘 오르고 '
            '있을 때 파는 것입니다. 위 고점 신호들이 그 신호로, 오닐은 "누구나 팔고 싶어 안달일 때 팔라"고 '
            '했습니다. 신문에 좋은 기사가 나오고 급등할 때가 실제로는 마지막 국면인 경우가 많습니다.<br><br>'
            f'현재 매도 압력은 <b>{D["sp"]["score"]}점 · {D["sp"]["action"]}</b>입니다.',
            "오닐의 매도 원칙", "oneil")

        step_header("SUMMARY", "한 문단 결론")
        bpart = (f'{binfo["type"]}가 {binfo["cur"]["start"]:%Y년 %m월}부터 '
                 f'{binfo["cur"]["weeks"]:.0f}주째 진행 중이고 피봇은 {fmt(binfo["pivot"], market)}'
                 if binfo else "형성된 베이스가 없고")
        vt = ("오닐 기준 매수 후보로 볼 수 있습니다." if D["score"] >= 65 and D["m_ok"] and D["base_ok"]
              else "지금은 매수보다 관찰 단계입니다." if D["score"] >= 50
              else "오닐 기준에는 뚜렷하게 미달합니다.")
        st.markdown(f'<div class="read oneil"><span class="h">결론</span>'
                    f'{CTX["name"].split(" (")[0]}는 CANSLIM <b>{D["score"]}점({D["grade"]}등급)</b>, '
                    f'RS <b>{CTX["rating"] or "—"}</b>, 분기 EPS '
                    f'<b>{"흑자전환" if q_g == 999 else pct(q_g)}</b>입니다. {bpart}, '
                    f'현재 상태는 <b>{binfo["stage"] if binfo else "매수 기준점 없음"}</b>, '
                    f'매도 압력은 <b>{D["sp"]["score"]}점</b>입니다. {vt}</div>',
                    unsafe_allow_html=True)

        with st.expander("데이터 수집 상태"):
            st.markdown(table(["항목", "상태", "출처 / 사유"],
                              [[a, tag(b2, "pass" if b2 == "성공" else
                                       ("warn" if b2 in ("재시도", "부분") else "fail")), c2]
                               for a, b2, c2 in CTX["log"]]), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — 환율
# ════════════════════════════════════════════════════════════════════════════
with TABS[2]:
    st.markdown('<div class="masthead"><h1>환율 분석 — USD/KRW</h1><div class="sub">'
                '기간별 전략 · 평균 대비 위치 · 환전 시기 평가</div></div>', unsafe_allow_html=True)
    fx, dxy, fxlog = load_fx()
    if fx is None:
        st.error("환율 데이터를 불러오지 못했습니다.")
        st.markdown(table(["항목", "상태", "내용"], fxlog), unsafe_allow_html=True)
    else:
        a = fx_analysis(fx)
        c = st.columns(4)
        c[0].markdown(bigcard("현재 환율", f'{a["cur"]:,.1f}',
                              f'52주 {a["lo52"]:,.0f} ~ {a["hi52"]:,.0f} · 밴드 위치 {a["band"]:.0f}%'),
                      unsafe_allow_html=True)
        c[1].markdown(bigcard("3년 백분위", f'{a["pctile"]:.0f}%',
                              ("3년 중 싼 편 — 환전 유리" if a["pctile"] <= 40 else
                               "중간권" if a["pctile"] <= 70 else "3년 중 비싼 편 — 환전 불리")
                              + bar(a["pctile"]),
                              "up" if a["pctile"] <= 40 else ("amb" if a["pctile"] <= 70 else "down")),
                      unsafe_allow_html=True)
        c[2].markdown(bigcard("추세", a["trend"],
                              f'20일 {a["ma20"]:,.0f} · 60일 {a["ma60"]:,.0f} · 120일 {a["ma120"]:,.0f}'),
                      unsafe_allow_html=True)
        c[3].markdown(bigcard("권장 환전 비중", f'{a["now_ratio"]}%', a["guide"], "amb"),
                      unsafe_allow_html=True)

        step_header("AVERAGE", "기간별 평균 환율과 현재 위치", "평균보다 낮으면 환전에 유리")
        rows = []
        for lab in ("1개월", "6개월", "1년", "2년", "3년"):
            if lab in a["avgs"]:
                d = a["dev"][lab]
                rows.append([lab, f'{a["avgs"][lab]:,.1f}', f'<span class="mono">{pct(d)}</span>',
                             tag("평균 이하 (유리)", "pass") if d < 0 else tag("평균 이상 (불리)", "fail"),
                             "현재 환율이 이 기간 평균보다 "
                             + (f'{abs(d):.1f}% 낮음' if d < 0 else f'{d:.1f}% 높음')])
        st.markdown(table(["기간", "평균 환율", "현재 대비", "판정", "설명"], rows),
                    unsafe_allow_html=True)
        st.plotly_chart(fx_chart(a["series"], a), use_container_width=True)

        step_header("STRATEGY", "기간별 환전 전략", "투자 기간에 맞는 판단")
        rows = []
        for horizon, method, (act, kind, why) in a["plans"]:
            rows.append([f'<b>{horizon}</b>', method, tag(act, kind), why])
        st.markdown(table(["기간", "판단 기준", "전략", "근거"], rows), unsafe_allow_html=True)

        step_header("TIMING", "환전 실행 가이드")
        c = st.columns([1, 1.6])
        c[0].markdown(card("지금 환전할 비중", f'{a["now_ratio"]}%',
                           f'{a["guide"]}<br>나머지는 아래 트리거에서 분할', "amb"),
                      unsafe_allow_html=True)
        with c[1]:
            if a["triggers"]:
                st.markdown(table(["추가 환전 트리거", "가격", "조건"],
                                  [[x[0], f'{x[1]:,.1f}', x[2]] for x in a["triggers"]]),
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="hint">현재 환율이 주요 평균선 아래에 있어 별도 대기 '
                            '트리거가 없습니다. 계획된 비중을 분할 실행하세요.</div>',
                            unsafe_allow_html=True)
        st.markdown(evidence([
            ("3년 백분위", f'{a["pctile"]:.0f}%', "40% 이하면 환전 유리", a["pctile"] <= 40),
            ("1년 평균 대비", pct(a["dev"].get("1년")), "0% 이하", (a["dev"].get("1년") or 0) <= 0),
            ("RSI(14)", f'{a["rsi"]:.0f}', "40 이하면 단기 저가권", a["rsi"] <= 40),
            ("연 변동성", f'{a["vol"]:.1f}%', "참고 지표", True)]), unsafe_allow_html=True)

        if CTX.get("ok") and CTX["market"] == "US" and CTX.get("binfo"):
            b = CTX["binfo"]
            krw_entry = b["pivot"] * a["cur"]
            st.markdown(f'<div class="hint" style="margin-top:.6rem">이 종목({TK})의 피봇 '
                        f'<b class="mono">${b["pivot"]:,.2f}</b>를 현재 환율로 환산하면 '
                        f'<b class="mono">{krw_entry:,.0f}원</b>입니다. 환율이 5% 하락하면 '
                        f'주가가 그대로여도 원화 평가액은 약 5% 줄어듭니다.</div>',
                        unsafe_allow_html=True)

        read_box(
            '오닐은 환율을 다루지 않았지만, 해외주식 투자자에게 환율은 <b>매수 단가의 일부</b>입니다. '
            '원화 기준 수익 = 주가 수익 + 환차익이기 때문입니다.<br><br>'
            '판단은 두 가지만 기억하면 됩니다. <b>① 지금이 역사적으로 어디쯤인가</b> — 3년 백분위가 '
            '낮을수록 싸게 사는 것입니다. <b>② 지금 흐름이 어느 쪽인가</b> — 오르는 중이면 서두르지 말고, '
            '내리는 중이면 분할로 담습니다. 한 번에 다 바꾸는 것은 종목을 한 번에 다 사는 것과 같은 '
            '실수입니다.<br><br>'
            f'현재 <b>3년 백분위 {a["pctile"]:.0f}%</b>, 추세는 <b>{a["trend"]}</b>이므로 '
            f'필요 금액의 <b>{a["now_ratio"]}%</b>를 지금 환전하고 나머지는 위 트리거에서 나누는 것이 '
            f'합리적입니다.', "환율을 읽는 법", "oneil")


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — 뉴스
# ════════════════════════════════════════════════════════════════════════════
with TABS[5]:
    st.markdown(f'<div class="masthead"><h1>{TK} 뉴스</h1><div class="sub">'
                f'신뢰 기관 필터 · 주제 분류 · 투자 시사점</div></div>', unsafe_allow_html=True)
    if not CTX.get("ok"):
        st.info("종목을 먼저 입력하세요.")
    else:
        news, nlog = load_news(TK, CTX["market"])
        news = classify_news(news)
        st.markdown('<div class="hint">로이터·블룸버그·WSJ·CNBC·배런스·IBD 등(국내는 연합뉴스·'
                    '한국경제·매일경제 등) 신뢰 기관 기사만 남기고 나머지는 걸러냅니다.</div>',
                    unsafe_allow_html=True)
        if not news:
            st.warning("신뢰 기관 뉴스가 수집되지 않았습니다. 아래 사유를 확인하세요.")
            if nlog:
                st.markdown(table(["항목", "상태", "내용"], nlog), unsafe_allow_html=True)
        else:
            step_header("INSIGHT", "뉴스 시사점 · 투자 시 고려할 점")
            for line in news_insight(news, CTX["binfo"], D.get("q_g"), CTX["rating"]):
                st.markdown(f'<div class="ev">· {line}</div>', unsafe_allow_html=True)
            cnt = {}
            for it in news:
                for nm, cs in it["topics"]:
                    cnt[nm] = cnt.get(nm, 0) + 1
            if cnt:
                rows = []
                cmap = {n: c for n, k, c in NEWS_TOPICS}
                for nm, v in sorted(cnt.items(), key=lambda x: -x[1]):
                    rows.append([nm, str(v) + "건", cmap.get(nm, "—")])
                st.markdown("<br>" + table(["주제", "건수", "CANSLIM 연결"], rows),
                            unsafe_allow_html=True)
            step_header("HEADLINES", f"최신 {len(news)}건")
            for it in news:
                when = f'{it["when"]:%Y-%m-%d %H:%M}' if it["when"] is not None else ""
                link = (f'<a href="{it["url"]}" target="_blank">{it["title"]}</a>'
                        if it["url"] else it["title"])
                tone_cls = "up" if it["tone"] == "긍정" else ("down" if it["tone"] == "부정" else "mut")
                st.markdown(f'<div class="news"><div class="src">{it["pub"]} · {when}</div>'
                            f'<div class="ti">{link}</div><div class="mt">'
                            f'{" / ".join(t[0] for t in it["topics"])} · '
                            f'<span class="{tone_cls}">논조 {it["tone"]}</span></div></div>',
                            unsafe_allow_html=True)
        read_box('오닐은 뉴스로 사고팔지 말라고 했습니다. 뉴스는 이미 가격에 반영되기 때문입니다. '
                 '대신 <b>뉴스에 주가와 거래량이 어떻게 반응했는지</b>를 보라고 했습니다. '
                 '악재가 나왔는데 저점이 지켜지고 거래량이 늘지 않으면 팔 사람이 이미 다 팔았다는 뜻이고, '
                 '호재가 나왔는데 대량 거래로 밀린다면 기관이 물량을 넘기고 있다는 뜻입니다.<br><br>'
                 '주제 분류와 논조는 제목의 키워드로 자동 판별한 것이라 참고용입니다. '
                 '실제 판단은 기사 본문과 공시 원문으로 확인하세요.', "뉴스를 대하는 태도", "oneil")


# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — 종목 스캔
# ════════════════════════════════════════════════════════════════════════════
with TABS[6]:
    st.markdown('<div class="masthead"><h1>종목 스캔</h1><div class="sub">'
                '추가한 종목이 목록에 계속 남습니다</div></div>', unsafe_allow_html=True)
    wl = load_watchlist()
    c = st.columns([2, 1, 1])
    add = c[0].text_input("종목 추가 (쉼표·공백 구분)", value="",
                          placeholder="예: AAPL MSFT 005930")
    if c[1].button("목록에 추가", use_container_width=True):
        new = [t.strip().upper() for t in add.replace(",", " ").split() if t.strip()]
        merged = wl + [t for t in new if t not in wl]
        save_watchlist(merged)
        wl = merged
        st.success(f"{len(new)}종목 추가 · 현재 {len(wl)}종목")
    if c[2].button("현재 종목 추가", use_container_width=True) and TK:
        if TK not in wl:
            wl = wl + [TK]
            save_watchlist(wl)
            st.success(f"{TK} 추가")

    edit = st.text_area("현재 목록 (직접 편집 가능)", value=" ".join(wl), height=80)
    cc = st.columns([1, 1, 4])
    if cc[0].button("목록 저장"):
        save_watchlist([t.strip().upper() for t in edit.replace(",", " ").split() if t.strip()])
        st.success("저장 완료")
    if cc[1].button("기본값 복원"):
        save_watchlist(list(WATCH_DEFAULT))
        st.info("기본 목록으로 되돌렸습니다")

    if st.button("스캔 실행", type="primary"):
        tks = load_watchlist()
        bar_ = st.progress(0.0, text="준비 중…")
        rows, ucache = [], {}
        for i, t in enumerate(tks, 1):
            bar_.progress(i / len(tks), text=f"{t} ({i}/{len(tks)})")
            try:
                d, mk, nm, _ = load_price(t)
                if d is None or len(d) < 200:
                    rows.append({"종목": t, "상태": "데이터 없음"})
                    continue
                if mk not in ucache:
                    ucache[mk] = load_rs_universe(mk)
                rt, _r = rs_rating(d, ucache[mk])
                bi = analyze_base(d, mk, zig_pct)
                m_, mok_, _u = ma_stack(d)
                p = float(d["Close"].iloc[-1])
                hi = float(d["High"].tail(252).max())
                sp_ = sell_pressure(d, m_, topping_signals(d, bi, m_), bi)
                rows.append({"종목": nm.split(" (")[0][:16], "코드": t, "현재가": round(p, 2),
                             "52주고(%)": round((p / hi - 1) * 100, 1), "RS": rt,
                             "베이스": bi["type"] if bi else "미형성",
                             "시작일": bi["cur"]["start"].strftime("%Y-%m-%d") if bi else None,
                             "차수": bi["cur"]["count"] if bi else None,
                             "깊이(%)": round(bi["cur"]["depth"], 1) if bi else None,
                             "결함": len(bi["flaws"]) if bi else None,
                             "피봇": bi["pivot"] if bi else None,
                             "피봇대비(%)": round(bi["gap"], 1) if bi else None,
                             "매도압력": sp_["score"],
                             "상태": bi["stage"] if bi else "베이스 미형성"})
            except Exception as e:
                rows.append({"종목": t, "상태": f"오류: {type(e).__name__}"})
        bar_.empty()
        out = pd.DataFrame(rows)
        if "RS" in out.columns:
            out = out.sort_values("RS", ascending=False, na_position="last")
        st.session_state["scan_result"] = out
    if "scan_result" in st.session_state:
        st.dataframe(st.session_state["scan_result"], use_container_width=True, hide_index=True)
        read_box('걸러내는 순서: <b>① 상태가 "매수 가능 구간"</b> → <b>② RS 80 이상</b> → '
                 '<b>③ 결함 0~1건</b> → <b>④ 차수 1~2</b> → <b>⑤ 매도압력 45 미만</b>. '
                 '여기까지 남은 종목만 개별종목 탭에서 정밀 검증하세요. '
                 '오닐은 한 번에 4~8종목만 보유하라고 했습니다.')


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — 분석보강 (기본 분석에서 빠지기 쉬운 항목)
# ════════════════════════════════════════════════════════════════════════════
with TABS[4]:
    st.markdown('<div class="masthead"><h1>분석보강</h1><div class="sub">'
                'CANSLIM 본체에는 없지만 실패를 줄이는 항목들</div></div>', unsafe_allow_html=True)
    if not CTX.get("ok"):
        st.info("종목을 먼저 입력하세요.")
    else:
        df, market, ma = CTX["df"], CTX["market"], CTX["ma"]
        price = CTX["price"]
        diag = extra_diagnostics(df, market, CTX["binfo"], CTX["fnd"], CTX["lead"], capital, ma)

        step_header("RISK", "변동성 · 손절폭 적정성", "고정 -8%가 이 종목에 맞는가")
        c = st.columns(4)
        c[0].markdown(card("ATR (일간 변동성)", f'{diag["atr"]:.2f}%',
                           "이 종목이 하루에 평균적으로 움직이는 폭"), unsafe_allow_html=True)
        c[1].markdown(card("적정 손절폭", f'{diag["atr"]*2.5:.1f}%',
                           "ATR×2.5 — 이보다 좁으면 정상 흔들림에 손절당함",
                           "down" if diag["atr"] * 2.5 > 8 else "up"), unsafe_allow_html=True)
        c[2].markdown(card("베타", num(diag["beta"], 2), "1보다 크면 지수보다 크게 움직임"),
                      unsafe_allow_html=True)
        c[3].markdown(card("최근 2년 최대낙폭", pct(diag["mdd2y"]),
                           f'전 기간 {pct(diag["mdd_all"])}'), unsafe_allow_html=True)
        read_box(f'오닐의 -8% 손절은 <b>모든 종목에 같은 숫자</b>를 쓰는 규칙입니다. 그런데 하루 변동폭이 '
                 f'{diag["atr"]:.1f}%인 종목에 8% 손절을 걸면 이틀치 정상 변동만으로도 손절될 수 있습니다. '
                 f'이 종목의 적정 손절폭은 <b>{diag["atr"]*2.5:.1f}%</b> 수준이므로, '
                 f'{"8% 손절이 다소 타이트합니다. 수량을 줄여 같은 금액 손실 한도를 맞추는 편이 낫습니다." if diag["atr"]*2.5 > 8 else "8% 손절이 충분히 여유 있습니다. 오닐 규칙 그대로 쓰면 됩니다."}')

        step_header("CONFIDENCE", "80% 신뢰구간 주가 변동 범위",
                    "이 종목이 통계적으로 움직일 수 있는 폭")
        vp = volatility_profile(df, 0.80)
        if vp is None:
            st.markdown('<div class="hint">데이터가 부족해 변동성 분석을 할 수 없습니다.</div>',
                        unsafe_allow_html=True)
        else:
            vc = st.columns(4)
            vc[0].markdown(card("일간 표준편차", f'{vp["sd_daily"]:.2f}%',
                                "하루 수익률의 흔들림 폭"), unsafe_allow_html=True)
            vc[1].markdown(card("연환산 변동성", f'{vp["ann"]:.1f}%',
                                f'최근 60일 기준 {vp["ann60"]:.1f}% · 국면 {vp["regime"]}',
                                "down" if vp["regime"] == "확대" else "up"), unsafe_allow_html=True)
            vc[2].markdown(card("-8% 손절 도달 확률", f'{vp["hit_stop"]:.0f}%',
                                "과거 20거래일 구간 기준 이력 빈도",
                                "down" if vp["hit_stop"] >= 35 else "up"), unsafe_allow_html=True)
            vc[3].markdown(card("+20% 목표 도달 확률", f'{vp["hit_tgt"]:.0f}%',
                                "과거 60거래일 구간 기준 이력 빈도",
                                "up" if vp["hit_tgt"] >= 30 else "mut"), unsafe_allow_html=True)
            rows = []
            for r in vp["rows"]:
                emp = ("—" if np.isnan(r["elo"]) else
                       f'<span class="mono">{r["elo"]:+.1f}% ~ {r["ehi"]:+.1f}%</span>')
                pxlo = price * (1 + r["lo"] / 100)
                pxhi = price * (1 + r["hi"] / 100)
                rows.append([f'<b>{r["기간"]}</b>',
                             f'<span class="mono">{r["sigma"]:.1f}%</span>',
                             f'<span class="mono down">{r["lo"]:+.1f}%</span> ~ '
                             f'<span class="mono up">{r["hi"]:+.1f}%</span>',
                             f'<span class="mono">{fmt(pxlo, market)} ~ {fmt(pxhi, market)}</span>',
                             emp])
            st.markdown(table(["기간", "표준편차(σ)", "80% 신뢰구간 변동률",
                               "예상 가격 범위", "실제 이력 10~90%"], rows),
                        unsafe_allow_html=True)
            st.markdown(evidence([
                ("연환산 변동성", f'{vp["ann"]:.1f}%', "40% 미만이면 관리 가능", vp["ann"] < 40),
                ("변동성 국면", vp["regime"], "안정 또는 축소", vp["regime"] != "확대"),
                ("수익률 왜도(skew)", f'{vp["skew"]:+.2f}',
                 "음수면 급락 꼬리가 두꺼움", vp["skew"] >= 0),
                ("첨도(kurtosis)", f'{vp["kurt"]:.1f}',
                 "3 이하면 정규분포에 가까움", vp["kurt"] <= 3),
                ("손절/목표 확률비", f'{vp["hit_stop"]:.0f}% vs {vp["hit_tgt"]:.0f}%',
                 "목표 확률이 더 높아야 유리", vp["hit_tgt"] >= vp["hit_stop"])]),
                unsafe_allow_html=True)
            read_box(
                f'<b>80% 신뢰구간</b>이란, 앞으로 100번 중 80번은 이 범위 안에서 움직인다는 뜻입니다. '
                f'(나머지 20번은 위아래로 더 크게 벗어납니다.)<br><br>'
                f'이 종목은 한 달 기준 <b>{vp["rows"][2]["lo"]:+.1f}% ~ {vp["rows"][2]["hi"]:+.1f}%</b>, '
                f'가격으로는 <b>{fmt(price*(1+vp["rows"][2]["lo"]/100), market)} ~ '
                f'{fmt(price*(1+vp["rows"][2]["hi"]/100), market)}</b> 범위가 정상 변동입니다. '
                f'여기서 <b>-8% 손절선이 이 범위 안에 들어 있다면</b>, 종목에 문제가 없어도 '
                f'정상적인 흔들림만으로 손절될 수 있다는 뜻입니다.<br><br>'
                f'실제로 과거 20거래일 구간 중 <b>{vp["hit_stop"]:.0f}%</b>에서 -8% 이상 밀렸고, '
                f'60거래일 구간 중 <b>{vp["hit_tgt"]:.0f}%</b>에서 +20% 이상 올랐습니다. '
                + ("목표 도달 확률이 손절 확률보다 높아 기대값이 유리합니다."
                   if vp["hit_tgt"] >= vp["hit_stop"] else
                   "손절 도달 확률이 더 높으므로, 진입 시점(피봇 근처)을 더 엄격하게 지켜야 합니다.")
                + '<br><br>왜도가 음수면 급락 꼬리가 두껍다는 뜻이라, 갑작스러운 하락 위험이 '
                  '평균보다 큽니다. 첨도가 높으면 평소엔 잠잠하다가 가끔 크게 튄다는 의미입니다.',
                "80% 신뢰구간이란", "oneil")

        step_header("LIQUIDITY", "유동성 · 체결 위험")
        c = st.columns(3)
        tv = diag["turnover"]
        tv_txt = f'{tv/1e8:,.0f}억원' if market == "KR" else f'${tv/1e6:,.0f}M'
        c[0].markdown(card("20일 평균 거래대금", tv_txt,
                           "기관이 못 들어오는 종목은 오래 못 오릅니다",
                           "up" if diag["liq_ok"] else "down"), unsafe_allow_html=True)
        c[1].markdown(card("내 주문 비중", pct(diag["order_ratio"], 2, False)
                           if not np.isnan(diag["order_ratio"]) else "—",
                           "일평균 거래대금 대비 · 1% 넘으면 체결 불리",
                           "down" if (not np.isnan(diag["order_ratio"]) and diag["order_ratio"] > 1) else "up"),
                      unsafe_allow_html=True)
        c[2].markdown(card("유통주식 비율", pct(diag["float_ratio"], 1, False),
                           "낮을수록 상승 탄력 크고 변동도 큼"), unsafe_allow_html=True)

        step_header("EVENT", "이벤트 리스크")
        c = st.columns(3)
        ed = diag["earn_days"]
        c[0].markdown(card("다음 실적 발표",
                           f'D-{ed}' if ed is not None and ed >= 0 else ("미확인" if ed is None else "지남"),
                           "돌파 직전 실적 발표는 큰 갭 위험",
                           "down" if (ed is not None and 0 <= ed <= 5) else "up"), unsafe_allow_html=True)
        c[1].markdown(card("과거 갭 상위 5%", pct(diag["gap_p95"], 1, False),
                           "이 종목이 하루 만에 벌어질 수 있는 폭"), unsafe_allow_html=True)
        c[2].markdown(card("50일선 이격", pct(diag["dist_ma50"]),
                           "+15% 넘으면 눌림 대기가 유리",
                           "down" if diag["dist_ma50"] > 15 else "up"), unsafe_allow_html=True)

        step_header("HISTORY", "이 종목의 베이스 돌파 승률", "과거가 미래를 보장하진 않지만 성향은 보여줍니다")
        if diag["win_rate"] is not None:
            st.markdown(card("과거 돌파 성공률", f'{diag["win_rate"]:.0f}%',
                             f'{diag["win_txt"]} · 돌파 후 120일 내 +20% 도달 기준',
                             "up" if diag["win_rate"] >= 50 else "down"), unsafe_allow_html=True)
        else:
            st.markdown('<div class="hint">완성된 과거 베이스가 없어 승률을 낼 수 없습니다.</div>',
                        unsafe_allow_html=True)

        step_header("BREADTH", "시장 폭 (참고)")
        br = breadth_pct(CTX["uni"])
        if br is not None:
            st.markdown(card("3개월 상승 종목 비율", f'{br:.0f}%',
                             "50% 이상이면 시장 전반이 함께 오르는 중 · "
                             "지수만 오르고 이 값이 낮으면 소수 종목 장세",
                             "up" if br >= 50 else "down"), unsafe_allow_html=True)

        step_header("CHECKLIST", "매수 전 최종 점검", "전부 통과해야 오닐 기준 매수")
        rows = final_checklist(D["m_ok"], D["c_ok"], D["a_ok"], D["n_ok"], D["s_ok"],
                               D["l_ok"], D["i_ok"], D["base_ok"], CTX["binfo"], D["sp"], diag)
        passed = sum(1 for _, ok, _ in rows if ok)
        st.markdown(card("통과 항목", f'{passed} / {len(rows)}',
                         "10개 이상이면 오닐 기준 진입 가능" + bar(passed, len(rows)),
                         "up" if passed >= 10 else ("amb" if passed >= 7 else "down")),
                    unsafe_allow_html=True)
        st.markdown("<br>" + table(["점검 항목", "판정", "확인 위치"],
                                   [[q, verdict(ok, "예", "아니오"), w] for q, ok, w in rows]),
                    unsafe_allow_html=True)

        read_box(
            '오닐 기법은 종목 고르기에 집중되어 있어 <b>실전에서 빠지는 부분</b>이 있습니다. '
            '이 탭은 그 빈틈을 메우는 항목들입니다.<br><br>'
            '<b>① 변동성</b> — 모든 종목에 같은 8% 손절을 적용하면, 변동성 큰 종목은 정상 흔들림에도 '
            '손절됩니다. 손절폭을 넓히는 대신 수량을 줄이는 것이 정답입니다.<br>'
            '<b>② 유동성</b> — 거래대금이 작으면 기관이 못 들어오고, 내 주문도 불리하게 체결됩니다.<br>'
            '<b>③ 실적 발표일</b> — 돌파 직전 실적 발표가 있으면 갭으로 손절선이 무력화됩니다. '
            '오닐도 실적 발표 직전 신규 진입은 피하라고 했습니다.<br>'
            '<b>④ 과거 승률</b> — 같은 종목이라도 돌파가 잘 먹히는 종목과 아닌 종목이 있습니다.<br>'
            '<b>⑤ 시장 폭</b> — 지수는 오르는데 상승 종목 비율이 낮으면, 소수 대형주만 오르는 '
            '장세라 신규 돌파가 잘 안 먹힙니다.', "왜 이 항목들이 필요한가", "oneil")


# ════════════════════════════════════════════════════════════════════════════
# TAB 8 — 사용 가이드
# ════════════════════════════════════════════════════════════════════════════
with TABS[8]:
    st.markdown('<div class="masthead"><h1>사용 가이드</h1><div class="sub">'
                '오닐 기법과 이 앱을 함께 읽는 법</div></div>', unsafe_allow_html=True)

    step_header("BASIC", "오닐 기법이란 무엇인가")
    st.markdown("""
윌리엄 오닐은 40년간 크게 오른 주식 수천 개를 뒤에서부터 되짚어, **오르기 직전에 공통으로 있던 특징**을
7가지로 정리했습니다. 그게 CANSLIM입니다. 중요한 건 이게 예측이 아니라 **관찰의 결과**라는 점입니다.

| 글자 | 뜻 | 한 줄 설명 |
|---|---|---|
| **C** | Current Earnings | 가장 최근 분기 이익이 작년 같은 분기보다 25% 이상 늘었는가 |
| **A** | Annual Earnings | 연간 이익이 3년 연속 늘고 ROE가 17% 이상인가 |
| **N** | New | 신제품·신경영진·신고가 — 뭔가 새로운 것이 있는가 |
| **S** | Supply & Demand | 돌파할 때 거래량이 평소보다 40% 이상 터지는가 |
| **L** | Leader | 전체 종목 중 수익률 상위 20%(RS 80+) 안에 드는가 |
| **I** | Institutional | 기관이 사고 있는가 |
| **M** | Market | 시장 전체가 상승세인가 — **가장 중요** |

오닐이 반복해서 강조한 것은 두 가지입니다.

1. **시장이 조정이면 아무것도 사지 마라.** 조정장에서 산 종목은 4개 중 3개가 실패합니다.
2. **7~8% 손실이면 무조건 팔아라.** 예외는 없습니다. 작은 손실은 회복되지만 큰 손실은 회복되지 않습니다.
   10% 잃으면 11% 벌어야 본전이지만, 50% 잃으면 100%를 벌어야 본전입니다.
""")

    step_header("ORDER", "이 앱을 보는 순서")
    st.markdown("""
매일 아침 이 순서로 3분이면 충분합니다.

**1단계 · 대시보드** — 오늘 매수 적합도가 몇 점인지 봅니다.
35점 미만이면 그날은 아무것도 사지 않습니다. 그것만으로 큰 손실의 대부분을 피할 수 있습니다.

**2단계 · 시장 탭** — 다우·S&P·나스닥 세 지수의 FTD와 분산일, 그리고 공포탐욕지수를 봅니다.
분산일이 6개 이상 쌓였거나 지수가 극단적 탐욕이면 신규 매수 규모부터 줄입니다.

**3단계 · 환율 탭** — 미국 주식을 살 계획이면 여기서 환전 비중을 먼저 정합니다.
환율은 매수 단가의 일부입니다.

**4단계 · 개별종목 탭** — 위에서 통과했을 때만 봅니다. STEP 2 베이스 → STEP 5 RS →
STEP 3 실적(3분기·3년) 순서로 보고, 하나라도 탈락이면 거기서 멈춥니다.
그다음 STEP 8에서 진입가·손절가·수량을 정합니다. 손절가는 **사기 전에** 정하는 것입니다.

**5단계 · 분석보강 탭** — 80% 신뢰구간으로 이 종목의 정상 변동 폭을 확인합니다.
-8% 손절선이 정상 변동 범위 안에 들어 있으면 수량을 줄여야 합니다.
유동성, 실적 발표일, 과거 돌파 승률, 12항목 체크리스트도 여기서 봅니다.

**6단계 · my투자 탭** — 매일 아침 여기부터 보는 게 실전에서는 가장 중요합니다.
보유 종목별 오늘의 전략(손절/익절/보유)이 자동으로 갱신됩니다.

**보조 · 뉴스 탭** — 뉴스로 사고팔지는 않되, 무슨 일이 있었는지는 압니다.
**보조 · 종목스캔 탭** — 조회한 종목이 자동으로 쌓입니다. 한 번에 비교할 때 씁니다.
""")

    step_header("TERMS", "용어 풀이")
    st.markdown("""
- **베이스(Base)** — 주가가 오른 뒤 옆으로 쉬면서 매물을 소화하는 구간. 이 구간이 있어야 다음 상승의
  발판이 생깁니다. 오닐 매수는 베이스 없이는 시작되지 않습니다.
- **피봇(Pivot)** — 베이스를 벗어나는 돌파 기준가. 오닐의 매수는 **이 한 지점**에서만 일어납니다.
  피봇 +5%를 넘기면 사지 않습니다.
- **핸들(Handle)** — 베이스 끝자락의 얕은 눌림. 마지막 약한 손을 털어내는 과정이며,
  이게 있어야 돌파 성공률이 올라갑니다.
- **FTD(Follow-Through Day)** — 시장 조정이 끝났다는 확인 신호. 저점에서 4일 이상 지난 뒤
  지수가 크게 오르며 거래량도 늘어난 날.
- **분산일(Distribution Day)** — 지수가 내렸는데 거래량은 늘어난 날. 기관이 판 흔적입니다.
- **RS Rating** — 전체 종목 중 수익률 순위(1~99). 80이면 상위 20%.
- **베이스 차수** — 상승 과정에서 몇 번째 베이스인가. 1~2차가 안전하고 3차 이상은 실패율이 급증합니다.
- **연장(Extended)** — 피봇에서 5% 넘게 오른 상태. 사면 안 되는 구간입니다.
- **8주 보유 규칙** — 돌파 후 3주 안에 20% 이상 오르면 익절하지 말고 최소 8주 보유.
  진짜 대박 종목은 그렇게 시작합니다.
""")

    step_header("RULES", "자동 판정 규칙 대조표")
    st.markdown("""
| 항목 | 이 앱의 판정 | 오닐 원전 |
|---|---|---|
| FTD | 조정(-4%↓) 저점 후 4일차 이상, 지수 +1.2%↑ & 거래량 증가한 첫날 | 4~7일차, +1.25%↑ |
| 분산일 | 25일 내 종가 -0.2%↓ + 거래량 증가. +5% 상승 시 만료 | 6개 이상이면 상승세 종료 |
| 매수 적합도 | 국면 40 + 분산일 20 + FTD경과 15 + 추세 15 + 당일 10 | 오닐 원전에 없는 자체 지표 |
| 베이스 탐지 | 주봉 지그재그(기본 8% 전환)로 고점→저점→돌파 추출 | 주봉 차트로 판단 |
| 컵 위드 핸들 | 6주 이상 + 핸들 존재 | 7~65주, 깊이 12~33% |
| 플랫 베이스 | 깊이 15% 이내 + 4주 이상 | 5주 이상, 15% 이내 |
| 이중 바닥 | 두 저점이 하단 40% 내 + 중간 반등 45%↑ | 7주 이상 |
| 하이 타이트 플래그 | 직전 60일 +60%↑ 후 깊이 25% 이내·2.5~8주 | 4~8주 100~120% 후 3~5주 |
| 핸들 | 저점 이후 최고점부터의 마지막 눌림 | 깊이 8~12%, 상단 절반, 거래량 건조 |
| 피봇 | 핸들 고점(없으면 좌측 고점) + 호가 1틱 | 핸들 고점 +$0.10 |
| 매수 구간 | 피봇 ~ 피봇 +5% | +5% 초과는 추격 금지 |
| 손절 | 진입가 -8%와 핸들/베이스 저점 중 타이트한 쪽 | 7~8%, 예외 없음 |
| 익절 | +20~25%, 3주 내 20%↑면 8주 보유 | 동일 |
| 고점 신호 | 클라이맥스 급등·200일선 이격·최대상승일·최대거래량 음봉·소진갭·레일로드 | 동일 개념 |
| RS Rating | 0.4×3M + 0.2×(6M·9M·12M) 가중수익률의 백분위 | 80↑, 돌파 시 90↑ |
| EPS·SMR·Composite | 성장률/마진을 곡선 환산한 **근사값** | IBD 자체 산출 |
| 실적 판정 | 최근 3분기 각각 +25% 충족 개수 · 최근 3년 이익 증가 개수 | 3분기 연속 25%↑, 3년 연속 증가 |
| 80% 신뢰구간 | 최근 252일 로그수익률 σ × √기간 × 1.2816 (이력 10~90% 분위수 병기) | 오닐 원전에 없는 보조 지표 |
| 공포탐욕지수 | 모멘텀·변동성·시장폭·주가강도·안전자산·정크본드 평균 (미국은 CNN 공식값 병기) | 오닐 원전에 없는 보조 지표 |
| R 배수 | 수익률 ÷ 8% (1R = 손절폭) | 손실 1R, 이익 3R 이상 |
""")

    step_header("MISTAKE", "가장 흔한 실수 5가지")
    st.markdown("""
1. **시장을 안 보고 종목만 본다** — 오닐이 가장 강조한 실수입니다. 종목이 아무리 좋아도
   시장이 조정이면 실패합니다.
2. **피봇을 넘긴 뒤 뒤늦게 산다** — 진입가가 높아진 만큼 손절선이 베이스 안으로 들어와
   정상적인 흔들림에도 손절됩니다.
3. **손절을 미룬다** — "조금만 더 기다리면 오를 것"이 가장 비싼 문장입니다.
4. **오른 종목을 팔고 내린 종목을 들고 간다** — 오닐은 정반대로 하라고 했습니다.
   손실은 잘라내고 이익은 굴려야 합니다.
5. **너무 많은 종목을 산다** — 오닐은 4~8종목을 권했습니다. 종목이 많으면 관리가 안 됩니다.
""")

    st.markdown('<div class="quote">이 앱의 모든 판정은 오닐 기법의 계량 가능한 규칙을 자동화한 것입니다. '
                'EPS Rating·SMR·Composite·매수 적합도는 IBD 원본이 아닌 자체 환산 근사값이며, '
                '뉴스 주제·논조는 제목 키워드 기반 자동 분류입니다. 실적 수치는 공시 원문(DART·SEC) '
                '대조를 권합니다. 투자 판단과 책임은 이용자 본인에게 있습니다.</div>',
                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 7 — my투자
# ════════════════════════════════════════════════════════════════════════════
with TABS[7]:
    st.markdown('<div class="masthead"><h1>my투자</h1><div class="sub">'
                '보유 종목 오늘의 전략 · 누적 수익률 관리</div></div>', unsafe_allow_html=True)
    port = load_portfolio()

    with st.expander("보유 종목 추가", expanded=len(port["open"]) == 0):
        ic = st.columns([1.1, 1, 1, 1, 1.4])
        in_tk = ic[0].text_input("종목코드/티커", value=TK, key="p_tk")
        in_dt = ic[1].date_input("매수일", value=datetime.today(), key="p_dt")
        in_px = ic[2].number_input("매수가", min_value=0.0, value=0.0, format="%.2f", key="p_px")
        in_qty = ic[3].number_input("수량", min_value=0, value=0, step=1, key="p_qty")
        in_memo = ic[4].text_input("메모 (선택)", value="", key="p_memo")
        if st.button("포트폴리오에 추가", type="primary"):
            if in_tk.strip() and in_px > 0:
                port["open"].append({"id": f'{in_tk.strip().upper()}-{datetime.now():%Y%m%d%H%M%S}',
                                     "ticker": in_tk.strip().upper(), "date": str(in_dt),
                                     "price": float(in_px), "qty": int(in_qty),
                                     "memo": in_memo.strip()})
                save_portfolio(port)
                st.success(f'{in_tk.strip().upper()} 추가 완료')
            else:
                st.warning("종목과 매수가를 입력하세요.")

    if not port["open"] and not port["closed"]:
        st.info("보유 종목을 추가하면 매일 이 화면에서 종목별 오늘의 전략과 누적 수익률을 확인할 수 있습니다.")
    else:
        revs = []
        if port["open"]:
            with st.spinner("보유 종목 시세 갱신 중…"):
                for h in port["open"]:
                    r = position_review(h, zig_pct)
                    r["h"] = h
                    revs.append(r)
        ok_revs = [r for r in revs if r["ok"]]

        if ok_revs:
            tot_cost = sum(r["cost"] for r in ok_revs)
            tot_val = sum(r["value"] for r in ok_revs)
            has_qty = tot_cost > 0
            avg_ret = (float(np.mean([r["ret"] for r in ok_revs])) if not has_qty
                       else (tot_val / tot_cost - 1) * 100)
            winners = sum(1 for r in ok_revs if r["ret"] > 0)
            mk0 = ok_revs[0]["market"]

            step_header("PORTFOLIO", "누적 현황")
            pc = st.columns(4)
            pc[0].markdown(bigcard("총 평가손익",
                                   (f'{fmt(tot_val - tot_cost, mk0)}{unit(mk0)}' if has_qty
                                    else f'{avg_ret:+.1f}%'),
                                   (f'투자 {fmt(tot_cost, mk0)} → 평가 {fmt(tot_val, mk0)}'
                                    if has_qty else "수량 미입력 — 단순 평균 수익률"),
                                   "up" if avg_ret >= 0 else "down"), unsafe_allow_html=True)
            pc[1].markdown(bigcard("수익률", f'{avg_ret:+.1f}%',
                                   ("금액 가중" if has_qty else "종목 단순 평균")
                                   + bar(min(100, max(0, avg_ret + 50)),
                                         color=P_UP if avg_ret >= 0 else P_DOWN),
                                   "up" if avg_ret >= 0 else "down"), unsafe_allow_html=True)
            pc[2].markdown(bigcard("보유 종목 수", f'{len(ok_revs)}',
                                   ("오닐 권장 4~8종목" if 4 <= len(ok_revs) <= 8 else
                                    "너무 분산되면 관리가 안 됩니다" if len(ok_revs) > 8 else
                                    "집중도가 높습니다 — 한 종목 실패의 타격이 큽니다"),
                                   "up" if 4 <= len(ok_revs) <= 8 else "amb"), unsafe_allow_html=True)
            pc[3].markdown(bigcard("승률", f'{winners}/{len(ok_revs)}',
                                   "평가익 종목 비율 · 오닐은 손실을 짧게 끊어 "
                                   "승률 50%로도 수익을 냈습니다"), unsafe_allow_html=True)

            step_header("TODAY", "종목별 오늘의 전략")
            rows = []
            for r in sorted(ok_revs, key=lambda x: {"fail": 0, "warn": 1, "idle": 2, "pass": 3}[x["kind"]]):
                rows.append([
                    f'<b>{r["name"]}</b><br><span class="mono mut" style="font-size:.7rem">'
                    f'{r["ticker"]}</span>',
                    f'<span class="mono">{fmt(r["buy"], r["market"])}</span><br>'
                    f'<span class="mono mut" style="font-size:.7rem">{r["date"]:%Y-%m-%d}</span>',
                    f'<span class="mono">{fmt(r["price"], r["market"])}</span>',
                    f'<span class="mono {"up" if r["ret"]>=0 else "down"}">{r["ret"]:+.1f}%</span><br>'
                    f'<span class="mono mut" style="font-size:.7rem">R {r["r_mult"]:+.1f}</span>',
                    f'<span class="mono">{fmt(r["stop"], r["market"])}</span><br>'
                    f'<span class="mono mut" style="font-size:.7rem">{fmt(r["t1"], r["market"])} 목표</span>',
                    f'<span class="mono">{r["sp"]["score"]}</span>',
                    tag(r["act"], r["kind"]),
                    f'<span class="m">{r["why"]}</span>'])
            st.markdown(table(["종목", "매수가/일", "현재가", "수익률", "손절/목표",
                               "매도압력", "오늘의 전략", "근거"], rows), unsafe_allow_html=True)

            urgent = [r for r in ok_revs if r["kind"] == "fail"]
            if urgent:
                st.markdown('<br>' + tag(f'즉시 조치 필요 {len(urgent)}건', "fail")
                            + '<span class="hint"> — '
                            + " / ".join(f'{r["name"]} {r["act"]}' for r in urgent)
                            + '</span>', unsafe_allow_html=True)

            for r in ok_revs:
                with st.expander(f'{r["name"]} 상세 — {r["act"]} ({r["ret"]:+.1f}%)'):
                    dc = st.columns(4)
                    dc[0].markdown(card("보유 기간", f'{r["held"]}일',
                                        f'{r["date"]:%Y-%m-%d} 매수'), unsafe_allow_html=True)
                    dc[1].markdown(card("매수 후 최고", f'{r["peak_ret"]:+.1f}%',
                                        f'고점 대비 현재 {r["dd_from_peak"]:+.1f}%',
                                        "down" if r["dd_from_peak"] <= -10 else "up"),
                                   unsafe_allow_html=True)
                    dc[2].markdown(card("이동평균", "50일선 " + ("아래" if r["below50"] else "위"),
                                        f'50일 {fmt(r["ma50"], r["market"])} · '
                                        f'200일 {fmt(r["ma200"], r["market"])}',
                                        "down" if r["below50"] else "up"), unsafe_allow_html=True)
                    dc[3].markdown(card("R 배수", f'{r["r_mult"]:+.2f}R',
                                        "1R = 8% · 손실은 -1R에서 끊고 이익은 3R 이상 노립니다",
                                        "up" if r["r_mult"] > 0 else "down"), unsafe_allow_html=True)
                    fired = [t for t in r["top"] if t[1]]
                    if fired:
                        st.markdown(table(["발생한 고점 신호", "측정", "의미"],
                                          [[t[0], f'<span class="mono">{t[2]}</span>',
                                            f'<span class="m">{t[4]}</span>'] for t in fired]),
                                    unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="hint">발생한 고점 신호가 없습니다.</div>',
                                    unsafe_allow_html=True)
                    if r["binfo"]:
                        st.markdown(f'<div class="ev">현재 베이스 · <b>{r["binfo"]["type"]}</b> · '
                                    f'{r["binfo"]["stage"]} · 피봇 '
                                    f'{fmt(r["binfo"]["pivot"], r["market"])}</div>',
                                    unsafe_allow_html=True)
                    ec = st.columns([1, 1, 3])
                    if ec[0].button("청산 기록", key=f'close_{r["h"]["id"]}'):
                        h = r["h"]
                        port["open"] = [x for x in port["open"] if x["id"] != h["id"]]
                        port["closed"].append({**h, "sell_date": str(datetime.today().date()),
                                               "sell_price": r["price"], "ret": r["ret"]})
                        save_portfolio(port)
                        st.success(f'{r["name"]} 청산 기록 완료')
                    if ec[1].button("삭제", key=f'del_{r["h"]["id"]}'):
                        port["open"] = [x for x in port["open"] if x["id"] != r["h"]["id"]]
                        save_portfolio(port)
                        st.info("삭제했습니다")

            read_box(
                '오닐의 보유 관리는 세 가지 규칙으로 끝납니다.<br><br>'
                '<b>① -7~8%면 무조건 손절</b> — 이유를 찾지 마세요. 규칙이 판단보다 낫습니다.<br>'
                '<b>② +20~25%면 익절</b> — 단, 돌파 후 3주 안에 20% 이상 올랐다면 8주는 들고 갑니다. '
                '진짜 대박 종목이 그렇게 시작하기 때문입니다.<br>'
                '<b>③ 오른 종목을 팔고 내린 종목을 들고 있지 마세요</b> — 대부분의 투자자가 정반대로 합니다.<br><br>'
                '위 표의 <b>R 배수</b>는 손실 한 단위(8%)를 1R로 본 수익 배수입니다. '
                '오닐 방식은 -1R에서 끊고 +3R 이상을 노리는 게임이라, 승률이 40%여도 수익이 납니다.',
                "보유 종목을 다루는 법", "oneil")

        failed = [r for r in revs if not r["ok"]]
        if failed:
            st.markdown('<div class="hint">시세를 못 불러온 종목: '
                        + ", ".join(r["ticker"] for r in failed) + '</div>', unsafe_allow_html=True)

        if port["closed"]:
            step_header("CLOSED", "청산 이력 · 실현 손익")
            cl = pd.DataFrame(port["closed"])
            rets_ = _clean(cl["ret"].tolist()) if "ret" in cl.columns else []
            if rets_:
                wins = [x for x in rets_ if x > 0]
                loss = [x for x in rets_ if x <= 0]
                cc2 = st.columns(4)
                cc2[0].markdown(card("청산 종목", f'{len(rets_)}건', "누적 기록"), unsafe_allow_html=True)
                cc2[1].markdown(card("승률", f'{len(wins)/len(rets_)*100:.0f}%',
                                     f'{len(wins)}승 {len(loss)}패',
                                     "up" if len(wins) >= len(loss) else "mut"), unsafe_allow_html=True)
                cc2[2].markdown(card("평균 수익 / 평균 손실",
                                     f'{np.mean(wins) if wins else 0:+.1f}% / '
                                     f'{np.mean(loss) if loss else 0:+.1f}%',
                                     "오닐: 평균 수익이 평균 손실의 3배 이상이어야 함",
                                     "up" if (wins and loss and np.mean(wins) >= abs(np.mean(loss)) * 3)
                                     else "mut"), unsafe_allow_html=True)
                cc2[3].markdown(card("누적 평균 수익률", f'{np.mean(rets_):+.1f}%',
                                     "청산 종목 단순 평균",
                                     "up" if np.mean(rets_) >= 0 else "down"), unsafe_allow_html=True)
            need = ["ticker", "date", "price", "sell_date", "sell_price", "ret"]
            for cnm in need:
                if cnm not in cl.columns:
                    cl[cnm] = None
            show = cl[need].copy()
            show.columns = ["종목", "매수일", "매수가", "청산일", "청산가", "수익률(%)"]
            show["수익률(%)"] = pd.to_numeric(show["수익률(%)"], errors="coerce").round(1)
            st.dataframe(show.iloc[::-1], use_container_width=True, hide_index=True)
            if st.button("청산 이력 전체 삭제"):
                port["closed"] = []
                save_portfolio(port)
                st.info("청산 이력을 비웠습니다")

    st.markdown('<div class="quote">입력한 보유 내역은 이 앱 서버의 portfolio.json에 저장됩니다. '
                '재배포하면 초기화될 수 있으니 중요한 기록은 따로 백업하세요. '
                '수익률은 종가 기준이며 수수료·세금·환율 변동은 반영되지 않습니다.</div>',
                unsafe_allow_html=True)
