"""Startup Investor Network — Streamlit app

Four interaction modes:
  1. Home        — network stats overview
  2. Search      — explore a startup and its connections
  3. Connections — find how two startups are linked
  4. Rankings    — most-connected startups leaderboard
"""

from __future__ import annotations

import streamlit as st

# ── Page config must be the very first Streamlit call ──────────────────────
st.set_page_config(
    page_title="Startup Network",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject global styles ────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ---- palette ---- */
    :root {
        --green:  #1DB954;
        --black:  #0D0D0D;
        --surface: #1A1A1A;
        --muted:  #6B6B6B;
        --text:   #F0F0F0;
        --border: #2A2A2A;
    }

    /* ---- base ---- */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--black) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif;
    }

    /* ---- sidebar ---- */
    [data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    [data-testid="stSidebar"] .stRadio > label { font-size: 0.85rem; color: var(--muted) !important; }

    /* ---- headings ---- */
    h1, h2, h3, h4 { color: var(--text) !important; font-weight: 700; }

    /* ---- metric cards ---- */
    [data-testid="metric-container"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricValue"] { color: var(--green) !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.8rem !important; }

    /* ---- buttons ---- */
    button[kind="primary"], .stButton > button {
        background-color: var(--green) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 50px !important;
        font-weight: 700 !important;
        padding: 0.45rem 1.6rem !important;
    }
    button[kind="primary"]:hover, .stButton > button:hover {
        background-color: #17a349 !important;
    }

    /* ---- inputs / selects ---- */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSlider > div { background: var(--surface) !important; color: var(--text) !important; }

    /* ---- dataframe / table ---- */
    .stDataFrame, [data-testid="stTable"] {
        background: var(--surface) !important;
        border-radius: 10px;
    }

    /* ---- divider ---- */
    hr { border-color: var(--border) !important; }

    /* ---- info / success / warning boxes ---- */
    .stAlert { border-radius: 10px !important; }

    /* ---- tag pill ── */
    .pill {
        display: inline-block;
        background: #1a1a1a;
        border: 1px solid var(--green);
        color: var(--green);
        border-radius: 50px;
        padding: 2px 12px;
        font-size: 0.78rem;
        margin: 2px 3px;
    }

    /* ── path step card ── */
    .path-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--green);
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.6rem;
    }
    .path-arrow {
        text-align: center;
        font-size: 1.4rem;
        color: var(--green);
        margin: 0.1rem 0;
    }

    /* ── stat detail row ── */
    .stat-row {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data loading (cached) ───────────────────────────────────────────────────
from app import (
    get_bundle,
    get_raw_data,
    path_report,
    ranking_table,
    startup_details,
    startup_label_map,
)
from startup_network import connected_companies


@st.cache_data(show_spinner="Loading startup data…")
def load_data():
    df = get_raw_data()
    return df


@st.cache_data(show_spinner="Building investor network…")
def load_bundle(
    min_freq: int,
    max_prev: float,
    min_edge: int,
    industries: tuple,
    countries: tuple,
):
    return get_bundle(
        min_investor_frequency=min_freq,
        max_investor_prevalence=max_prev,
        min_edge_weight=min_edge,
        industry_filter=industries,
        country_filter=countries,
    )


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Startup Network")
    st.markdown(
        "<p style='color:#6B6B6B;font-size:0.82rem;margin-top:-0.6rem;'>Explore how startups are connected through shared investors.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["Home", "Search", "Connections", "Rankings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Filters**")

    raw_df = load_data()
    all_industries = sorted(raw_df["industry"].dropna().unique().tolist())
    all_countries = sorted(raw_df["country"].dropna().unique().tolist())

    selected_industries = st.multiselect("Industries", all_industries, placeholder="All industries")
    selected_countries = st.multiselect("Countries", all_countries, placeholder="All countries")

    st.markdown("---")
    with st.expander("Advanced", expanded=False):
        min_freq = st.slider("Min. times an investor must appear", 1, 10, 2)
        max_prev = st.slider("Max. % of startups one investor can back", 5, 50, 10) / 100
        min_edge = st.slider("Min. shared investors to draw a connection", 1, 5, 1)

# Build the bundle for all pages
bundle = load_bundle(
    min_freq=min_freq,
    max_prev=max_prev,
    min_edge=min_edge,
    industries=tuple(selected_industries),
    countries=tuple(selected_countries),
)

label_map = startup_label_map(bundle.startups)  # startup_id → "Name (dataset)"
id_by_label = {v: k for k, v in label_map.items()}
sorted_labels = sorted(label_map.values())

diag = bundle.diagnostics

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════
if "Home" in page:
    st.markdown("# The Startup Investor Network")
    st.markdown(
        "Two startups are connected when at least one VC firm backed both. "
        "This map shows how capital flows through ecosystems — who sits at the center, "
        "and how far apart any two companies really are."
    )
    st.markdown("---")

    # ── Key numbers ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    n_startups     = int(diag.get("n_startups", 0))
    n_connections  = int(diag.get("n_edges", 0))
    largest_group  = int(diag.get("largest_component", 0))
    n_inv_eligible = int(diag.get("n_investors_eligible", 0))

    c1.metric("Startups tracked", f"{n_startups:,}", help="Total companies in the current filtered view")
    c2.metric("Investor connections", f"{n_connections:,}", help="Pairs of startups that share at least one investor (edges)")
    c3.metric("Largest cluster", f"{largest_group:,}", help="Number of startups in the biggest connected group")
    c4.metric("Active investors", f"{n_inv_eligible:,}", help="Investors that appear often enough to shape connections")

    st.markdown("---")

    # ── What the numbers mean ─────────────────────────────────────────────
    st.markdown("### What you're looking at")
    col_a, col_b = st.columns(2)

    with col_a:
        density = float(diag.get("density", 0))
        st.markdown(
            f"""
            <div class="stat-row">
                <strong>Network density</strong><br/>
                <span style="font-size:1.5rem;color:#1DB954;">{density:.4f}</span><br/>
                <span style="color:#6B6B6B;font-size:0.82rem;">
                    How tightly interconnected all startups are (0 = no links, 1 = everyone linked to everyone).
                    A low number is normal — most ecosystems have a handful of hubs.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        total_inv = int(diag.get("n_investors_total", 0))
        singleton_pct = float(diag.get("singleton_investor_pct", 0))
        st.markdown(
            f"""
            <div class="stat-row">
                <strong>Investor breakdown</strong><br/>
                <span style="color:#6B6B6B;font-size:0.82rem;">
                    <b style="color:#F0F0F0">{total_inv:,}</b> unique investors found in the data.<br/>
                    <b style="color:#F0F0F0">{singleton_pct:.1f}%</b> only backed a single startup —
                    they don't create connections, so the network filters them out.<br/>
                    <b style="color:#1DB954">{n_inv_eligible:,}</b> investors are active enough to matter.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        cluster_pct = (largest_group / n_startups * 100) if n_startups else 0
        st.markdown(
            f"""
            <div class="stat-row">
                <strong>How connected is the ecosystem?</strong><br/>
                <span style="font-size:1.5rem;color:#1DB954;">{cluster_pct:.1f}%</span><br/>
                <span style="color:#6B6B6B;font-size:0.82rem;">
                    of all startups belong to the largest connected cluster —
                    meaning you can find a path between them through shared investors.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="stat-row">
                <strong>What filters are active?</strong><br/>
                <span style="color:#6B6B6B;font-size:0.82rem;">
                    {"<b style='color:#F0F0F0'>Industries:</b> " + ", ".join(selected_industries) if selected_industries else "All industries included."}<br/>
                    {"<b style='color:#F0F0F0'>Countries:</b> " + ", ".join(selected_countries) if selected_countries else "All countries included."}<br/>
                    Investors must back at least <b style="color:#F0F0F0">{min_freq}</b> startups to count.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    # st.markdown(
    #     "<p style='color:#6B6B6B;font-size:0.82rem;'>Use the sidebar to search for a startup, trace connections between two companies, or see the top-ranked startups by investor reach.</p>",
    #     unsafe_allow_html=True,
    # )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SEARCH
# ══════════════════════════════════════════════════════════════════════════════
elif "Search" in page:
    st.markdown("# Search a Startup")
    st.markdown("Pick any company to see who invested in it and which other startups share its backers.")

    chosen_label = st.selectbox("Startup", sorted_labels, index=None, placeholder="Type to search…")

    if chosen_label:
        startup_id = id_by_label[chosen_label]
        details = startup_details(bundle, startup_id)

        if details is None:
            st.error("This startup isn't in the current filtered network. Try adjusting the sidebar filters.")
        else:
            st.markdown("---")
            # ── Header row ──────────────────────────────────────────────────
            name = details["company"]
            industry = details["industry"] or "—"
            country = details["country"] or "—"
            city = details["city"] or ""
            valuation = details["valuation"] or "—"
            dataset = details["dataset"] or "—"
            location = f"{city}, {country}" if city else country

            col_title, col_meta = st.columns([3, 2])
            with col_title:
                st.markdown(f"## {name}")
                st.markdown(
                    f'<span class="pill">{industry}</span><span class="pill">{location}</span>',
                    unsafe_allow_html=True,
                )
            with col_meta:
                st.markdown(
                    f"""
                    <div class="stat-row" style="margin-top:0.5rem;">
                        <span style="color:#6B6B6B;font-size:0.78rem;">VALUATION</span><br/>
                        <span style="font-size:1.1rem;">{valuation}</span><br/>
                        <span style="color:#6B6B6B;font-size:0.76rem;">Source: {dataset}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ── Investors ────────────────────────────────────────────────────
            st.markdown("### Investors")
            investors_all = details.get("investors_all", [])
            investors_eligible = details.get("investors_eligible", [])
            if investors_all:
                pills_html = "".join(
                    f'<span class="pill" style="border-color:{"#1DB954" if inv in investors_eligible else "#3a3a3a"};'
                    f'color:{"#1DB954" if inv in investors_eligible else "#888"};">{inv}</span>'
                    for inv in investors_all
                )
                st.markdown(
                    pills_html
                    + "<br/><span style='color:#6B6B6B;font-size:0.76rem;'>Green = investor active enough to create connections in the current network.</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<span style='color:#6B6B6B;'>No investors listed for this startup.</span>", unsafe_allow_html=True)

            # ── Connected startups ───────────────────────────────────────────
            st.markdown("### Connected startups")
            neighbors_df = connected_companies(bundle, startup_id, top_n=30)

            if neighbors_df.empty:
                st.info("No startups are connected to this company under the current filters. Try lowering the investor frequency threshold in the sidebar.")
            else:
                st.markdown(
                    f"<span style='color:#6B6B6B;font-size:0.85rem;'>"
                    f"{len(neighbors_df)} companies share at least one investor with <b style='color:#F0F0F0'>{name}</b>."
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.markdown("")

                display_df = neighbors_df[["company", "weight", "shared_investors"]].copy()
                display_df.columns = ["Company", "Shared investors", "Investor names"]
                display_df.index = range(1, len(display_df) + 1)
                st.dataframe(display_df, use_container_width=True, height=420)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CONNECTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif "Connections" in page:
    st.markdown("# Find the Connection")
    st.markdown(
        "Pick two startups and we'll find the shortest chain of shared investors between them — "
        "like six degrees of separation, but for venture capital."
    )

    col_src, col_tgt = st.columns(2)
    with col_src:
        src_label = st.selectbox("From", sorted_labels, index=None, placeholder="First startup…", key="src")
    with col_tgt:
        tgt_label = st.selectbox("To", sorted_labels, index=None, placeholder="Second startup…", key="tgt")

    use_weighted = st.toggle(
        "Prefer stronger connections",
        value=False,
        help="When on, the path favors links with more shared investors over raw shortest distance.",
    )

    find_btn = st.button("Find connection →", type="primary")

    if find_btn:
        if not src_label or not tgt_label:
            st.warning("Please select both a starting and an ending startup.")
        elif src_label == tgt_label:
            st.warning("The two startups are the same — pick different ones.")
        else:
            src_id = id_by_label[src_label]
            tgt_id = id_by_label[tgt_label]

            with st.spinner("Tracing the connection…"):
                report = path_report(bundle, src_id, tgt_id, weighted=use_weighted)

            st.markdown("---")
            companies = report["path_companies"]

            if not companies:
                st.error(
                    "No connection found between these two startups under the current filters. "
                    "Try removing industry/country filters or lowering the investor frequency threshold."
                )
            else:
                hops = len(companies) - 1
                st.markdown(
                    f"### {companies[0]}  →  {companies[-1]}",
                )
                st.markdown(
                    f"<span style='color:#6B6B6B;'>Connected in <b style='color:#1DB954'>{hops} hop{'s' if hops != 1 else ''}</b> through shared investors.</span>",
                    unsafe_allow_html=True,
                )
                st.markdown("")

                # ── Path visual ──────────────────────────────────────────────
                edge_df = report["edges"]
                for i, company_name in enumerate(companies):
                    if i < len(edge_df):
                        row = edge_df.iloc[i]
                        shared_investors = str(row.get("shared_investors", ""))
                        shared_count = int(row.get("shared_investor_count", 0))
                        inv_pills = "".join(
                            f'<span class="pill">{inv.strip()}</span>'
                            for inv in shared_investors.split(",") if inv.strip()
                        )
                        st.markdown(
                            f"""
                            <div class="path-card">
                                <strong style="font-size:1.05rem;">{company_name}</strong><br/>
                                <span style="color:#6B6B6B;font-size:0.8rem;">shared with next via {shared_count} investor{'s' if shared_count != 1 else ''}:</span><br/>
                                {inv_pills}
                            </div>
                            <div class="path-arrow">↓</div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div class="path-card"><strong style="font-size:1.05rem;">{company_name}</strong></div>',
                            unsafe_allow_html=True,
                        )

                # ── Explanation ──────────────────────────────────────────────
                st.markdown("---")
                st.markdown("### How they're linked")
                explanation = report.get("explanation", "")
                st.markdown(
                    f'<div class="stat-row">{explanation}</div>',
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif "Rankings" in page:
    st.markdown("# Most Connected Startups")
    st.markdown(
        "These are the companies that sit at the center of the investor network — "
        "backed by firms that also backed many others, making them hubs of the ecosystem."
    )

    col_metric, col_topn = st.columns([2, 1])
    with col_metric:
        metric_label = st.selectbox(
            "Rank by",
            ["Total investor reach", "Number of connections", "Bridge score"],
            help=(
                "Total investor reach: sum of shared-investor counts across all connections.\n"
                "Number of connections: how many other startups share at least one investor.\n"
                "Bridge score: how often this startup lies on the shortest path between others."
            ),
        )
    with col_topn:
        top_n = st.number_input("Show top", min_value=5, max_value=100, value=25, step=5)

    metric_map = {
        "Total investor reach": "weighted_degree",
        "Number of connections": "degree",
        "Bridge score": "betweenness",
    }
    metric_key = metric_map[metric_label]

    with st.spinner("Computing rankings…"):
        ranked = ranking_table(bundle, metric=metric_key, top_n=int(top_n))

    st.markdown("---")

    if ranked.empty:
        st.info("No startups to rank under the current filters.")
    else:
        # ── Podium (top 3) ────────────────────────────────────────────────
        if len(ranked) >= 3:
            st.markdown("### Top 3")
            pod1, pod2, pod3 = st.columns(3)
            for col, pos, medal in zip([pod1, pod2, pod3], [0, 1, 2], ["#1", "#2", "#3"]):
                row = ranked.iloc[pos]
                col.markdown(
                    f"""
                    <div class="stat-row" style="text-align:center;">
                        <div style="font-size:1.6rem;">{medal}</div>
                        <strong>{row["company"]}</strong><br/>
                        <span style="color:#6B6B6B;font-size:0.78rem;">{row.get("industry","—")} · {row.get("country","—")}</span><br/>
                        <span style="color:#1DB954;font-size:1.1rem;font-weight:700;">{row["score"]:.1f}</span>
                        <span style="color:#6B6B6B;font-size:0.75rem;"> {metric_label.lower()}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ── Full table ────────────────────────────────────────────────────
        st.markdown("### Full leaderboard")
        display = ranked[["company", "score", "industry", "country"]].copy()
        display.columns = ["Company", metric_label, "Industry", "Country"]
        display.index = range(1, len(display) + 1)
        st.dataframe(display, use_container_width=True, height=520)
