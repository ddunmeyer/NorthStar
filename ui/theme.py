"""North Star look and feel: palette, artwork and the page stylesheet.

All artwork is original vector drawn here (the compass star and the aurora
banner), so the app ships no stock imagery.
"""
from __future__ import annotations

from pathlib import Path

from ui.artwork import banner_data_uri

MIDNIGHT = "#0C1626"
PANEL = "#15243A"
OCEAN = "#2F6C8A"
AURORA = "#9DE5F4"
SILVER = "#B6CFEB"
ICE = "#F3F7FC"
LINE = "#24364F"

ASSETS = Path(__file__).resolve().parent / "assets"
STAR_AVATAR = str(ASSETS / "star.svg")

STAR_PATH = "M12 1.5 13.9 10.1 22.5 12 13.9 13.9 12 22.5 10.1 13.9 1.5 12 10.1 10.1Z"


def star_svg(size: int = 28) -> str:
    """The four-point compass star used for the wordmark and assistant avatar."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true">'
        f'<path d="{STAR_PATH}" fill="{AURORA}"/>'
        f'<path d="M12 7.2 13 11 16.8 12 13 13 12 16.8 11 13 7.2 12 11 11Z" fill="{ICE}"/></svg>'
    )


def css(dim_banner: bool = False) -> str:
    """The page stylesheet. dim_banner fades the artwork on pages where text sits over it."""
    veil = "linear-gradient(rgba(12,22,38,.72), var(--ns-midnight) 330px), " if dim_banner else ""
    return f"""
<style>
:root {{
  --ns-midnight:{MIDNIGHT}; --ns-panel:{PANEL}; --ns-ocean:{OCEAN}; --ns-aurora:{AURORA};
  --ns-silver:{SILVER}; --ns-ice:{ICE}; --ns-line:{LINE}; --ns-raise:#1B2E49;
  --ns-ok:#4ADE80; --ns-warn:#F6C177; --ns-bad:#F58C8C;
}}
html, body, [data-testid="stAppViewContainer"] {{
  font-family:"Segoe UI Variable Text","Segoe UI",Inter,system-ui,-apple-system,"Helvetica Neue",sans-serif;
}}
[data-testid="stAppViewContainer"] {{ background:var(--ns-midnight); }}
[data-testid="stMain"] {{
  background:{veil}url("{banner_data_uri()}") top center / max(100%, 1480px) auto no-repeat, var(--ns-midnight);
}}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stHeaderActionElements"] {{ display:none; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none; }}
[data-testid="stMainBlockContainer"] {{ padding:6.2rem 2.4rem 1rem; max-width:1500px; }}
h1,h2,h3 {{ letter-spacing:-.02em; color:var(--ns-ice); }}
a {{ color:var(--ns-aurora); }}
:focus-visible:not(input):not(textarea) {{ outline:2px solid var(--ns-aurora) !important; outline-offset:2px; }}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {{
  background:linear-gradient(180deg,#0E1B2E 0%,#0A1524 100%); border-right:1px solid var(--ns-line);
  width:328px !important; min-width:328px !important;
}}
[data-testid="stSidebarHeader"] {{ display:none; }}
[data-testid="stSidebarContent"] {{ padding:1.6rem 1rem 1rem; }}
[data-testid="stSidebarUserContent"] {{ padding:0; }}
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {{ min-height:calc(100vh - 3.4rem); }}
[data-testid="stSidebar"] .st-key-signout {{ margin-top:auto; }}
.ns-brand {{ display:flex; align-items:center; gap:14px; padding:0 .5rem 1.6rem; }}
.ns-emblem {{
  width:54px; height:54px; border-radius:12px; display:grid; place-items:center; flex:none;
  background:radial-gradient(circle at 50% 40%,#1D3554,#0F1F35); border:1px solid #3A5677;
  box-shadow:0 0 22px rgba(157,229,244,.16);
}}
.ns-wordmark {{ white-space:nowrap; font-size:1.42rem; font-weight:700; letter-spacing:.14em; color:var(--ns-ice); line-height:1.1; }}
.ns-tagline {{ font-size:.86rem; color:var(--ns-silver); margin-top:3px; }}
.ns-profile {{ display:flex; align-items:center; gap:14px; padding:.4rem .5rem 1.5rem; }}
.ns-avatar {{
  width:54px; height:54px; border-radius:50%; background:#1D3554; display:grid; place-items:center; flex:none;
  color:var(--ns-aurora); font-weight:600; font-size:1.15rem; border:1px solid #2F4B6C;
}}
.ns-profile-name {{ font-size:1.12rem; font-weight:600; color:var(--ns-ice); }}
.ns-profile-meta {{ font-size:.9rem; color:var(--ns-silver); }}
[data-testid="stSidebar"] .stButton button {{
  justify-content:flex-start; gap:14px; width:100%; padding:.85rem 1rem; border-radius:10px;
  background:transparent; border:1px solid transparent; color:var(--ns-silver); font-size:1.04rem;
  transition:background .15s, color .15s;
}}
[data-testid="stSidebar"] .stButton button:hover {{ background:rgba(157,229,244,.06); color:var(--ns-ice); }}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
  background:linear-gradient(90deg,#1B3251,#162840); color:var(--ns-ice);
  box-shadow:inset 3px 0 0 var(--ns-aurora);
}}
[data-testid="stSidebar"] .stButton button [data-testid="stIconMaterial"] {{ font-size:1.5rem; color:var(--ns-aurora); }}
.st-key-signout button {{ border:1px solid var(--ns-line) !important; }}
.ns-side-note {{ font-size:.76rem; color:#7F96B5; padding:.9rem .6rem 0; line-height:1.5; }}
.ns-dot {{ display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:7px; background:var(--ns-ok); }}
.ns-dot.warn {{ background:var(--ns-warn); }}

[data-testid="stSidebar"] .stButton button > div, [class*="st-key-quick_"] button > div {{ width:100%; justify-content:flex-start; }}
[data-testid="stSidebar"] .stButton button > div > span, [class*="st-key-quick_"] button > div > span {{ gap:14px; }}
[data-testid="stSidebar"] .stButton button p, [class*="st-key-quick_"] button p {{ font-size:1.04rem; }}

/* ---------- hero ---------- */
.ns-hero h1 {{ font-size:2.75rem; font-weight:700; margin:0; padding:0; text-shadow:0 2px 24px rgba(5,11,23,.9); }}
.ns-hero p {{ font-size:1.42rem; color:var(--ns-silver); margin:.1rem 0 1.5rem; text-shadow:0 2px 18px rgba(5,11,23,.9); }}
.ns-page-title {{ font-size:2.1rem; font-weight:700; margin:0; }}
.ns-page-sub {{ color:var(--ns-silver); font-size:1.08rem; margin:.15rem 0 1.6rem; }}
.ns-section {{ font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; color:var(--ns-silver); margin:1.5rem 0 .7rem; }}

/* ---------- stat tiles (a transparent button covers each tile) ---------- */
.ns-tile {{
  display:flex; align-items:center; gap:18px; padding:1.25rem 1.3rem; border-radius:14px; min-height:112px; overflow:hidden; min-width:0;
  background:linear-gradient(180deg,rgba(24,41,66,.92),rgba(16,29,48,.92)); border:1px solid var(--ns-line);
  backdrop-filter:blur(6px); transition:border-color .15s, transform .15s;
}}
.ns-tile-icon {{
  width:60px; height:60px; border-radius:50%; background:#213A5C; display:grid; place-items:center; flex:none;
  color:var(--ns-aurora);
}}
.ns-tile-label {{ color:var(--ns-silver); font-size:1.08rem; white-space:nowrap; }}
.ns-tile-value {{ color:var(--ns-ice); font-size:clamp(1.8rem,2.7vw,2.5rem); font-weight:700; line-height:1.1; letter-spacing:-.02em; white-space:nowrap; }}
.ns-tile-value small {{ font-size:1.05rem; font-weight:400; color:var(--ns-silver); margin-left:.4rem; letter-spacing:0; }}
.ns-tile-foot {{ color:#8FA6C4; font-size:.82rem; margin-top:2px; white-space:nowrap; }}
.ns-chevron {{ margin-left:auto; color:var(--ns-silver); font-size:1.5rem; }}
[class*="st-key-tile_"] {{ position:relative; }}
[class*="st-key-tile_"] [data-testid="stElementContainer"]:has(.stButton) {{ position:absolute; inset:0; z-index:2; }}
[class*="st-key-tile_"] .stButton, [class*="st-key-tile_"] .stButton button {{ width:100%; height:100%; }}
[class*="st-key-tile_"] .stButton button {{ opacity:0; cursor:pointer; }}
[class*="st-key-tile_"]:hover .ns-tile {{ border-color:#4C7397; transform:translateY(-1px); }}
[class*="st-key-tile_"]:has(button:focus-visible) .ns-tile {{ outline:2px solid var(--ns-aurora); outline-offset:2px; }}

/* ---------- quick prompts ---------- */
[class*="st-key-quick_"] {{ margin-top:.35rem; }}
[class*="st-key-quick_"] button {{
  width:100%; justify-content:flex-start; gap:12px; padding:1.05rem 1.1rem; border-radius:12px; min-height:66px;
  background:rgba(19,34,55,.92); border:1px solid var(--ns-line); color:var(--ns-ice); font-size:1.02rem;
}}
[class*="st-key-quick_"] button:hover {{ border-color:#4C7397; background:#1A2F4B; color:var(--ns-ice); }}
[class*="st-key-quick_"] button [data-testid="stIconMaterial"] {{ color:var(--ns-aurora); font-size:1.6rem; }}
[class*="st-key-quick_"] button::after {{ content:"\\203A"; margin-left:auto; color:var(--ns-silver); font-size:1.4rem; }}

/* ---------- chat ---------- */
.st-key-chat_panel {{
  background:rgba(14,26,44,.82); border:1px solid var(--ns-line); border-radius:16px; padding:.6rem 1rem 1rem;
}}
.st-key-chat_scroll {{ border:none !important; }}
/* the chat fills what is left of the window, so the dashboard fits one screen */
[data-testid="stLayoutWrapper"]:has(> .st-key-chat_scroll) {{ height:calc(100vh - 632px) !important; flex:0 0 auto !important; min-height:300px; }}
.ns-user {{ display:flex; justify-content:flex-end; align-items:flex-start; gap:14px; margin:.3rem 0 .2rem; }}
.ns-user-bubble {{
  background:#1C3252; border:1px solid #2F4B6C; color:var(--ns-ice); padding:.7rem 1.15rem;
  border-radius:14px 14px 4px 14px; font-size:1.06rem; max-width:72%; white-space:pre-wrap;
}}
.ns-user-avatar {{
  width:42px; height:42px; border-radius:50%; background:#213A5C; display:grid; place-items:center; flex:none;
  color:var(--ns-aurora);
}}
.ns-time {{ font-size:.78rem; color:#8FA6C4; }}
.ns-user-time {{ text-align:right; padding-right:58px; margin-bottom:.5rem; }}
[data-testid="stChatMessage"] {{ background:transparent; padding:.2rem 0; gap:16px; align-items:flex-start; }}
[data-testid="stChatMessage"] > :first-child {{
  width:50px; height:50px; border-radius:10px; background:radial-gradient(circle at 50% 40%,#1D3554,#0F1F35);
  border:1px solid #3A5677; padding:9px; flex:none;
}}
[data-testid="stChatMessageContent"] {{
  background:linear-gradient(180deg,#182942,#14233A); border:1px solid var(--ns-line);
  border-radius:4px 14px 14px 14px; padding:1rem 1.3rem 1.05rem; max-width:860px; flex:0 1 auto;
  margin-left:0; margin-right:auto;  /* sit next to the avatar; the default centres it on wide screens */
}}
[data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{ font-size:1.06rem; line-height:1.6; }}
.ns-from {{ font-size:.8rem; letter-spacing:.12em; color:var(--ns-silver); margin-bottom:.35rem; }}
.ns-working {{ color:var(--ns-silver); font-size:1rem; display:flex; align-items:center; gap:10px; }}
.ns-pulse {{ width:9px; height:9px; border-radius:50%; background:var(--ns-aurora); animation:ns-pulse 1.1s ease-in-out infinite; }}
@keyframes ns-pulse {{ 0%,100% {{ opacity:.25; transform:scale(.8); }} 50% {{ opacity:1; transform:scale(1.15); }} }}
@media (prefers-reduced-motion: reduce) {{ .ns-pulse {{ animation:none; }} .ns-tile {{ transition:none; }} }}
.ns-sources {{ display:flex; flex-direction:column; gap:8px; margin-top:.8rem; }}
.ns-source {{
  display:flex; align-items:center; gap:12px; padding:.6rem .9rem; border-radius:9px;
  background:#1B3150; border:1px solid #2F4B6C; color:var(--ns-aurora); font-size:.96rem;
}}
.ns-source small {{ color:var(--ns-silver); margin-left:auto; }}
.ns-activity {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; padding:.1rem 0 .7rem 66px; font-size:.86rem; color:var(--ns-silver); }}
.ns-check {{ width:20px; height:20px; border-radius:50%; background:var(--ns-ok); color:#06251A; display:grid; place-items:center; font-size:.78rem; font-weight:700; }}
.ns-check.bad {{ background:var(--ns-bad); color:#3A0D0D; }}
.ns-step {{ padding:.12rem .6rem; border-radius:999px; background:#16283F; border:1px solid var(--ns-line); color:var(--ns-silver); }}
.ns-activity .ns-time {{ margin-left:auto; }}
[data-testid="stChatInput"] {{ background:#132238; border:1px solid var(--ns-line); border-radius:14px; }}
[data-testid="stChatInput"] textarea {{ font-size:1.05rem; }}
[data-testid="stChatInputSubmitButton"] {{ background:var(--ns-aurora) !important; color:#06202B !important; border-radius:50% !important; }}
.ns-empty {{ text-align:center; padding:3.2rem 1rem 2rem; color:var(--ns-silver); }}
.ns-empty h3 {{ margin:.7rem 0 .2rem; font-size:1.35rem; }}

/* ---------- cards, pills, rows ---------- */
.ns-card {{ background:linear-gradient(180deg,#182942,#14233A); border:1px solid var(--ns-line); border-radius:14px; padding:1.1rem 1.3rem; }}
.ns-card h4 {{ margin:0 0 .15rem; font-size:1.1rem; color:var(--ns-ice); }}
.ns-muted {{ color:var(--ns-silver); font-size:.92rem; }}
.ns-row {{
  display:grid; grid-template-columns:110px minmax(0,1fr) auto; gap:6px 18px; align-items:center;
  padding:.95rem 1.2rem; border:1px solid var(--ns-line); border-radius:12px; background:#132238; margin-bottom:.6rem;
}}
.ns-key {{ font-family:"Cascadia Code",Consolas,ui-monospace,monospace; color:var(--ns-aurora); font-size:.95rem; }}
.ns-row-title {{ color:var(--ns-ice); font-size:1.03rem; }}
.ns-row-meta {{ color:var(--ns-silver); font-size:.88rem; margin-top:2px; }}
.ns-pill {{ display:inline-flex; align-items:center; gap:7px; padding:.2rem .7rem; border-radius:999px; font-size:.84rem;
  border:1px solid var(--ns-line); background:#16283F; color:var(--ns-silver); white-space:nowrap; }}
.ns-pill::before {{ content:""; width:7px; height:7px; border-radius:50%; background:currentColor; }}
.ns-pill.ok {{ color:var(--ns-ok); }} .ns-pill.warn {{ color:var(--ns-warn); }}
.ns-pill.info {{ color:var(--ns-aurora); }} .ns-pill.bad {{ color:var(--ns-bad); }}
.ns-draft {{ border:1px dashed #4C7397; border-radius:12px; padding:1rem 1.2rem; background:#12233A; margin:.2rem 0 .6rem 66px; max-width:800px; }}
.ns-draft-head {{ display:flex; align-items:center; gap:10px; margin-bottom:.6rem; color:var(--ns-ice); font-weight:600; }}
.ns-draft dl {{ display:grid; grid-template-columns:minmax(110px,190px) minmax(0,1fr); gap:.3rem 1rem; margin:0; }}
.ns-draft dt {{ color:var(--ns-silver); font-size:.9rem; }} .ns-draft dd {{ margin:0; color:var(--ns-ice); font-size:.96rem; }}
[class*="st-key-draftbar_"] {{ padding-left:66px; max-width:866px; }}
[data-testid="stExpander"] {{ border:1px solid var(--ns-line); border-radius:12px; background:#132238; }}
.st-key-chat_scroll [data-testid="stExpander"] {{ margin:0 0 .7rem 66px; max-width:800px; }}
.ns-handoff {{ display:grid; grid-template-columns:auto auto 1fr; gap:10px; align-items:baseline; padding:.3rem 0; font-size:.94rem; color:var(--ns-silver); }}
.ns-handoff b {{ color:var(--ns-ice); font-weight:600; white-space:nowrap; }}
.ns-foot {{ text-align:right; color:#7F96B5; font-size:.8rem; padding:.9rem .2rem 0; }}

/* ---------- narrower windows ---------- */
@media (max-width: 1150px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left:1.2rem; padding-right:1.2rem; }}
  .ns-tile-icon, .ns-chevron {{ display:none; }}
  .ns-tile-foot {{ display:none; }}
  .ns-row {{ grid-template-columns:minmax(0,1fr); }}
  .ns-draft, .ns-activity, [class*="st-key-draftbar_"] {{ margin-left:0; padding-left:0; }}
  .ns-draft {{ padding-left:1rem; }}
  .ns-hero h1 {{ font-size:2.1rem; }} .ns-hero p {{ font-size:1.15rem; }}
  .ns-user-bubble {{ max-width:88%; }}
  .st-key-chat_scroll [data-testid="stExpander"] {{ margin-left:0; }}
}}

/* ---------- entry screen ---------- */
/* The wordmark sits in the open sky, top left; the heading and form start below the shoreline. */
.ns-entry-brand {{ position:fixed; top:1.7rem; left:2.2rem; display:flex; align-items:center; gap:16px; z-index:5; }}
.ns-entry {{ margin-top:calc(max(17.6vw, 262px) - 9rem); }}
.ns-entry h1 {{ text-align:center; font-size:3rem; margin:0; text-shadow:0 2px 26px rgba(5,11,23,.95); }}
.ns-entry p {{ text-align:center; color:var(--ns-silver); font-size:1.15rem; margin:.4rem 0 1.4rem; }}
[data-testid="stForm"] {{ background:rgba(16,29,48,.88); border:1px solid var(--ns-line); border-radius:16px; padding:1.6rem 1.6rem 1.3rem; backdrop-filter:blur(8px); }}
[data-testid="stForm"] input {{ font-size:1.08rem; padding:.8rem .9rem; }}
[data-testid="stFormSubmitButton"] button {{
  background:var(--ns-aurora); color:#06202B; border:none; font-weight:600; font-size:1.05rem; padding:.75rem; border-radius:10px;
}}
[data-testid="stFormSubmitButton"] button:hover {{ background:#C3F1FA; color:#06202B; }}

/* ---------- phones: no sidebar, a tab bar pinned to the bottom ---------- */
.ns-mobile-brand {{ display:none; align-items:center; gap:10px; }}
[data-testid="stElementContainer"]:has(.ns-chatting) {{ display:none; }}
[data-testid="stElementContainer"]:has(.ns-mobile-brand),
[data-testid="stLayoutWrapper"]:has(> .st-key-mobile_nav), .st-key-mobile_nav {{ display:none; }}
@media (max-width: 768px) {{
  [data-testid="stSidebar"], [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] {{ display:none !important; }}
  [data-testid="stHeader"] {{ display:none; }}
  [data-testid="stMainBlockContainer"] {{ padding:1rem .85rem 6.4rem; }}
  [data-testid="stMain"] {{ background-position:top right 38%; }}
  /* a veil keeps the heading readable where it sits over bright snow */
  [data-testid="stMain"]::before {{ content:""; position:absolute; left:0; right:0; top:0; height:150px; pointer-events:none;
    background:linear-gradient(rgba(12,22,38,.78), rgba(12,22,38,.5) 62%, rgba(12,22,38,0)); }}
  [data-testid="stMainBlockContainer"] {{ position:relative; z-index:1; }}

  [data-testid="stElementContainer"]:has(.ns-mobile-brand) {{ display:block; }}
  .ns-mobile-brand {{ display:flex; margin-bottom:.4rem; }}
  .ns-mobile-brand .ns-emblem {{ width:38px; height:38px; border-radius:9px; }}
  .ns-mobile-brand .ns-wordmark {{ font-size:1.02rem; }}
  .ns-mobile-brand .ns-who {{ margin-left:auto; color:var(--ns-silver); font-size:.88rem; }}

  .ns-hero h1 {{ font-size:1.72rem; }} .ns-hero p {{ font-size:1rem; margin-bottom:.9rem; color:var(--ns-ice); }}
  .ns-page-title {{ font-size:1.6rem; }} .ns-page-sub {{ font-size:.98rem; margin-bottom:1rem; }}

  /* tiles stay three across, compact */
  [data-testid="stHorizontalBlock"]:has([class*="st-key-tile_"]) {{ flex-wrap:nowrap !important; gap:.5rem !important; }}
  [data-testid="stHorizontalBlock"]:has([class*="st-key-tile_"]) > [data-testid="stColumn"] {{ min-width:0 !important; flex:1 1 0 !important; width:auto !important; }}
  .ns-tile {{ padding:.7rem .65rem; min-height:86px; border-radius:12px; align-items:flex-start; }}
  .ns-tile-label {{ font-size:.74rem; white-space:normal; line-height:1.2; min-height:1.8rem; }}
  .ns-tile-value {{ font-size:1.28rem; }} .ns-tile-value small {{ font-size:.7rem; margin-left:.25rem; }}

  /* quick prompts two by two */
  [data-testid="stHorizontalBlock"]:has([class*="st-key-quick_"]) {{ flex-wrap:wrap !important; gap:.5rem !important; }}
  [data-testid="stHorizontalBlock"]:has([class*="st-key-quick_"]) > [data-testid="stColumn"] {{
    min-width:calc(50% - .25rem) !important; flex:1 1 calc(50% - .25rem) !important; width:auto !important; }}
  [class*="st-key-quick_"] {{ margin-top:0; }}
  [class*="st-key-quick_"] button {{ min-height:52px; padding:.6rem .7rem; gap:8px; }}
  [class*="st-key-quick_"] button p {{ font-size:.86rem; text-align:left; line-height:1.2; white-space:normal; }}
  [class*="st-key-quick_"] button::after {{ display:none; }}
  [class*="st-key-quick_"] button [data-testid="stMarkdownContainer"] {{ text-align:left; }}
  [class*="st-key-quick_"] button [data-testid="stIconMaterial"] {{ font-size:1.3rem; }}

  /* chat */
  .st-key-chat_panel {{ padding:.35rem .55rem .7rem; border-radius:14px; }}
  /* Size the chat to the part of the screen the phone's browser really shows (dvh), so the
     message box always sits just above the tab bar. */
  [data-testid="stLayoutWrapper"]:has(> .st-key-chat_scroll) {{
    height:calc(100vh - 528px) !important; height:calc(100dvh - 528px) !important; flex:0 0 auto !important; min-height:120px; }}
  .ns-empty svg {{ width:30px; height:30px; }} .ns-empty h3 {{ font-size:1.12rem; margin:.4rem 0 0; }}
  .ns-empty-more {{ display:none; }}
  /* Once a conversation starts, the heading and quick prompts step aside and the chat takes the room. */
  [data-testid="stMain"]:has(.ns-chatting) [data-testid="stElementContainer"]:has(.ns-hero),
  [data-testid="stMain"]:has(.ns-chatting) [data-testid="stHorizontalBlock"]:has([class*="st-key-quick_"]),
  [data-testid="stMain"]:has(.ns-chatting) [data-testid="stLayoutWrapper"]:has(> [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] [class*="st-key-quick_"]) {{
    display:none !important; }}
  [data-testid="stMain"]:has(.ns-chatting) [data-testid="stLayoutWrapper"]:has(> .st-key-chat_scroll) {{
    height:calc(100vh - 324px) !important; height:calc(100dvh - 324px) !important; }}
  [data-testid="stChatMessage"] {{ gap:10px; }}
  [data-testid="stChatMessage"] > :first-child {{ width:36px; height:36px; padding:6px; border-radius:8px; }}
  [data-testid="stChatMessageContent"] {{ padding:.75rem .9rem .8rem; }}
  [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{ font-size:1rem; }}
  .ns-user-bubble {{ font-size:1rem; max-width:84%; }} .ns-user-avatar {{ display:none; }} .ns-user-time {{ padding-right:4px; }}
  .ns-activity {{ gap:6px; font-size:.8rem; }} .ns-activity .ns-time {{ margin-left:0; }}
  .ns-source {{ font-size:.86rem; flex-wrap:wrap; gap:4px 10px; }} .ns-source span {{ flex:1 1 0; min-width:0; }}
  .ns-source small {{ margin-left:0; flex-basis:100%; padding-left:30px; }}
  .ns-draft dl {{ grid-template-columns:minmax(0,1fr); gap:0; }} .ns-draft dd {{ margin-bottom:.45rem; }}
  .ns-handoff {{ grid-template-columns:auto 1fr; }} .ns-handoff span:last-child {{ grid-column:1 / -1; }}
  .ns-empty {{ padding:.8rem .6rem .3rem; }}
  .ns-foot {{ text-align:center; }}

  /* bottom tab bar */
  [data-testid="stLayoutWrapper"]:has(> .st-key-mobile_nav) {{ display:block; }}
  .st-key-mobile_nav {{
    display:flex; position:fixed; left:0; right:0; bottom:0; z-index:999; width:100% !important;
    background:rgba(9,18,32,.96); border-top:1px solid var(--ns-line); backdrop-filter:blur(10px);
    padding:.3rem .3rem calc(.3rem + env(safe-area-inset-bottom));
  }}
  .st-key-mobile_nav [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap !important; gap:.15rem !important; }}
  .st-key-mobile_nav [data-testid="stColumn"] {{ min-width:0 !important; flex:1 1 0 !important; width:auto !important; }}
  .st-key-mobile_nav button {{
    width:100%; background:transparent; border:none; border-radius:10px; padding:.3rem 0; min-height:52px; color:var(--ns-silver);
  }}
  .st-key-mobile_nav button > div > span {{ flex-direction:column; gap:1px; }}
  .st-key-mobile_nav button p {{ font-size:.68rem; white-space:nowrap; }}
  .st-key-mobile_nav button [data-testid="stIconMaterial"] {{ font-size:1.45rem; }}
  /* phones keep a tapped button in its hover state; only the current tab should look selected */
  .st-key-mobile_nav button:hover, .st-key-mobile_nav button:active, .st-key-mobile_nav button:focus {{ background:transparent; color:var(--ns-silver); }}
  .st-key-mobile_nav button[kind="primary"], .st-key-mobile_nav [data-testid="stBaseButton-primary"] {{ background:#182C47 !important; color:var(--ns-aurora) !important; }}

  /* entry screen */
  .ns-entry-brand {{ top:1rem; left:1rem; gap:10px; }}
  .ns-entry-brand .ns-emblem {{ width:40px; height:40px; border-radius:9px; }}
  .ns-entry-brand .ns-wordmark {{ font-size:1.05rem; }} .ns-entry-brand .ns-tagline {{ font-size:.76rem; }}
  .ns-entry {{ margin-top:190px; }}
  .ns-entry h1 {{ font-size:clamp(1.9rem, 8.4vw, 3rem); }} .ns-entry p {{ font-size:1rem; margin-bottom:.4rem; }}
  [data-testid="stForm"] {{ padding:1.1rem 1rem 1rem; }}
}}
</style>
"""
