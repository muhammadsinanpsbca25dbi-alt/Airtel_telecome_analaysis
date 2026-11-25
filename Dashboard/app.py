# ============================================================
# AIRTEL RETENTION INTELLIGENCE  |  DOMAIN A
# Professional single-screen Streamlit dashboard (SQLite backed)
# ============================================================

import math
import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------- CONFIG ---------------------------

st.set_page_config(
    page_title="Airtel | Retention Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

TABLE_NAME = "customer_features"

# Database lookup order: env var AIRTEL_DB -> your original path -> local folders
DB_CANDIDATES = [
    os.environ.get("AIRTEL_DB", ""),
    r"C:\Users\muham\Works\Airtel_analysis\Data\raw\airtel.db",
    "airtel.db",
    "Data/raw/airtel.db",
    "data/raw/airtel.db",
]

DATE_CANDIDATES = [
    "churn_date", "exit_date", "deactivation_date",
    "disconnection_date", "left_date",
]

REQUIRED = {
    "circle_name", "region", "connection_type", "tenure_years",
    "is_churned", "unresolved_count", "complaint_count", "ab_group",
}

C = {
    "red": "#E31B36",
    "gold": "#D59B35",
    "red_soft": "#FDECEF",
    "blue": "#2F6FA8",
    "blue_soft": "#EAF2FA",
    "teal": "#2E8B8A",
    "grey": "#9AA7B4",
    "green": "#1F8A5B",
    "ink": "#111827",
    "muted": "#6B7785",
    "line": "#E3E9F0",
    "canvas": "#F4F6FA",
    "white": "#FFFFFF",
}

# Streamlit >= 1.50 replaced use_container_width with width="stretch"
_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}


# ---------------------------- STYLE --------------------------

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    html, body, .stApp, [data-testid="stSidebar"] * {{
        font-family: 'DM Sans', sans-serif;
    }}
    .stApp {{ background: {C['canvas']}; color: {C['ink']}; }}

    /* leave room for Streamlit's top toolbar so the header is never clipped */
    .block-container {{
        max-width: 100%;
        padding: 3.4rem 1.6rem 1.2rem 1.6rem;
    }}
    header[data-testid="stHeader"] {{ background: transparent; }}

    /* ---------- sidebar ---------- */
    [data-testid="stSidebar"] {{
        background: {C['white']};
        border-right: 1px solid {C['line']};
    }}
    [data-testid="stSidebar"] label p {{
        font-size: 12px; font-weight: 700; color: {C['ink']};
        text-transform: uppercase; letter-spacing: .5px;
    }}
    /* light inputs even if the browser/OS forces a dark theme */
    [data-baseweb="select"] > div {{
        background: {C['white']} !important;
        border: 1px solid {C['line']} !important;
        color: {C['ink']} !important;
        border-radius: 8px !important;
    }}
    [data-baseweb="select"] * {{ color: {C['ink']} !important; }}
    [data-testid="stSidebar"] .stButton button {{
        background: {C['white']}; color: {C['ink']};
        border: 1px solid {C['line']}; border-radius: 8px; font-weight: 600;
    }}
    [data-testid="stSidebar"] .stButton button:hover {{
        border-color: {C['red']}; color: {C['red']};
    }}

    .brand {{ display:flex; align-items:center; gap:10px; padding: 2px 0 14px 0; }}
    .brand-mark {{
        width:34px; height:34px; border-radius:9px; background:{C['red']};
        color:#fff; display:flex; align-items:center; justify-content:center;
        font-size:18px; font-weight:700;
    }}
    .brand-name {{ font-size:16px; font-weight:700; color:{C['ink']}; line-height:1.1; }}
    .brand-sub {{ font-size:9px; font-weight:700; letter-spacing:1.2px; color:{C['muted']}; margin-top:3px; }}
    .side-note {{ font-size:11px; color:{C['muted']}; line-height:1.5; }}

    /* ---------- header ---------- */
    .page-header {{
        background: linear-gradient(110deg, #FFFFFF 0%, #FFFFFF 55%, {C['red_soft']} 100%);
        border: 1px solid {C['line']};
        border-left: 5px solid {C['red']};
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 12px;
        display:flex; align-items:center; justify-content:space-between;
        box-shadow: 0 1px 3px rgba(16,24,40,.05);
    }}
    .eyebrow {{ color:{C['red']}; font-size:10px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; }}
    .page-title {{ color:{C['ink']}; font-size:23px; font-weight:700; letter-spacing:-.4px; margin:2px 0 0 0; line-height:1.2; }}
    .page-subtitle {{ color:{C['muted']}; font-size:12px; margin-top:3px; }}
    .header-pill {{
        background:{C['blue_soft']}; color:{C['blue']}; border-radius:20px;
        padding:6px 12px; font-size:11px; font-weight:700; white-space:nowrap;
    }}

    /* ---------- KPI cards ---------- */
    .kpi {{
        background:{C['white']}; border:1px solid {C['line']};
        border-top: 3px solid var(--accent, {C['blue']});
        border-radius:12px; padding:11px 16px 10px 16px;
        box-shadow: 0 1px 3px rgba(16,24,40,.05); min-height: 92px;
    }}
    .kpi-label {{ font-size:10.5px; font-weight:700; letter-spacing:.7px; text-transform:uppercase; color:{C['muted']}; }}
    .kpi-value {{ font-size:27px; font-weight:700; color:{C['ink']}; line-height:1.25; letter-spacing:-.5px; }}
    .kpi-sub {{ font-size:11.5px; font-weight:600; color:{C['muted']}; }}
    .kpi-sub.bad {{ color:{C['red']}; }}
    .kpi-sub.good {{ color:{C['green']}; }}

    /* ---------- chart + insight cards ---------- */
    div[data-testid="stPlotlyChart"] {{
        background:{C['white']}; border:1px solid {C['line']};
        border-radius:12px; padding:4px 6px;
        box-shadow: 0 1px 3px rgba(16,24,40,.05);
    }}
    .insight-card {{
        background:{C['white']}; border:1px solid {C['line']}; border-radius:12px;
        padding:12px 16px; box-shadow: 0 1px 3px rgba(16,24,40,.05);
    }}
    .insight-title {{ font-size:13px; font-weight:700; color:{C['ink']}; margin-bottom:6px; }}
    .insight-row {{
        font-size:12px; color:{C['ink']}; line-height:1.45;
        padding:6px 0; border-top: 1px solid {C['line']};
    }}
    .insight-row:first-of-type {{ border-top:none; }}
    .dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; }}

    /* ---------- tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {{ gap:22px; border-bottom:1px solid {C['line']}; }}
    .stTabs [data-baseweb="tab"] {{ padding:8px 2px; font-size:13px; font-weight:700; color:{C['muted']}; }}
    .stTabs [aria-selected="true"] {{ color:{C['red']} !important; }}
    .stTabs [data-baseweb="tab-highlight"] {{ background-color:{C['red']}; }}

    .provenance {{
        color:{C['muted']}; border-top:1px solid {C['line']};
        padding-top:8px; margin-top:12px; font-size:11px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------ DATABASE HELPERS -------------------

def resolve_db_path():
    for candidate in DB_CANDIDATES:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return None


DB_PATH = resolve_db_path()


def qi(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def db_connection():
    return sqlite3.connect(str(DB_PATH), timeout=30)


@st.cache_data(show_spinner=False)
def read_sql(query: str, params: tuple = ()) -> pd.DataFrame:
    with db_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def inspect_schema():
    with db_connection() as conn:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'",
            conn,
        )["name"].tolist()
        if TABLE_NAME not in tables:
            raise RuntimeError(
                f"Table '{TABLE_NAME}' was not found. "
                f"Available: {', '.join(tables) or 'none'}"
            )
        schema = conn.execute(f"PRAGMA table_info({qi(TABLE_NAME)})").fetchall()
    return {row[1] for row in schema}


def where_clause(connection_type="All", region="All", circle=None, extra=None):
    clauses, params = [], []
    if connection_type != "All":
        clauses.append("connection_type = ?")
        params.append(connection_type)
    if region != "All":
        clauses.append("region = ?")
        params.append(region)
    if circle is not None:
        clauses.append("circle_name = ?")
        params.append(circle)
    if extra:
        clauses.append(extra)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, tuple(params)


def get_options(column):
    df = read_sql(
        f"SELECT DISTINCT {qi(column)} AS value FROM {qi(TABLE_NAME)} "
        f"WHERE {qi(column)} IS NOT NULL ORDER BY value"
    )
    return df["value"].tolist()


CHURN_AGG = """
    COUNT(*) AS subscribers,
    COALESCE(SUM(CASE WHEN is_churned = 1 THEN 1 ELSE 0 END), 0) AS left_count,
    ROUND(100.0 * SUM(CASE WHEN is_churned = 1 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 2) AS churn_rate
"""


# -------------------------- SQL METRICS ----------------------

def get_overall():
    """Whole-base numbers. Used as the fixed benchmark everywhere."""
    return read_sql(f"SELECT {CHURN_AGG} FROM {qi(TABLE_NAME)}").iloc[0]


def get_filtered_summary(connection_type, region, circle=None):
    where, params = where_clause(connection_type, region, circle)
    return read_sql(
        f"""
        SELECT {CHURN_AGG},
            COALESCE(SUM(CASE WHEN unresolved_count > 0 THEN 1 ELSE 0 END), 0)
                AS open_ticket_subscribers,
            ROUND(100.0 * SUM(CASE WHEN unresolved_count > 0 THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0), 2) AS open_ticket_pct
        FROM {qi(TABLE_NAME)} {where}
        """,
        params,
    ).iloc[0]


def get_experiment_result():
    df = read_sql(
        f"""
        SELECT UPPER(TRIM(CAST(ab_group AS TEXT))) AS grp,
               COUNT(*) AS n,
               SUM(CASE WHEN is_churned = 1 THEN 1 ELSE 0 END) AS churned
        FROM {qi(TABLE_NAME)}
        WHERE UPPER(TRIM(CAST(ab_group AS TEXT))) IN ('A', 'B')
        GROUP BY grp
        """
    )
    if set(df["grp"]) != {"A", "B"}:
        return None
    a = df[df["grp"] == "A"].iloc[0]
    b = df[df["grp"] == "B"].iloc[0]
    n_a, n_b, x_a, x_b = int(a["n"]), int(b["n"]), int(a["churned"]), int(b["churned"])
    if min(n_a, n_b) == 0:
        return None
    pooled = (x_a + x_b) / (n_a + n_b)
    se2 = pooled * (1 - pooled) * (1 / n_a + 1 / n_b)
    if se2 <= 0:
        return None
    z = (x_b / n_b - x_a / n_a) / math.sqrt(se2)
    # One-tailed test, H1: churn(B) < churn(A)
    p_value = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return {
        "p_value": p_value, "z": z,
        "rate_a": 100 * x_a / n_a, "rate_b": 100 * x_b / n_b,
    }


def grouped_churn(group_expr, alias, connection_type, region, circle=None,
                  order="ORDER BY 1", extra_select=""):
    where, params = where_clause(connection_type, region, circle)
    return read_sql(
        f"""
        SELECT {group_expr} AS {alias}{extra_select}, {CHURN_AGG}
        FROM {qi(TABLE_NAME)} {where}
        GROUP BY {group_expr}{', region' if extra_select else ''}
        {order}
        """,
        params,
    )


def get_tenure_data(connection_type, region, circle=None):
    return grouped_churn(
        "CAST(tenure_years AS INTEGER)", "tenure_years",
        connection_type, region, circle,
    )


def get_connection_data(connection_type, region, circle=None):
    return grouped_churn("connection_type", "connection_type",
                         connection_type, region, circle)


def get_region_data(connection_type):
    return grouped_churn("region", "region", connection_type, "All",
                         order="ORDER BY churn_rate DESC")


def get_circle_data(connection_type, region):
    return grouped_churn(
        "circle_name", "circle_name", connection_type, region,
        order="ORDER BY churn_rate DESC, circle_name",
        extra_select=", region",
    )


def get_complaint_data(connection_type, region, circle=None):
    where, params = where_clause(connection_type, region, circle)
    return read_sql(
        f"""
        SELECT
            CASE
                WHEN COALESCE(complaint_count, 0) = 0 THEN 'No complaints'
                WHEN COALESCE(unresolved_count, 0) > 0 THEN 'Open complaint ticket'
                ELSE 'All complaints resolved'
            END AS complaint_status,
            {CHURN_AGG}
        FROM {qi(TABLE_NAME)} {where}
        GROUP BY complaint_status
        """,
        params,
    )


def get_monthly_data(connection_type, region, circle, date_column):
    where, params = where_clause(
        connection_type, region, circle,
        extra=f"is_churned = 1 AND {qi(date_column)} IS NOT NULL",
    )
    return read_sql(
        f"""
        SELECT strftime('%Y-%m', {qi(date_column)}) AS month,
               COUNT(*) AS subscribers_left
        FROM {qi(TABLE_NAME)} {where}
        GROUP BY month
        ORDER BY month
        """,
        params,
    )


# -------------------------- CHART HELPERS --------------------

FONT = dict(family="DM Sans, Arial", size=11, color=C["ink"])


def base_layout(height, title):
    return dict(
        template="plotly_white",
        height=height,
        title=dict(text=f"<b>{title}</b>", font=dict(size=13, color=C["ink"]),
                   x=0.02, xanchor="left", y=0.96),
        font=FONT,
        paper_bgcolor=C["white"],
        plot_bgcolor=C["white"],
        margin=dict(l=48, r=22, t=44, b=44),
        hoverlabel=dict(bgcolor=C["ink"], font_color="#FFFFFF", font_size=11),
        showlegend=False,
        bargap=0.35,
    )


def polish_axes(fig, y_title="Churn rate"):
    fig.update_xaxes(showgrid=False, linecolor=C["line"],
                     tickfont=dict(size=10, color=C["ink"]),
                     title_font=dict(size=10, color=C["muted"]))
    fig.update_yaxes(showgrid=True, gridcolor="#EEF2F6", zeroline=False,
                     linecolor=C["line"], tickfont=dict(size=10, color=C["muted"]),
                     title_text=y_title,
                     title_font=dict(size=10, color=C["muted"]))
    return fig


HOVER = ("<b>%{x}</b><br>Churn: %{y:.2f}%<br>"
         "Subscribers: %{customdata[0]:,}<br>Left: %{customdata[1]:,}"
         "<extra></extra>")


def vbar(df, x_labels, colors, title, height, ref=None, ref_label=None, xtitle=""):
    """Vertical churn bars. Value labels sit inside the bar base so they
    never collide with the reference line."""
    rates = df["churn_rate"].astype(float)
    fig = go.Figure(go.Bar(
        x=x_labels, y=rates, marker_color=colors,
        marker_line_width=0,
        text=[f"{r:.1f}%" for r in rates],
        textposition="inside", insidetextanchor="start",
        textfont=dict(color="#FFFFFF", size=11, family="DM Sans, Arial"),
        customdata=df[["subscribers", "left_count"]].to_numpy(),
        hovertemplate=HOVER,
    ))
    top = max(rates.max(), ref or 0) * 1.22
    if ref is not None:
        fig.add_hline(
            y=ref, line_dash="dash", line_color=C["ink"], line_width=1.1,
            annotation_text=ref_label, annotation_position="top right",
            annotation_font=dict(size=10, color=C["ink"]),
        )
    fig.update_layout(**base_layout(height, title))
    fig.update_xaxes(title_text=xtitle)
    fig.update_yaxes(ticksuffix="%", range=[0, top])
    return polish_axes(fig)


def above_below(rates, ref):
    return [C["red"] if r > ref else C["blue"] for r in rates]


def tenure_chart(df, title, ref, ref_label, height):
    labels = [
        ("<1 yr" if int(t) == 0 else f"{int(t)} yr{'s' if int(t) > 1 else ''}")
        + f"<br><span style='color:{C['muted']};font-size:9px'>n={int(n):,}</span>"
        for t, n in zip(df["tenure_years"], df["subscribers"])
    ]
    return vbar(df, labels, above_below(df["churn_rate"], ref), title, height,
                ref, ref_label, "Completed years with Airtel")


def connection_chart(df, title, height, ref=None, ref_label=None):
    colors = [C["blue"] if str(v).lower() == "prepaid"
              else C["red"] if str(v).lower() == "postpaid" else C["teal"]
              for v in df["connection_type"]]
    labels = [f"{v}<br><span style='color:{C['muted']};font-size:9px'>n={int(n):,}</span>"
              for v, n in zip(df["connection_type"], df["subscribers"])]
    return vbar(df, labels, colors, title, height, ref, ref_label, "Connection type")


COMPLAINT_ORDER = ["No complaints", "All complaints resolved", "Open complaint ticket"]
COMPLAINT_SHORT = {
    "No complaints": "No complaints",
    "All complaints resolved": "All resolved",
    "Open complaint ticket": "Open ticket",
}
COMPLAINT_COLOR = {
    "No complaints": C["grey"],
    "All complaints resolved": C["blue"],
    "Open complaint ticket": C["red"],
}


def complaint_chart(df, title, height, ref=None, ref_label=None):
    df = df.copy()
    df["o"] = df["complaint_status"].map({k: i for i, k in enumerate(COMPLAINT_ORDER)})
    df = df.sort_values("o")
    colors = [COMPLAINT_COLOR.get(s, C["teal"]) for s in df["complaint_status"]]
    labels = [f"{COMPLAINT_SHORT.get(s, s)}<br>"
              f"<span style='color:{C['muted']};font-size:9px'>n={int(n):,}</span>"
              for s, n in zip(df["complaint_status"], df["subscribers"])]
    return vbar(df, labels, colors, title, height, ref, ref_label, "Complaint status")


def region_chart(df, title, height, ref, ref_label, selected):
    colors = [C["red"] if (selected != "All" and r == selected)
              else (C["blue"] if selected == "All" else C["grey"])
              for r in df["region"]]
    labels = [f"{r}<br><span style='color:{C['muted']};font-size:9px'>n={int(n):,}</span>"
              for r, n in zip(df["region"], df["subscribers"])]
    return vbar(df, labels, colors, title, height, ref, ref_label, "")


def circle_chart(df, national, height):
    ordered = df.sort_values("churn_rate", ascending=True)
    rates = ordered["churn_rate"].astype(float)
    fig = go.Figure(go.Bar(
        x=rates, y=ordered["circle_name"], orientation="h",
        marker_color=above_below(rates, national), marker_line_width=0,
        text=[f"{r:.1f}%" for r in rates],
        textposition="inside", insidetextanchor="end",
        textfont=dict(color="#FFFFFF", size=10, family="DM Sans, Arial"),
        customdata=ordered[["subscribers", "left_count", "region"]].to_numpy(),
        hovertemplate=("<b>%{y}</b> (%{customdata[2]})<br>Churn: %{x:.2f}%<br>"
                       "Subscribers: %{customdata[0]:,}<br>Left: %{customdata[1]:,}"
                       "<extra></extra>"),
    ))
    fig.add_vline(
        x=national, line_dash="dash", line_color=C["ink"], line_width=1.1,
        annotation_text=f"National {national:.2f}%", annotation_position="top",
        annotation_font=dict(size=10, color=C["ink"]),
    )
    fig.update_layout(**base_layout(height, "Circle churn ranking"))
    fig.update_layout(margin=dict(l=120, r=24, t=50, b=36), bargap=0.25)
    fig.update_xaxes(title_text="Churn rate", ticksuffix="%", rangemode="tozero")
    polish_axes(fig, "")
    fig.update_yaxes(showgrid=False, tickfont=dict(size=10, color=C["ink"]))
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F6")
    return fig


def monthly_chart(df, height):
    if df.empty:
        full = pd.DataFrame({"month": [], "subscribers_left": []})
    else:
        span = pd.period_range(df["month"].min(), df["month"].max(), freq="M")
        full = (pd.DataFrame({"month": span.strftime("%Y-%m")})
                .merge(df, on="month", how="left").fillna({"subscribers_left": 0}))
    full["subscribers_left"] = full["subscribers_left"].astype(int)
    full["label"] = pd.to_datetime(full["month"] + "-01").dt.strftime("%b %Y") \
        if not full.empty else []
    peak = full["subscribers_left"].max() if not full.empty else 0
    colors = [C["red"] if v == peak and peak > 0 else C["blue"]
              for v in full["subscribers_left"]]
    fig = go.Figure(go.Bar(
        x=full["label"], y=full["subscribers_left"], marker_color=colors,
        text=[f"{v:,}" for v in full["subscribers_left"]],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=10, color=C["ink"]),
        hovertemplate="<b>%{x}</b><br>Left: %{y:,}<extra></extra>",
    ))
    fig.update_layout(**base_layout(height, "Monthly subscriber losses"))
    fig.update_yaxes(rangemode="tozero", range=[0, max(peak * 1.2, 1)])
    return polish_axes(fig, "Subscribers left")


def render_chart(fig, key):
    st.plotly_chart(fig, config={"displayModeBar": False, "responsive": True},
                    key=key, **STRETCH)


# ------------------------- UI COMPONENTS ---------------------

def kpi(label, value, sub="", tone="", accent=None):
    style = f' style="--accent:{accent}"' if accent else ""
    st.markdown(
        f'<div class="kpi"{style}><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub {tone}">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def pts_tone(gap):
    """Higher churn than benchmark = bad (red), lower = good (green)."""
    if gap is None or pd.isna(gap) or abs(gap) < 0.05:
        return ""
    return "bad" if gap > 0 else "good"


def insights_card(circles, complaints, connections, tenure, national):
    rows = []

    if not circles.empty:
        top = circles.iloc[0]
        rows.append((C["red"],
            f"<b>{top['circle_name']}</b> has the highest churn at "
            f"<b>{top['churn_rate']:.1f}%</b> "
            f"({top['churn_rate'] - national:+.1f} pts vs national)."))
        n_above = int((circles["churn_rate"] > national).sum())
        rows.append((C["gold"],
            f"<b>{n_above} of {len(circles)}</b> circles churn above the "
            f"{national:.2f}% national rate."))

    if not complaints.empty:
        c = complaints.set_index("complaint_status")["churn_rate"]
        if "Open complaint ticket" in c and "No complaints" in c:
            rows.append((C["red"],
                f"Subscribers with an <b>open ticket</b> churn "
                f"<b>{c['Open complaint ticket'] - c['No complaints']:+.1f} pts</b> "
                f"vs those with no complaints."))

    if len(connections) >= 2:
        hi = connections.sort_values("churn_rate", ascending=False).iloc[0]
        lo = connections.sort_values("churn_rate").iloc[0]
        rows.append((C["blue"],
            f"<b>{hi['connection_type']}</b> churns "
            f"{hi['churn_rate'] - lo['churn_rate']:.1f} pts more than "
            f"{lo['connection_type']}."))

    if not tenure.empty:
        t = tenure.sort_values("churn_rate", ascending=False).iloc[0]
        yrs = "under 1 year" if int(t["tenure_years"]) == 0 else f"{int(t['tenure_years'])} yr"
        rows.append((C["teal"],
            f"Churn peaks at tenure <b>{yrs}</b> ({t['churn_rate']:.1f}%)."))

    body = "".join(
        f'<div class="insight-row"><span class="dot" style="background:{col}"></span>{txt}</div>'
        for col, txt in rows
    ) or '<div class="insight-row">No data for the current filters.</div>'
    st.markdown(
        f'<div class="insight-card"><div class="insight-title">Key insights</div>{body}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------- STARTUP ------------------------

if DB_PATH is None:
    st.error(
        "Database file not found. Set the `AIRTEL_DB` environment variable, "
        "edit `DB_CANDIDATES` at the top of this file, or place `airtel.db` "
        "next to `app.py`."
    )
    st.stop()

try:
    AVAILABLE_COLUMNS = inspect_schema()
except Exception as exc:
    st.error(f"Unable to inspect the database: {exc}")
    st.stop()

missing = REQUIRED - AVAILABLE_COLUMNS
if missing:
    st.error("Missing required columns: " + ", ".join(sorted(missing)))
    st.stop()

date_column = next((c for c in DATE_CANDIDATES if c in AVAILABLE_COLUMNS), None)

try:
    connection_options = get_options("connection_type")
    region_options = get_options("region")
    overall = get_overall()
except Exception as exc:
    st.error(f"Unable to load base data: {exc}")
    st.stop()

NATIONAL = float(overall["churn_rate"])      # computed, not hard-coded
TOTAL_BASE = int(overall["subscribers"])


# ----------------------------- SIDEBAR -----------------------

st.sidebar.markdown(
    """
    <div class="brand">
        <div class="brand-mark">A</div>
        <div>
            <div class="brand-name">Airtel Analytics</div>
            <div class="brand-sub">RETENTION INTELLIGENCE</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_connection = st.sidebar.selectbox(
    "Connection type", ["All"] + connection_options, key="f_conn")
selected_region = st.sidebar.selectbox(
    "Region", ["All"] + region_options, key="f_region")
circles_shown = st.sidebar.selectbox(
    "Circles in ranking", ["Top 10", "Top 15", "All"], key="f_topn")

st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<div class="side-note"><b>Domain A · Retention</b><br>'
    f'National churn: {NATIONAL:.2f}%<br>Base: {TOTAL_BASE:,} subscribers<br><br>'
    f'Circle &amp; plan structures are real; records are synthetic.</div>',
    unsafe_allow_html=True,
)
st.sidebar.write("")
if st.sidebar.button("↻ Refresh data", **STRETCH):
    st.cache_data.clear()
    st.rerun()


# ------------------------------ HEADER -----------------------

filter_text = (
    f"{selected_connection} · {selected_region}"
    if (selected_connection != "All" or selected_region != "All")
    else "All subscribers"
)
st.markdown(
    f"""
    <div class="page-header">
        <div>
            <div class="eyebrow">Domain A / Retention Intelligence</div>
            <div class="page-title">Subscriber Retention Analytics</div>
            <div class="page-subtitle">Churn patterns, risk segments and circle priorities at a glance.</div>
        </div>
        <div class="header-pill">View: {filter_text}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, detail_tab = st.tabs(["Overview", "Circle detail"])


# ---------------------------- OVERVIEW -----------------------

with overview_tab:
    summary = get_filtered_summary(selected_connection, selected_region)
    experiment = get_experiment_result()
    rate = summary["churn_rate"]
    gap = (rate - NATIONAL) if pd.notna(rate) else None

    k1, k2, k3, k4, k5 = st.columns(5, gap="small")
    with k1:
        kpi("Subscribers in view", f"{int(summary['subscribers']):,}",
            f"of {TOTAL_BASE:,} total base", accent=C["blue"])
    with k2:
        kpi("Subscribers lost", f"{int(summary['left_count']):,}",
            "churned in observation window", accent=C["red"])
    with k3:
        kpi("Churn rate", f"{rate:.2f}%" if pd.notna(rate) else "N/A",
            f"{gap:+.2f} pts vs national" if gap is not None else "",
            pts_tone(gap), accent=C["red"])
    with k4:
        kpi("Open-ticket exposure",
            f"{summary['open_ticket_pct']:.1f}%" if pd.notna(summary["open_ticket_pct"]) else "N/A",
            f"{int(summary['open_ticket_subscribers']):,} subscribers", accent=C["teal"])
    with k5:
        if experiment:
            p = experiment["p_value"]
            kpi("A/B test p-value (1-tailed)", f"{p:.4f}",
                ("Significant: B lowers churn" if p < 0.05
                 else f"Not significant · A {experiment['rate_a']:.1f}% vs B {experiment['rate_b']:.1f}%"),
                "good" if p < 0.05 else "", accent=C["gold"])
        else:
            kpi("A/B test p-value (1-tailed)", "N/A", "Groups A/B not found")

    st.write("")

    tenure = get_tenure_data(selected_connection, selected_region)
    connection_data = get_connection_data(selected_connection, selected_region)
    complaint_data = get_complaint_data(selected_connection, selected_region)
    view_rate = float(rate) if pd.notna(rate) else NATIONAL

    c1, c2, c3 = st.columns([1.25, 0.85, 1.1], gap="small")
    with c1:
        if not tenure.empty:
            render_chart(tenure_chart(tenure, "Churn by tenure", view_rate,
                                      f"Avg {view_rate:.1f}%", 270), "ov_tenure")
    with c2:
        if not connection_data.empty:
            render_chart(connection_chart(connection_data, "Churn by connection", 270,
                                          view_rate, f"Avg {view_rate:.1f}%"), "ov_conn")
    with c3:
        if not complaint_data.empty:
            render_chart(complaint_chart(complaint_data, "Churn by complaint status", 270,
                                         view_rate, f"Avg {view_rate:.1f}%"), "ov_comp")

    st.write("")

    circles = get_circle_data(selected_connection, selected_region)
    region_data = get_region_data(selected_connection)

    left, right = st.columns([1.6, 1], gap="small")
    with left:
        if not circles.empty:
            n_show = {"Top 10": 10, "Top 15": 15}.get(circles_shown, len(circles))
            shown = circles.head(n_show)
            render_chart(circle_chart(shown, NATIONAL, 30 * len(shown) + 90),
                         "ov_circles")
    with right:
        if not region_data.empty:
            render_chart(region_chart(region_data, "Churn by region", 215,
                                      NATIONAL, f"National {NATIONAL:.1f}%",
                                      selected_region), "ov_region")
        st.write("")
        insights_card(circles, complaint_data, connection_data, tenure, NATIONAL)

    st.markdown(
        f'<div class="provenance">Source: SQLite · <b>{TABLE_NAME}</b>. '
        f'Red bars/line = above benchmark. A/B test and total base are always '
        f'computed on the full {TOTAL_BASE:,} subscribers; other figures follow the sidebar filters.</div>',
        unsafe_allow_html=True,
    )


# ------------------------- CIRCLE DETAIL ---------------------

with detail_tab:
    circle_df = get_circle_data(selected_connection, selected_region)

    if circle_df.empty:
        st.warning("No circles are available for the selected filters.")
    else:
        names = circle_df["circle_name"].tolist()
        churn_map = dict(zip(circle_df["circle_name"], circle_df["churn_rate"]))

        sel_col, _ = st.columns([1.2, 3])
        with sel_col:
            selected_circle = st.selectbox(
                "Circle (highest churn first)", names,
                format_func=lambda n: f"{n} · {churn_map[n]:.2f}%",
                key="detail_circle",
            )

        d = get_filtered_summary(selected_connection, selected_region, selected_circle)
        crate = d["churn_rate"]
        cgap = (crate - NATIONAL) if pd.notna(crate) else None
        rank = names.index(selected_circle) + 1

        k1, k2, k3, k4 = st.columns(4, gap="small")
        with k1:
            kpi("Circle subscribers", f"{int(d['subscribers']):,}",
                f"{int(d['left_count']):,} left", accent=C["blue"])
        with k2:
            kpi("Circle churn rate", f"{crate:.2f}%" if pd.notna(crate) else "N/A",
                f"{cgap:+.2f} pts vs national" if cgap is not None else "",
                pts_tone(cgap), accent=C["red"])
        with k3:
            kpi("Churn rank", f"#{rank} of {len(names)}",
                "1 = highest churn", accent=C["gold"])
        with k4:
            pct = d["open_ticket_pct"]
            kpi("Open-ticket subscribers", f"{int(d['open_ticket_subscribers']):,}",
                f"{pct:.1f}% of circle" if pd.notna(pct) else "", accent=C["teal"])

        st.write("")

        dt = get_tenure_data(selected_connection, selected_region, selected_circle)
        dc = get_complaint_data(selected_connection, selected_region, selected_circle)

        d1, d2, d3 = st.columns([1.15, 1.05, 1.15], gap="small")
        with d1:
            if not dt.empty:
                render_chart(tenure_chart(dt, f"{selected_circle} · churn by tenure",
                                          NATIONAL, f"National {NATIONAL:.1f}%", 290),
                             "det_tenure")
        with d2:
            if not dc.empty:
                render_chart(complaint_chart(dc, f"{selected_circle} · complaint status",
                                             290, NATIONAL, f"National {NATIONAL:.1f}%"),
                             "det_comp")
        with d3:
            if date_column:
                monthly = get_monthly_data(selected_connection, selected_region,
                                           selected_circle, date_column)
                render_chart(monthly_chart(monthly, 290), "det_monthly")
            else:
                st.info("No churn-date column found, so the monthly trend is unavailable.")