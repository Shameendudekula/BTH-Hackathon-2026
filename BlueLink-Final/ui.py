"""Presentation helpers; no external assets or unsafe user HTML."""
from html import escape
import streamlit as st

CSS = '''<style>
.block-container {max-width: 1440px; padding: 2rem 3rem 4rem;}
[data-testid="stSidebar"] {border-right:1px solid #d5e2ed;background:#102b4d;}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding-top:1rem;}
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stRadio"] p {color:#d8e7f5 !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:6px 8px;border-radius:8px;}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background:#244e75;}
[data-testid="stSidebar"] hr {border-color:#395775;}
h1,h2,h3 {letter-spacing:-.035em;}
[data-testid="stMetric"] {border:1px solid #dce5ef;background:#fff;padding:18px 20px;border-radius:16px;box-shadow:0 3px 12px #142c5010;}
[data-testid="stMetricLabel"] {color:#536579;}
[data-testid="stMetricValue"] {color:#102e52;font-weight:700;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px;background:white;box-shadow:0 3px 12px #142c5008;}
.stButton button,.stLinkButton a {border-radius:9px; font-weight:600;}
.bl-brand {font-size:24px;font-weight:800;letter-spacing:-1px;color:#ffffff;}
.bl-brand span {color:#63e0d9;}
.bl-kicker {font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#54748e;margin:0 0 8px;}
.bl-hero {background:linear-gradient(115deg,#102b50,#164b73 65%,#087e87);border-radius:22px;padding:32px 36px;color:white;margin-bottom:18px;position:relative;overflow:hidden;}
.bl-hero:after {content:'';position:absolute;width:280px;height:280px;border:1px solid #ffffff24;border-radius:50%;right:-65px;top:-100px;box-shadow:0 0 0 35px #ffffff09,0 0 0 70px #ffffff09;pointer-events:none;}
.bl-hero h1 {font-size:clamp(25px,3vw,38px);line-height:1.2;color:white;margin:12px 0;max-width:75%;}
.bl-hero p {color:#d4e5f4;font-size:15px;max-width:74%;margin:0;}
.bl-hero .bl-kicker {color:#9ee5e8;}
.bl-chip {display:inline-block;background:#e6f3f5;color:#12646e;border-radius:999px;padding:5px 11px;font-size:12px;font-weight:650;margin:0 5px 5px 0;}
.bl-overline {font-size:12px;font-weight:700;color:#087e87;letter-spacing:1px;text-transform:uppercase;}
.bl-match {font-size:13px;font-weight:700;color:#12646e;background:#e6f3f5;border-radius:9px;padding:9px 12px;margin:8px 0;}
@media(max-width:700px){.block-container{padding:1rem 1rem 3rem}.bl-hero{padding:24px}.bl-hero h1,.bl-hero p{max-width:100%}}
</style>'''

def hero(kicker,title,description):
    st.markdown(f'<div class="bl-hero"><div class="bl-kicker">{escape(kicker)}</div><h1>{escape(title)}</h1><p>{escape(description)}</p></div>',unsafe_allow_html=True)

def chips(values):
    st.markdown(''.join(f'<span class="bl-chip">{escape(str(v))}</span>' for v in values),unsafe_allow_html=True)

def match_label(score):
    st.markdown(f'<div class="bl-match">{int(score)} match points · Explainable relevance</div>',unsafe_allow_html=True)
