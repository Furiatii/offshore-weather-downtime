"""Offshore Weather Downtime Dashboard - Costa do RJ

Quantos dias o mar "fecha" na costa do Rio de Janeiro?
Análise de dados meteorológicos reais do INMET para estimar
janelas operacionais de atividades offshore.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from analysis.processor import load_all_stations, ms_to_knots, STATION_META
from analysis.thresholds import (
    OPERATIONS,
    calculate_downtime,
    daily_downtime_summary,
)

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Downtime Offshore - Costa RJ",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }

    /* Header */
    .header-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #0369A1 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    .header-container h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        color: white;
    }
    .header-container p {
        font-size: 1rem;
        opacity: 0.85;
        margin: 0;
        line-height: 1.5;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        flex: 1;
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
    }
    .metric-card .label {
        font-size: 0.85rem;
        color: #64748B;
        margin-top: 0.2rem;
    }
    .metric-card.highlight {
        border-color: #0369A1;
        background: #F0F9FF;
    }
    .metric-card.highlight .value {
        color: #0369A1;
    }
    .metric-card.warn .value {
        color: #DC2626;
    }

    /* Context boxes */
    .context-box {
        background: #F0F9FF;
        border-left: 4px solid #0369A1;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        line-height: 1.5;
        color: #334155;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #F8FAFC;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* Plotly charts bg */
    .js-plotly-plot .plotly .main-svg {
        border-radius: 12px;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data(show_spinner="Carregando dados do INMET...")
def load_data():
    df = load_all_stations(DATA_DIR)
    df = calculate_downtime(df)
    daily = daily_downtime_summary(df)
    return df, daily


try:
    hourly, daily = load_data()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

if hourly.empty:
    st.warning("Nenhum dado encontrado na pasta data/.")
    st.stop()

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <h1>Quantos dias o mar "fecha" na costa do RJ?</h1>
    <p>
        Análise de dados meteorológicos reais (INMET, 2019-2023) para estimar
        janelas de downtime em operações offshore na Bacia de Campos e arredores.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtros")

    stations = sorted(daily["estacao"].unique())
    station_labels = {s: f"{s} - {STATION_META.get(s, {}).get('name', s)}" for s in stations}
    selected_stations = st.multiselect(
        "Estações",
        options=stations,
        default=stations,
        format_func=lambda x: station_labels[x],
    )

    years = sorted(daily["year"].unique())
    selected_years = st.multiselect(
        "Anos", options=years, default=years
    )

    operation_names = list(OPERATIONS.keys())
    selected_op = st.selectbox(
        "Operação de referência",
        options=operation_names,
        index=0,
        help="Cada tipo de operação tem limites de vento e chuva diferentes.",
    )

    st.markdown("---")
    st.markdown("### Limites operacionais")
    limits = OPERATIONS[selected_op]
    st.markdown(f"**{selected_op}**")
    st.markdown(f"- Vento: {limits['vento_max_ms']:.1f} m/s ({ms_to_knots(limits['vento_max_ms']):.0f} kt)")
    st.markdown(f"- Rajada: {limits['rajada_max_ms']:.1f} m/s ({ms_to_knots(limits['rajada_max_ms']):.0f} kt)")
    st.markdown(f"- Chuva: {limits['chuva_max_mm']:.0f} mm/h")

    st.markdown("---")
    st.markdown(
        "<small>Dados: INMET (estações automáticas)<br>"
        "Limites: NORMAM-01 / Noble Denton</small>",
        unsafe_allow_html=True,
    )

# ── Filter data ──────────────────────────────────────────────
mask_d = daily["estacao"].isin(selected_stations) & daily["year"].isin(selected_years)
filtered_daily = daily[mask_d].copy()

mask_h = hourly["estacao"].isin(selected_stations) & hourly["datetime"].dt.year.isin(selected_years)
filtered_hourly = hourly[mask_h].copy()

dt_col = f"downtime_{selected_op}"
dt_day_col = f"downtime_{selected_op}_day"

if filtered_daily.empty:
    st.warning("Nenhum dado com os filtros selecionados.")
    st.stop()

# ── Key metrics ──────────────────────────────────────────────
total_days = filtered_daily.groupby(["estacao", "date"]).first().shape[0]
downtime_days = filtered_daily[filtered_daily[dt_day_col] == True].shape[0]
pct_downtime = (downtime_days / total_days * 100) if total_days > 0 else 0
avg_wind = filtered_hourly["vento_vel_ms"].mean()
max_gust = filtered_hourly["vento_rajada_ms"].max()

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="value">{total_days:,}</div>
        <div class="label">Dias analisados (estação-dia)</div>
    </div>
    <div class="metric-card warn">
        <div class="value">{downtime_days:,}</div>
        <div class="label">Dias com downtime ({selected_op})</div>
    </div>
    <div class="metric-card highlight">
        <div class="value">{pct_downtime:.1f}%</div>
        <div class="label">Taxa de downtime</div>
    </div>
    <div class="metric-card">
        <div class="value">{avg_wind:.1f} m/s</div>
        <div class="label">Vento médio ({ms_to_knots(avg_wind):.0f} kt)</div>
    </div>
    <div class="metric-card">
        <div class="value">{max_gust:.1f} m/s</div>
        <div class="label">Rajada máxima ({ms_to_knots(max_gust):.0f} kt)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Context ──────────────────────────────────────────────────
st.markdown(f"""
<div class="context-box">
    <strong>O que isso significa?</strong> Um dia conta como "downtime" quando pelo menos 4 horas
    naquele dia excederam os limites para <em>{selected_op}</em>.
    Vento sustentado acima de {ms_to_knots(limits['vento_max_ms']):.0f} nós,
    rajadas acima de {ms_to_knots(limits['rajada_max_ms']):.0f} nós ou
    precipitação acima de {limits['chuva_max_mm']:.0f} mm/h já inviabilizam a operação.
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Sazonalidade",
    "Por Estação",
    "Série Temporal",
    "Comparativo de Operações",
])

# ── Colors ───────────────────────────────────────────────────
NAVY = "#0F172A"
ACCENT = "#0369A1"
RED = "#DC2626"
COLORS = px.colors.qualitative.Set2

MONTH_NAMES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

# ── Tab 1: Sazonalidade ─────────────────────────────────────
with tab1:
    st.markdown("### Downtime mensal ao longo do ano")
    st.markdown("""
    <div class="context-box">
        Em quais meses o mar mais "fecha"? Esse gráfico mostra a taxa média de downtime
        por mês, agrupando todos os anos e estações selecionadas. Útil para planejar janelas de manutenção
        e campanhas de mergulho.
    </div>
    """, unsafe_allow_html=True)

    # Monthly downtime rate
    monthly = filtered_daily.groupby("month").agg(
        total_days=("date", "count"),
        downtime_days=(dt_day_col, "sum"),
    ).reset_index()
    monthly["pct"] = (monthly["downtime_days"] / monthly["total_days"] * 100).round(1)
    monthly["month_name"] = monthly["month"].map(MONTH_NAMES_PT)

    fig_season = go.Figure()
    fig_season.add_trace(go.Bar(
        x=monthly["month_name"],
        y=monthly["pct"],
        marker_color=[RED if v > pct_downtime else ACCENT for v in monthly["pct"]],
        text=[f"{v:.1f}%" for v in monthly["pct"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Downtime: %{y:.1f}%<extra></extra>",
    ))
    fig_season.update_layout(
        yaxis_title="% de dias com downtime",
        xaxis_title="",
        plot_bgcolor="white",
        height=420,
        margin=dict(t=20, b=40),
        yaxis=dict(gridcolor="#E2E8F0"),
    )
    st.plotly_chart(fig_season, use_container_width=True)

    # Avg hours of downtime per day by month
    st.markdown("### Horas médias de downtime por dia (por mês)")
    monthly_hours = filtered_daily.groupby("month")[dt_col].mean().reset_index()
    monthly_hours["month_name"] = monthly_hours["month"].map(MONTH_NAMES_PT)

    fig_hours = go.Figure()
    fig_hours.add_trace(go.Scatter(
        x=monthly_hours["month_name"],
        y=monthly_hours[dt_col],
        mode="lines+markers",
        line=dict(color=ACCENT, width=3),
        marker=dict(size=10, color=ACCENT),
        fill="tozeroy",
        fillcolor="rgba(3, 105, 161, 0.1)",
        hovertemplate="<b>%{x}</b><br>Média: %{y:.1f}h<extra></extra>",
    ))
    fig_hours.update_layout(
        yaxis_title="Horas de downtime / dia",
        xaxis_title="",
        plot_bgcolor="white",
        height=350,
        margin=dict(t=20, b=40),
        yaxis=dict(gridcolor="#E2E8F0"),
    )
    st.plotly_chart(fig_hours, use_container_width=True)

# ── Tab 2: Por Estação ──────────────────────────────────────
with tab2:
    st.markdown("### Downtime por estação meteorológica")
    st.markdown("""
    <div class="context-box">
        Qual trecho da costa é mais crítico? As estações vão de Marambaia (Sul/RJ) até
        São Tomé (Norte Fluminense, coração da Bacia de Campos). Cada região tem um
        perfil de vento diferente.
    </div>
    """, unsafe_allow_html=True)

    by_station = filtered_daily.groupby(["estacao", "local"]).agg(
        total_days=("date", "count"),
        downtime_days=(dt_day_col, "sum"),
        avg_wind=("vento_vel_ms", "mean"),
        max_gust=("vento_rajada_ms", "max"),
    ).reset_index()
    by_station["pct"] = (by_station["downtime_days"] / by_station["total_days"] * 100).round(1)

    fig_station = go.Figure()
    fig_station.add_trace(go.Bar(
        x=by_station["local"],
        y=by_station["pct"],
        marker_color=COLORS[:len(by_station)],
        text=[f"{v:.1f}%" for v in by_station["pct"]],
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Downtime: %{y:.1f}%<br>"
            "<extra></extra>"
        ),
    ))
    fig_station.update_layout(
        yaxis_title="% de dias com downtime",
        xaxis_title="",
        plot_bgcolor="white",
        height=420,
        margin=dict(t=20, b=40),
        yaxis=dict(gridcolor="#E2E8F0"),
    )
    st.plotly_chart(fig_station, use_container_width=True)

    # Station map
    st.markdown("### Localização das estações")
    map_data = []
    for _, row in by_station.iterrows():
        meta = STATION_META.get(row["estacao"], {})
        map_data.append({
            "lat": meta.get("lat", 0),
            "lon": meta.get("lon", 0),
            "local": row["local"],
            "pct": row["pct"],
            "size": row["pct"] * 2 + 5,
        })
    map_df = pd.DataFrame(map_data)

    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        size="size",
        color="pct",
        hover_name="local",
        hover_data={"pct": ":.1f", "lat": False, "lon": False, "size": False},
        color_continuous_scale=["#0369A1", "#DC2626"],
        labels={"pct": "Downtime %"},
        zoom=6,
        center={"lat": -22.5, "lon": -42.5},
        mapbox_style="open-street-map",
        height=450,
    )
    fig_map.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_map, use_container_width=True)

    # Table
    st.markdown("### Resumo por estação")
    table = by_station[["estacao", "local", "total_days", "downtime_days", "pct", "avg_wind", "max_gust"]].copy()
    table.columns = ["Código", "Local", "Dias analisados", "Dias downtime", "% Downtime", "Vento médio (m/s)", "Rajada máx (m/s)"]
    table["Vento médio (m/s)"] = table["Vento médio (m/s)"].round(1)
    table["Rajada máx (m/s)"] = table["Rajada máx (m/s)"].round(1)
    st.dataframe(table, use_container_width=True, hide_index=True)

# ── Tab 3: Série Temporal ────────────────────────────────────
with tab3:
    st.markdown("### Evolução do downtime ao longo dos anos")
    st.markdown("""
    <div class="context-box">
        O downtime está piorando com o tempo? Esse gráfico mostra a taxa anual de downtime
        por estação. Tendências de aumento podem indicar mudanças climáticas impactando
        a operação offshore.
    </div>
    """, unsafe_allow_html=True)

    yearly = filtered_daily.groupby(["year", "estacao", "local"]).agg(
        total_days=("date", "count"),
        downtime_days=(dt_day_col, "sum"),
    ).reset_index()
    yearly["pct"] = (yearly["downtime_days"] / yearly["total_days"] * 100).round(1)

    fig_yearly = px.line(
        yearly,
        x="year",
        y="pct",
        color="local",
        markers=True,
        labels={"pct": "% Downtime", "year": "Ano", "local": "Estação"},
        height=420,
    )
    fig_yearly.update_layout(
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#E2E8F0"),
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig_yearly, use_container_width=True)

    # Heatmap: month x year
    st.markdown("### Heatmap: mês x ano")
    heat = filtered_daily.groupby(["year", "month"]).agg(
        total=("date", "count"),
        down=(dt_day_col, "sum"),
    ).reset_index()
    heat["pct"] = (heat["down"] / heat["total"] * 100).round(1)
    heat_pivot = heat.pivot(index="month", columns="year", values="pct").fillna(0)
    heat_pivot.index = heat_pivot.index.map(MONTH_NAMES_PT)

    fig_heat = px.imshow(
        heat_pivot,
        labels=dict(x="Ano", y="Mês", color="% Downtime"),
        color_continuous_scale=["#F0F9FF", "#0369A1", "#DC2626"],
        aspect="auto",
        height=400,
    )
    fig_heat.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Tab 4: Comparativo de Operações ─────────────────────────
with tab4:
    st.markdown("### Qual operação é mais afetada?")
    st.markdown("""
    <div class="context-box">
        Diferentes operações offshore têm diferentes limites de tolerância.
        Transferência de pessoal e mergulho param com ventos menores que
        içamentos com guindaste. Esse comparativo ajuda a priorizar quais operações
        planejar em quais meses.
    </div>
    """, unsafe_allow_html=True)

    # Calculate monthly downtime for ALL operations
    all_ops_data = []
    for op_name in OPERATIONS:
        op_dt_day = f"downtime_{op_name}_day"
        if op_dt_day not in filtered_daily.columns:
            continue
        monthly_op = filtered_daily.groupby("month").agg(
            total=("date", "count"),
            down=(op_dt_day, "sum"),
        ).reset_index()
        monthly_op["pct"] = (monthly_op["down"] / monthly_op["total"] * 100).round(1)
        monthly_op["operation"] = op_name
        monthly_op["month_name"] = monthly_op["month"].map(MONTH_NAMES_PT)
        all_ops_data.append(monthly_op)

    all_ops = pd.concat(all_ops_data, ignore_index=True)

    fig_ops = px.line(
        all_ops,
        x="month_name",
        y="pct",
        color="operation",
        markers=True,
        labels={"pct": "% Downtime", "month_name": "", "operation": "Operação"},
        height=450,
    )
    fig_ops.update_layout(
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#E2E8F0"),
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="top", y=-0.15),
    )
    st.plotly_chart(fig_ops, use_container_width=True)

    # Summary table for all ops
    st.markdown("### Taxa de downtime anual por operação")
    ops_summary = []
    for op_name in OPERATIONS:
        op_dt_day = f"downtime_{op_name}_day"
        if op_dt_day not in filtered_daily.columns:
            continue
        total = filtered_daily["date"].count()
        down = filtered_daily[op_dt_day].sum()
        ops_summary.append({
            "Operação": op_name,
            "Limite de vento": f"{OPERATIONS[op_name]['vento_max_ms']} m/s ({ms_to_knots(OPERATIONS[op_name]['vento_max_ms']):.0f} kt)",
            "Dias downtime": int(down),
            "% Downtime": f"{down/total*100:.1f}%",
        })
    st.dataframe(pd.DataFrame(ops_summary), use_container_width=True, hide_index=True)

# ── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 0.85rem; padding: 1rem 0;">
    Dados: INMET (estações automáticas costeiras do RJ, 2019-2023) |
    Limites operacionais: NORMAM-01 / Noble Denton |
    Desenvolvido por <a href="https://linkedin.com/in/gabrielfuriati" style="color: #0369A1;">Gabriel Furiati</a>
</div>
""", unsafe_allow_html=True)
