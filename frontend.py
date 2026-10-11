from __future__ import annotations

import html
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Wayfarer | Travel Studio",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "appearance" not in st.session_state:
    st.session_state["appearance"] = "Light"

api_url = os.getenv("TRAVEL_API_URL", "http://127.0.0.1:8000")

st.markdown(
    """
    <style>
    :root {
        --ink: #1c302c;
        --muted: #71817a;
        --forest: #174f43;
        --mint: #c8eee1;
        --coral: #ed765e;
        --sun: #e8b849;
        --paper: #f5f7f3;
        --line: #dce4dc;
        --white: #fffefa;
    }
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
    .stApp {
        background: var(--paper);
        color: var(--ink);
        font-family: 'DM Sans', 'Avenir Next', sans-serif;
    }
    .main .block-container { max-width: 1320px; padding: 1.2rem 2rem 4rem; }
    h1, h2, h3, p, span, label { letter-spacing: 0 !important; }
    h1, h2, h3 { color: var(--ink); font-family: 'Manrope', 'Avenir Next', sans-serif; }
    h1 { font-size: 3.1rem !important; font-weight: 700 !important; line-height: 1.04 !important; }
    h2 { font-size: 1.7rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.14rem !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] {
        background: #edf2ec;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-size: 1rem !important; }
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 8px;
    }
    .stApp button[data-variant="segmented_control"] {
        background: var(--white);
        border-color: var(--line);
        color: var(--ink);
    }
    .stApp button[data-variant="segmented_control"][aria-checked="true"] {
        background: var(--forest);
        border-color: var(--forest);
        color: white;
    }
    .stApp [data-testid="stFormSubmitButton"] button,
    .stApp [data-testid="stButton"] button[kind="primary"],
    .stApp button[data-testid="baseButton-primary"] {
        background: var(--forest) !important;
        border: 1px solid var(--forest) !important;
        border-radius: 8px;
        color: white !important;
        min-height: 3rem;
        font-weight: 700;
        transition: transform 180ms ease, background 180ms ease, box-shadow 180ms ease;
    }
    .stApp [data-testid="stFormSubmitButton"] button:hover,
    .stApp [data-testid="stButton"] button[kind="primary"]:hover,
    .stApp button[data-testid="baseButton-primary"]:hover {
        background: #216b58 !important;
        border-color: #216b58 !important;
        box-shadow: 0 8px 20px #174f4324;
        transform: translateY(-1px);
    }
    [data-testid="stExpander"] {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 8px;
        margin-bottom: 0.6rem;
    }
    [data-testid="stMetric"] {
        background: var(--white);
        border: 1px solid var(--line);
        border-top: 3px solid var(--coral);
        padding: 14px;
        border-radius: 8px;
    }
    [data-testid="stMetricValue"] { color: var(--forest); font-family: 'Manrope', sans-serif; }
    .brandbar {
        align-items: center;
        display: flex;
        gap: 0.7rem;
        margin: 0.15rem 0 1rem;
    }
    .brand-mark {
        align-items: center;
        background: var(--forest);
        border-radius: 8px;
        color: white;
        display: inline-flex;
        font-size: 1.1rem;
        height: 38px;
        justify-content: center;
        width: 38px;
    }
    .brand-name { color: var(--ink); font: 800 0.9rem 'Manrope', sans-serif; letter-spacing: 0.08em !important; }
    .brand-context { color: var(--muted); font-size: 0.72rem; margin-left: auto; }
    .hero {
        align-items: flex-end;
        background-image: linear-gradient(90deg, #102a25d9 0%, #163a315c 56%, #102a2510 100%),
            url('/app/static/travel_hero.png');
        background-position: center 48%;
        background-size: cover;
        border-radius: 8px;
        color: white;
        display: flex;
        min-height: 330px;
        overflow: hidden;
        padding: 2.6rem 3rem;
        position: relative;
    }
    .hero:after {
        border: 1px solid #ffffff50;
        border-radius: 50%;
        content: '';
        height: 270px;
        position: absolute;
        right: 9%;
        top: -145px;
        width: 270px;
    }
    .hero-copy { max-width: 660px; position: relative; z-index: 1; }
    .hero-kicker { color: #d0f1e4; font-size: 0.74rem; font-weight: 700; letter-spacing: 0.14em !important; }
    .hero h1 { color: white; font-size: 3.15rem !important; margin: 0.65rem 0 0.8rem; }
    .hero p { color: #f4f5ef; font-size: 1rem; line-height: 1.6; margin: 0; max-width: 510px; }
    .search-panel {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 12px 34px #243e3210;
        margin: -1rem 1.2rem 2.5rem;
        padding: 1.1rem 1.3rem 0.35rem;
        position: relative;
        z-index: 2;
    }
    .section-kicker { color: var(--forest); font-size: 0.7rem; font-weight: 800; letter-spacing: 0.12em !important; }
    .section-heading { align-items: flex-end; display: flex; justify-content: space-between; margin: 2.1rem 0 1rem; }
    .section-heading h2 { margin: 0; }
    .section-note { color: var(--muted); font-size: 0.83rem; }
    .profile-strip {
        align-items: center;
        background: #e5f1e9;
        border-left: 4px solid var(--forest);
        border-radius: 0 8px 8px 0;
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem 1.3rem;
        margin: 1.15rem 0 2rem;
        padding: 0.9rem 1.1rem;
    }
    .profile-label { color: var(--muted); font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em !important; text-transform: uppercase; }
    .profile-value { color: var(--ink); font-size: 0.9rem; font-weight: 700; }
    .destination-card {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 8px;
        min-height: 178px;
        overflow: hidden;
        padding: 1.1rem;
        position: relative;
        transition: transform 180ms ease, box-shadow 180ms ease;
    }
    .destination-card:hover { box-shadow: 0 12px 28px #203d3017; transform: translateY(-3px); }
    .destination-index { color: var(--coral); font: 800 0.72rem 'Manrope', sans-serif; letter-spacing: 0.1em !important; }
    .destination-name { color: var(--ink); font: 700 1.1rem 'Manrope', sans-serif; margin: 0.55rem 0 1.2rem; }
    .destination-rating { color: var(--forest); font: 800 1.45rem 'Manrope', sans-serif; }
    .destination-meta { color: var(--muted); font-size: 0.77rem; margin-top: 0.2rem; }
    .activity-row { display: flex; flex-wrap: wrap; gap: 0.55rem; margin: 0.7rem 0 1.7rem; }
    .activity-item {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 8px;
        flex: 1 1 145px;
        min-width: 135px;
        padding: 0.8rem 0.9rem;
    }
    .activity-name { color: var(--muted); font-size: 0.75rem; }
    .activity-rating { color: var(--ink); font: 700 1.05rem 'Manrope', sans-serif; margin-top: 0.2rem; }
    .evidence-meta { color: var(--muted); font-size: 0.78rem; }
    .trust-note {
        background: #fff5e3;
        border: 1px solid #f1dfb9;
        border-radius: 8px;
        color: #715522;
        font-size: 0.84rem;
        margin: 0.55rem 0;
        padding: 0.75rem 0.9rem;
    }
    .empty-state {
        background: #e8f0eb;
        border: 1px dashed #aac4b6;
        border-radius: 8px;
        color: var(--muted);
        padding: 1.1rem;
    }
    .footer { border-top: 1px solid var(--line); color: var(--muted); font-size: 0.72rem; margin-top: 3rem; padding-top: 1rem; }
    .loading-overlay {
        align-items: center;
        animation: veil-in 220ms ease-out both;
        backdrop-filter: blur(12px);
        background: #f3f7f2eF;
        display: flex;
        inset: 0;
        justify-content: center;
        position: fixed;
        z-index: 999999;
    }
    .loading-panel { max-width: 430px; padding: 2rem; text-align: center; width: calc(100% - 2rem); }
    .flight-mark {
        align-items: center;
        background: var(--forest);
        border: 8px solid #d7eee4;
        border-radius: 50%;
        box-shadow: 0 15px 38px #174f432b;
        color: white;
        display: flex;
        font-size: 2rem;
        height: 100px;
        justify-content: center;
        margin: 0 auto 1.6rem;
        position: relative;
        width: 100px;
    }
    .flight-mark span { animation: plane-fly 1.8s ease-in-out infinite; display: inline-block; }
    .flight-mark:before, .flight-mark:after {
        border: 1px solid #78a793;
        border-radius: 50%;
        content: '';
        inset: -20px;
        position: absolute;
    }
    .flight-mark:after { animation: orbit-pulse 2s ease-out infinite; inset: -31px; }
    .loading-kicker { color: var(--forest); font-size: 0.7rem; font-weight: 800; letter-spacing: 0.16em !important; }
    .loading-title { color: var(--ink); font: 800 1.8rem/1.2 'Manrope', sans-serif; margin: 0.6rem 0; }
    .loading-copy { color: var(--muted); font-size: 0.9rem; }
    .flight-track { background: #d7e2da; border-radius: 99px; height: 4px; margin: 1.5rem auto 0; max-width: 250px; overflow: hidden; }
    .flight-track span { animation: track-run 1.5s ease-in-out infinite; background: var(--coral); border-radius: inherit; display: block; height: 100%; width: 36%; }
    @keyframes plane-fly { 0%, 100% { transform: translate(-3px, 4px) rotate(-12deg); } 50% { transform: translate(5px, -5px) rotate(-5deg); } }
    @keyframes orbit-pulse { 0% { opacity: 0.7; transform: scale(0.94); } 100% { opacity: 0; transform: scale(1.13); } }
    @keyframes track-run { 0% { transform: translateX(-110%); } 100% { transform: translateX(290%); } }
    @keyframes veil-in { from { opacity: 0; } to { opacity: 1; } }
    @media (max-width: 760px) {
        .main .block-container { padding: 0.8rem 0.85rem 2.5rem; }
        h1 { font-size: 2.15rem !important; }
        .hero { min-height: 300px; padding: 1.5rem; }
        .hero h1 { font-size: 2.25rem !important; }
        .hero p { font-size: 0.9rem; }
        .search-panel { margin: -0.7rem 0.45rem 1.7rem; padding: 0.8rem 0.9rem 0.2rem; }
        .brand-context { display: none; }
        .section-heading { align-items: flex-start; flex-direction: column; gap: 0.35rem; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *:before, *:after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state["appearance"] == "Dark":
    st.markdown(
        """
        <style>
        :root {
            --ink: #edf4ee;
            --muted: #afc0b5;
            --forest: #8dd8bc;
            --mint: #1a3931;
            --coral: #f09579;
            --sun: #f0c96c;
            --paper: #101916;
            --line: #34463e;
            --white: #19241f;
        }
        html, body, [data-testid="stAppViewContainer"], .stApp, [data-testid="stHeader"] {
            background: #101916 !important;
            color: var(--ink) !important;
        }
        [data-testid="stSidebar"] { background: #17231e !important; border-color: var(--line) !important; }
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], .stApp label,
        .stApp p { color: var(--ink); }
        [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
        [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: #202d27 !important;
            border-color: #455950 !important;
            color: var(--ink) !important;
        }
        .stApp input::placeholder, .stApp textarea::placeholder {
            color: #afc0b5 !important;
            opacity: 1 !important;
        }
        .stApp button[data-variant="segmented_control"] {
            background: #202d27 !important;
            border-color: #455950 !important;
            color: var(--ink) !important;
        }
        .stApp button[data-variant="segmented_control"][aria-checked="true"] {
            background: #315b4d !important;
            border-color: #6a9e85 !important;
            color: #f3fff7 !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] span { color: var(--ink) !important; }
        [data-testid="stExpander"], [data-testid="stMetric"], .destination-card,
        .activity-item, .search-panel { background: var(--white) !important; border-color: var(--line) !important; }
        [data-testid="stMetricValue"], .destination-rating, .section-kicker { color: var(--forest) !important; }
        .profile-strip { background: #20382f !important; border-left-color: var(--forest) !important; }
        .empty-state { background: #192720 !important; border-color: #455d50 !important; color: var(--muted) !important; }
        .destination-name, .activity-rating, .profile-value, .section-heading h2 { color: var(--ink) !important; }
        .destination-meta, .activity-name, .section-note, .evidence-meta,
        .profile-label, .footer, .brand-context { color: var(--muted) !important; }
        .brand-name { color: var(--ink) !important; }
        .hero { background-image: linear-gradient(90deg, #081611ed 0%, #0e281ec2 58%, #0b171a30 100%),
            url('/app/static/travel_hero.png') !important; }
        .loading-overlay { background: #0d1714f2 !important; }
        .loading-title { color: var(--ink) !important; }
        .loading-copy { color: var(--muted) !important; }
        .loading-kicker { color: var(--forest) !important; }
        .flight-mark { background: #1b4c3f !important; border-color: #294b3f !important; }
        .flight-track { background: #34483e !important; }
        .footer { border-color: var(--line) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        :root {
            --ink: #1c302c !important;
            --muted: #71817a !important;
            --forest: #174f43 !important;
            --mint: #c8eee1 !important;
            --coral: #ed765e !important;
            --sun: #e8b849 !important;
            --paper: #f5f7f3 !important;
            --line: #dce4dc !important;
            --white: #fffefa !important;
        }
        html, body, [data-testid="stAppViewContainer"], .stApp, [data-testid="stHeader"] {
            background: #f5f7f3 !important;
            color: #1c302c !important;
        }
        [data-testid="stSidebar"] { background: #edf2ec !important; border-color: #dce4dc !important; }
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], .stApp label,
        .stApp p { color: #1c302c !important; }
        [data-testid="stCaptionContainer"] { color: #71817a !important; }
        [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: #fffefa !important;
            border-color: #dce4dc !important;
            color: #1c302c !important;
        }
        .stApp input::placeholder, .stApp textarea::placeholder { color: #71817a !important; opacity: 1 !important; }
        [data-testid="stSelectbox"] [data-baseweb="select"] span { color: #1c302c !important; }
        [data-testid="stExpander"], [data-testid="stMetric"], .destination-card,
        .activity-item, .search-panel { background: #fffefa !important; border-color: #dce4dc !important; }
        [data-testid="stMetricValue"], .destination-rating, .section-kicker { color: #174f43 !important; }
        .profile-strip { background: #e5f1e9 !important; border-left-color: #174f43 !important; }
        .empty-state { background: #e8f0eb !important; border-color: #aac4b6 !important; color: #71817a !important; }
        .destination-name, .activity-rating, .profile-value, .section-heading h2 { color: #1c302c !important; }
        .destination-meta, .activity-name, .section-note, .evidence-meta,
        .profile-label, .footer, .brand-context { color: #71817a !important; }
        .brand-name { color: #1c302c !important; }
        .hero { background-image: linear-gradient(90deg, #102a25d9 0%, #163a315c 56%, #102a2510 100%),
            url('/app/static/travel_hero.png') !important; }
        .hero p { color: #f4f5ef !important; }
        .loading-overlay { background: #f3f7f2ef !important; }
        .loading-title { color: #1c302c !important; }
        .loading-copy { color: #71817a !important; }
        .loading-kicker { color: #174f43 !important; }
        .flight-mark { background: #174f43 !important; border-color: #d7eee4 !important; }
        .flight-track { background: #d7e2da !important; }
        .stApp button[data-variant="segmented_control"] {
            background: #fffefa !important;
            border-color: #dce4dc !important;
            color: #1c302c !important;
        }
        .stApp button[data-variant="segmented_control"][aria-checked="true"] {
            background: #174f43 !important;
            border-color: #174f43 !important;
            color: #ffffff !important;
        }
        .footer { border-color: #dce4dc !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

LOADER_HTML = """
<div class="loading-overlay" role="status" aria-live="polite">
  <div class="loading-panel">
    <div class="flight-mark" aria-hidden="true"><span>✈</span></div>
    <div class="loading-kicker">WAYFARER TRAVEL STUDIO</div>
    <div class="loading-title">Finding your kind<br>of somewhere.</div>
    <div class="loading-copy">Scouting places that feel like your kind of trip.</div>
    <div class="flight-track"><span></span></div>
  </div>
</div>
"""

st.markdown(
    """
    <div class="brandbar">
      <div class="brand-mark" aria-hidden="true">✈</div>
      <div class="brand-name">WAYFARER</div>
      <div class="brand-context">PERSONAL TRAVEL STUDIO&nbsp;&nbsp; / &nbsp;&nbsp;PROJECT 02</div>
    </div>
    <section class="hero">
      <div class="hero-copy">
        <div class="hero-kicker">GO SOMEWHERE THAT GETS YOU</div>
        <h1>Travel, with a little more feeling.</h1>
        <p>Find places and experiences that match how you like to travel, informed by the journeys that came before.</p>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Refine your search")
    st.caption("Shape the results around your trip.")
    st.segmented_control("Appearance", ["Light", "Dark"], key="appearance")
    destination = st.text_input("Destination filter", placeholder="e.g. Nice, France")
    travel_type = st.selectbox("Travel party", ["Any", "Solo", "Couple", "Family", "Friends", "Business"])
    minimum_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=0.0, step=0.5)
    result_count = st.slider("Number of results", min_value=1, max_value=10, value=5)
    st.divider()
    try:
        health = requests.get(f"{api_url.rstrip('/')}/health", timeout=2).json()
        st.success("Ready for your next trip")
    except requests.RequestException:
        st.warning("Unable to load recommendations right now.")

st.markdown('<div class="search-panel">', unsafe_allow_html=True)
st.markdown('<div class="section-kicker">YOUR NEXT CHAPTER</div>', unsafe_allow_html=True)
with st.form("travel_query"):
    query = st.text_area(
        "Describe the trip you have in mind",
        value="A 5-day beach trip with local food for a couple",
        height=90,
        placeholder="Interests, destination, travel party, duration or budget",
        label_visibility="visible",
    )
    submitted = st.form_submit_button("Find recommendations  →", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not query.strip():
        st.warning("Enter a travel query to continue.")
    else:
        filters: dict[str, str | float] = {}
        if destination.strip():
            filters["destination"] = destination.strip()
        if travel_type != "Any":
            filters["travel_type"] = travel_type
        if minimum_rating > 0:
            filters["min_rating"] = minimum_rating
        loading = st.empty()
        loading.markdown(LOADER_HTML, unsafe_allow_html=True)
        try:
            response = requests.post(
                f"{api_url.rstrip('/')}/api/v1/recommendations",
                json={"query": query.strip(), "limit": result_count, "filters": filters},
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
            st.session_state["recommendation_result"] = result
            st.session_state["recommendation_api_url"] = api_url.rstrip("/")
        except requests.RequestException as error:
            st.error(f"Could not reach the API: {error}")
        finally:
            loading.empty()

result = st.session_state.get("recommendation_result")
if result:
    preferences = result["preferences"]
    interest_label = html.escape(", ".join(preferences["interests"]) or "No activity preference extracted")
    party_label = html.escape(preferences["travel_type"] or "Not specified")
    st.markdown(
        f"""
        <div class="profile-strip">
          <span class="profile-label">Trip read</span>
          <span><span class="profile-label">Interests</span><br><span class="profile-value">{interest_label}</span></span>
          <span><span class="profile-label">Travel party</span><br><span class="profile-value">{party_label}</span></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    destinations = result["destinations"]
    activities = result["activities"]
    st.markdown(
        '<div class="section-heading"><div><div class="section-kicker">A GOOD PLACE TO BEGIN</div>'
        '<h2>Places with a similar pulse</h2></div><div class="section-note">Ranked from matching past experiences</div></div>',
        unsafe_allow_html=True,
    )
    if not destinations:
        st.markdown('<div class="empty-state">No experiences matched those filters. Try broadening the search.</div>', unsafe_allow_html=True)
    else:
        destination_columns = st.columns(min(3, len(destinations)))
        for index, item in enumerate(destinations):
            with destination_columns[index % len(destination_columns)]:
                destination_name = html.escape(item["destination"])
                st.markdown(
                    f"""
                    <article class="destination-card">
                      <div class="destination-index">MATCH {index + 1:02d}</div>
                      <div class="destination-name">{destination_name}</div>
                      <div class="destination-rating">{item['average_rating']:.2f}<span style="font-size:.78rem;color:#71817a;font-weight:500"> / 5</span></div>
                      <div class="destination-meta">{item['evidence_count']} matching experience(s)</div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        '<div class="section-heading"><div><div class="section-kicker">THE DETAILS THAT MATTER</div>'
        '<h2>Experiences worth your time</h2></div><div class="section-note">Ideas that fit your interests</div></div>',
        unsafe_allow_html=True,
    )
    if activities:
        activity_html = '<div class="activity-row">'
        for item in activities:
            category = html.escape(item["category"].title())
            activity_html += (
                '<div class="activity-item">'
                f'<div class="activity-name">{category}</div>'
                f'<div class="activity-rating">{item["average_rating"]:.2f} / 5</div>'
                f'<div class="destination-meta">{item["evidence_count"]} rated case(s)</div>'
                '</div>'
            )
        activity_html += "</div>"
        st.markdown(activity_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">No rated activities were found for these preferences.</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-heading"><div><div class="section-kicker">THE PROOF, NOT JUST THE PROMISE</div>'
        '<h2>Travel stories behind the matches</h2></div></div>',
        unsafe_allow_html=True,
    )
    for item in result["evidence"]:
        title = f"{item['destination']}  ·  {item['overall_rating']:.2f}/5  ·  {item['travel_type']}"
        with st.expander(title):
            st.markdown(f"_{html.escape(item['review_text'])}_")
            categories = html.escape(", ".join(item["categories_visited"]))
            st.markdown(
                f'<div class="evidence-meta">{categories}<br>Visited {html.escape(item["visit_date"])}</div>',
                unsafe_allow_html=True,
            )
            rating = st.slider(
                "Was this result useful?",
                min_value=1,
                max_value=5,
                value=4,
                key=f"rating_{item['experience_id']}",
            )
            comment = st.text_input("Feedback note", key=f"comment_{item['experience_id']}")
            if st.button("Submit feedback", key=f"feedback_{item['experience_id']}"):
                try:
                    feedback_response = requests.post(
                        f"{st.session_state['recommendation_api_url']}/api/v1/feedback",
                        json={
                            "experience_id": item["experience_id"],
                            "rating": rating,
                            "comment": comment,
                        },
                        timeout=10,
                    )
                    feedback_response.raise_for_status()
                    st.success("Feedback recorded.")
                except requests.RequestException as error:
                    st.error(f"Feedback could not be saved: {error}")

st.markdown(
    '<div class="footer">WAYFARER · Find a place for your next story.</div>',
    unsafe_allow_html=True,
)