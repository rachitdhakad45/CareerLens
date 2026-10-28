"""CareerLens visual theme and Streamlit component styling."""

import streamlit as st


def inject_theme() -> None:
    """Apply the responsive dark visual system used across the app."""
    st.markdown(
        """
        <style>
        :root {
          color-scheme: dark;
          --cl-bg: #091216;
          --cl-panel: #101b20;
          --cl-panel-2: #142329;
          --cl-border: rgba(196, 224, 213, .11);
          --cl-muted: #9aaba9;
          --cl-text: #edf5f1;
          --cl-mint: #87e3c5;
          --cl-lime: #d5f080;
          --cl-lilac: #c7b7ff;
        }
        html, body, [data-testid="stAppViewContainer"] {
          background: var(--cl-bg);
          color: var(--cl-text);
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
        }
        [data-testid="stAppViewContainer"] {
          background-image: radial-gradient(ellipse at 86% 4%, rgba(76, 133, 119, .16), transparent 30%),
                            radial-gradient(ellipse at 8% 32%, rgba(94, 83, 145, .08), transparent 34%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] { max-width: 1320px; padding-top: 1.3rem; padding-bottom: 4rem; }
        h1, h2, h3, h4 { color: var(--cl-text); letter-spacing: -.035em; }
        h2 { font-size: 1.55rem; }
        p, label, [data-testid="stMarkdownContainer"] { color: var(--cl-text); }
        [data-testid="stCaptionContainer"] p { color: var(--cl-muted); }
        [data-testid="stVerticalBlockBorderWrapper"] {
          background: linear-gradient(135deg, rgba(21, 35, 40, .88), rgba(15, 26, 31, .82));
          border: 1px solid var(--cl-border); border-radius: 20px; padding: 1.15rem 1.35rem;
          box-shadow: 0 16px 45px rgba(0, 0, 0, .14);
        }
        [data-testid="stMetric"] {
          background: linear-gradient(145deg, rgba(21, 38, 43, .92), rgba(15, 27, 31, .9));
          border: 1px solid var(--cl-border); border-radius: 16px; padding: 1rem 1.05rem;
        }
        [data-testid="stMetricLabel"] p { color: var(--cl-muted); font-size: .79rem; letter-spacing: .04em; }
        [data-testid="stMetricValue"] { color: var(--cl-mint); font-weight: 650; }
        [data-testid="stTabs"] [role="tablist"] { gap: .55rem; border-bottom: 1px solid var(--cl-border); }
        [data-testid="stTabs"] button[role="tab"] { color: var(--cl-muted); padding: .8rem 1rem; border-radius: 12px 12px 0 0; }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: var(--cl-mint); }
        [data-testid="stFileUploader"] section {
          background: rgba(8, 18, 22, .38); border: 1px dashed rgba(135, 227, 197, .43);
          border-radius: 15px; transition: border-color .2s ease, background .2s ease;
        }
        [data-testid="stFileUploader"] section:hover { border-color: var(--cl-mint); background: rgba(135, 227, 197, .045); }
        [data-testid="stFileUploader"] button, [data-testid="stBaseButton-secondary"] {
          border: 1px solid rgba(135, 227, 197, .32); border-radius: 10px; color: var(--cl-mint); background: rgba(135, 227, 197, .07);
        }
        [data-testid="stBaseButton-primary"] { background: var(--cl-mint); color: #09201b; border: 0; border-radius: 10px; font-weight: 700; }
        [data-testid="stBaseButton-primary"]:hover { background: var(--cl-lime); color: #09201b; border: 0; }
        [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stTextArea"] textarea { background: var(--cl-panel); border-color: var(--cl-border); border-radius: 10px; }
        [data-testid="stExpander"] { border-color: var(--cl-border); border-radius: 14px; background: rgba(16, 27, 32, .55); }
        [data-testid="stAlert"] { border-radius: 13px; }
        a { color: var(--cl-mint) !important; }
        .cl-topbar { display:flex; justify-content:space-between; align-items:center; padding:.15rem 0 1.15rem; border-bottom:1px solid var(--cl-border); margin-bottom:2.2rem; }
        .cl-brand { display:flex; align-items:center; gap:.65rem; font-size:1.02rem; font-weight:750; letter-spacing:-.02em; color:var(--cl-text); }
        .cl-mark { width:2rem; height:2rem; display:grid; place-items:center; border-radius:10px; color:#09201b; background:linear-gradient(145deg,var(--cl-mint),var(--cl-lime)); font-weight:900; }
        .cl-topbar-note { display:flex; align-items:center; gap:.55rem; font-size:.65rem; letter-spacing:.15em; color:var(--cl-muted); font-weight:700; }
        .cl-live-dot { width:.42rem; height:.42rem; border-radius:50%; background:var(--cl-mint); box-shadow:0 0 12px rgba(135,227,197,.65); }
        .cl-hero { display:grid; grid-template-columns:1.35fr .75fr; align-items:center; gap:2rem; min-height:295px; padding:2rem 2.35rem; margin-bottom:2.3rem; border:1px solid var(--cl-border); border-radius:25px; overflow:hidden; position:relative; background:linear-gradient(115deg,rgba(19,36,40,.98),rgba(18,31,40,.94) 65%,rgba(36,38,61,.93)); box-shadow:0 22px 65px rgba(0,0,0,.22); }
        .cl-hero:after { content:""; position:absolute; width:340px; height:340px; border-radius:50%; right:8%; top:-60%; background:rgba(135,227,197,.07); filter:blur(2px); }
        .cl-eyebrow,.cl-section-kicker { color:var(--cl-mint); font-size:.64rem; letter-spacing:.17em; font-weight:750; }
        .cl-eyebrow { display:flex; align-items:center; gap:.65rem; }
        .cl-eyebrow-line { width:1.4rem; height:1px; background:var(--cl-mint); }
        .cl-hero h1 { font-size:clamp(2.45rem,5vw,4.1rem); line-height:1.02; margin:.9rem 0 .9rem; font-weight:760; color:#f2f7f3; }
        .cl-hero h1 span { color:var(--cl-mint); }
        .cl-hero-copy > p { max-width:600px; color:#b4c2bf; font-size:.99rem; line-height:1.7; margin:0; }
        .cl-hero-tags { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.35rem; }
        .cl-hero-tags span { border:1px solid rgba(196,224,213,.12); border-radius:999px; padding:.42rem .7rem; color:#c2d2cc; font-size:.59rem; letter-spacing:.09em; }
        .cl-hero-art { height:235px; display:grid; place-items:center; position:relative; isolation:isolate; }
        .cl-orbit { position:absolute; border:1px solid rgba(135,227,197,.2); border-radius:50%; transform:rotate(-25deg); }
        .cl-orbit-one { width:220px; height:128px; }
        .cl-orbit-two { width:160px; height:220px; border-color:rgba(199,183,255,.18); transform:rotate(35deg); }
        .cl-orbit-core { width:78px; height:78px; display:grid; place-items:center; border-radius:24px; color:#0b211b; font-size:2.1rem; background:linear-gradient(145deg,var(--cl-mint),var(--cl-lime)); box-shadow:0 0 50px rgba(135,227,197,.22); transform:rotate(-8deg); }
        .cl-art-label { position:absolute; right:2%; bottom:2%; padding:.7rem .9rem; border:1px solid var(--cl-border); border-radius:12px; background:rgba(9,18,22,.78); backdrop-filter:blur(10px); display:flex; flex-direction:column; gap:.2rem; }
        .cl-art-label span { font-size:.53rem; letter-spacing:.13em; color:var(--cl-mint); }
        .cl-art-label strong { font-size:.85rem; color:var(--cl-text); }
        .cl-art-spark { position:absolute; color:var(--cl-lime); font-size:1.2rem; }
        .cl-spark-one { top:18%; right:16%; }.cl-spark-two { left:16%; bottom:20%; font-size:2rem; color:var(--cl-lilac); }
        .cl-section-heading { display:flex; align-items:end; justify-content:space-between; gap:1rem; margin:0 0 1rem; }
        .cl-section-heading h2 { margin:.42rem 0 0; font-size:1.5rem; }
        .cl-step-note { color:var(--cl-muted); font-size:.64rem; letter-spacing:.1em; padding-bottom:.2rem; }
        .cl-privacy-card { display:flex; gap:.85rem; align-items:flex-start; min-height:90px; padding:1rem; border-radius:14px; border:1px solid rgba(135,227,197,.16); background:rgba(135,227,197,.045); }
        .cl-privacy-icon { width:1.8rem; height:1.8rem; flex:0 0 1.8rem; display:grid; place-items:center; color:#0b211b; background:var(--cl-mint); border-radius:9px; font-weight:800; }
        .cl-privacy-card strong { font-size:.85rem; color:var(--cl-text); }.cl-privacy-card p { margin:.25rem 0 0; color:var(--cl-muted); font-size:.76rem; line-height:1.5; }
        .cl-feature-row { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:2rem; }
        .cl-feature { min-height:120px; padding:1.15rem 1.25rem; border:1px solid var(--cl-border); border-radius:16px; background:linear-gradient(145deg,rgba(17,30,35,.88),rgba(13,24,29,.72)); }
        .cl-feature span { display:block; color:var(--cl-mint); font-size:.6rem; letter-spacing:.12em; margin-bottom:.65rem; }
        .cl-feature strong { color:var(--cl-text); font-size:.94rem; }.cl-feature p { color:var(--cl-muted); font-size:.78rem; line-height:1.5; margin:.42rem 0 0; }
        .cl-landing-intro { text-align:center; margin:2.7rem 0 1.25rem; }.cl-landing-intro h2 { margin:.5rem 0 .35rem; font-size:1.7rem; }.cl-landing-intro p { color:var(--cl-muted); margin:0; font-size:.9rem; }
        .cl-landing-features .cl-feature { min-height:150px; transition:transform .18s ease,border-color .18s ease,background .18s ease; }.cl-landing-features .cl-feature:hover { transform:translateY(-3px); border-color:rgba(135,227,197,.3); background:linear-gradient(145deg,rgba(25,45,48,.95),rgba(16,30,34,.88)); }
        .cl-how { display:grid; grid-template-columns:.8fr 1.5fr; align-items:center; gap:1.5rem; margin-top:1.2rem; padding:1.35rem 1.5rem; border:1px solid var(--cl-border); border-radius:17px; background:rgba(15,27,32,.65); }
        .cl-how h2 { font-size:1.2rem; margin:.4rem 0 0; }.cl-how-steps { display:flex; align-items:center; justify-content:space-between; gap:.8rem; }.cl-how-steps div { display:flex; flex-direction:column; gap:.2rem; }.cl-how-steps span { color:var(--cl-mint); font-size:.59rem; letter-spacing:.1em; }.cl-how-steps strong { color:var(--cl-text); font-size:.82rem; }.cl-how-steps small { color:var(--cl-muted); font-size:.68rem; }.cl-how-steps i { color:rgba(135,227,197,.55); font-style:normal; }
        .cl-landing-trust { display:flex; align-items:center; gap:.7rem; margin-top:1rem; padding:.8rem 1rem; border:1px solid rgba(135,227,197,.13); border-radius:13px; background:rgba(135,227,197,.035); }.cl-landing-trust > span { color:var(--cl-mint); font-size:1.15rem; }.cl-landing-trust p { flex:1; color:var(--cl-muted); font-size:.75rem; margin:0; }.cl-landing-trust strong { color:var(--cl-text); }.cl-landing-trust small { color:#82928e; font-size:.62rem; }
        .cl-landing-link { padding:.7rem .4rem; font-size:.83rem; }.cl-landing-link a { text-decoration:none; }
        .cl-workspace-title { padding:.1rem 0 .6rem; }.cl-workspace-title h1 { font-size:1.75rem; margin:.45rem 0 .2rem; }.cl-workspace-title p { color:var(--cl-muted); font-size:.85rem; margin:0; }
        .cl-snapshot-kicker { color:var(--cl-mint); font-size:.62rem; letter-spacing:.16em; font-weight:750; margin-top:.8rem; }
        .cl-workspace-privacy { display:flex; flex-wrap:wrap; align-items:center; gap:.5rem .8rem; margin:.3rem 0 1rem; padding:.7rem .9rem; border:1px solid var(--cl-border); border-radius:12px; background:rgba(16,27,32,.52); }.cl-workspace-privacy strong { color:var(--cl-mint); font-size:.72rem; }.cl-workspace-privacy span { color:#b4c2bf; font-size:.72rem; }.cl-workspace-privacy small { color:var(--cl-muted); font-size:.65rem; }
        .cl-upload-aside { display:flex; gap:.85rem; align-items:flex-start; min-height:75px; padding:1rem; border-radius:14px; border:1px solid rgba(135,227,197,.16); background:rgba(135,227,197,.045); }.cl-upload-aside strong { font-size:.85rem; color:var(--cl-text); }.cl-upload-aside p { margin:.3rem 0 0; color:var(--cl-muted); font-size:.75rem; line-height:1.5; }
        .cl-results-count { display:flex; align-items:baseline; gap:.55rem; margin:.5rem 0 .8rem; }.cl-results-count strong { color:var(--cl-mint); font-size:.95rem; }.cl-results-count span { color:var(--cl-muted); font-size:.76rem; }
        .cl-job-tags { display:flex; flex-wrap:wrap; gap:.4rem; margin:.15rem 0 .6rem; }.cl-job-tags span { border:1px solid var(--cl-border); background:rgba(135,227,197,.04); border-radius:999px; padding:.28rem .55rem; color:#b5c5bf; font-size:.65rem; }
        [data-testid="stChatMessage"] { border:1px solid var(--cl-border); border-radius:14px; background:rgba(16,27,32,.72); }
        [data-testid="stForm"] { border:1px solid var(--cl-border); border-radius:15px; background:rgba(16,27,32,.48); padding:1rem; }
        .cl-footer-note { text-align:center; color:#748580; font-size:.7rem; letter-spacing:.08em; margin-top:2rem; }
        .cl-prediction { display:flex; flex-wrap:wrap; align-items:center; gap:.55rem .8rem; padding:.8rem 1rem; margin:.5rem 0 1.2rem; border-left:2px solid var(--cl-mint); border-radius:0 10px 10px 0; background:rgba(135,227,197,.055); }
        .cl-prediction-label { color:var(--cl-mint); font-size:.6rem; letter-spacing:.12em; font-weight:750; }.cl-prediction small { color:var(--cl-muted); font-size:.7rem; }
        @media (max-width:760px) {
          [data-testid="stMainBlockContainer"] { padding:1rem 1rem 3rem; }
          .cl-topbar { margin-bottom:1.2rem; }.cl-topbar-note { font-size:.52rem; letter-spacing:.09em; }
          .cl-hero { grid-template-columns:1fr; min-height:unset; padding:1.6rem 1.3rem; gap:.5rem; }
          .cl-hero h1 { font-size:2.55rem; }.cl-hero-art { height:150px; }.cl-orbit-one { width:175px; height:105px; }.cl-orbit-two { width:125px; height:165px; }
          .cl-art-label { right:0; bottom:-.1rem; }.cl-section-heading { align-items:start; flex-direction:column; }.cl-feature-row { grid-template-columns:1fr; gap:.7rem; }
          .cl-how { grid-template-columns:1fr; }.cl-how-steps { align-items:flex-start; flex-direction:column; }.cl-how-steps i { transform:rotate(90deg); }.cl-landing-trust { align-items:flex-start; flex-wrap:wrap; }.cl-landing-trust p { flex-basis:calc(100% - 2rem); }
          [data-testid="stVerticalBlockBorderWrapper"] { padding:.9rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
