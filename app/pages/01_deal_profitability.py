import streamlit as st
import sys
from pathlib import Path
import numpy as np
import plotly.graph_objects as go

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.models import (
    SEG_MULT,
    COMP_DISC,
    TERM_DISC,
    LIST_RATE,
    WACC,
    AVG_BURST,
    BURST_PREM,
    compute_deal,
)

st.set_page_config(page_title="Deal Profitability", page_icon="📊", layout="wide")
st.title("Model 4 — STaaS Deal Profitability")
st.caption(
    "Enter deal parameters to compute the full P&L: discount stack, margins, "
    "NPV, win probability, and required approval tier."
)
st.markdown('<div class="dashboard-subtitle">Interactive deal dashboard</div>', unsafe_allow_html=True)

# ── Styling ───────────────────────────────────────────────────────────
st.markdown(
    """
<style>
:root {
  --bg: #F5F5F5;
  --card: #FFFFFF;
  --line: #D4D4D8;
  --text: #111111;
  --muted: #525252;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
  font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}
[data-testid="stAppViewContainer"] {
  background: linear-gradient(180deg, #FAFAFA 0%, #F3F4F6 100%);
}
.main .block-container {
  max-width: 1320px;
  padding-top: 1.2rem;
  padding-bottom: 2.2rem;
}
/* Center/nudge sidebar toggles inward (leave other widgets alone). */
section[data-testid="stSidebar"] [data-testid="stToggle"]{
  max-width: 280px;
  margin-left: auto;
  margin-right: auto;
}
.dashboard-subtitle {
  font-size: 1.02rem;
  color: #525252;
  margin: -0.15rem 0 0.65rem 0;
}
/* Keep headline KPIs visible while scrolling. */
.kpi-sticky-row {
  margin: 0.5rem 0 1rem 0;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
}
.kpi-card {
  background: var(--card);
  border: 1px solid #D4D4D8;
  border-radius: 0.8rem;
  padding: 0.95rem 0.95rem;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
}
.kpi-card.rate { border-top: 4px solid #111111; }
.kpi-card.discount { border-top: 4px solid #3F3F46; }
.kpi-card.gross { border-top: 4px solid #52525B; }
.kpi-card.net { border-top: 4px solid #71717A; }
.kpi-card.win { border-top: 4px solid #A1A1AA; }
.kpi-title {
  font-size: 1.02rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.55rem;
}
.kpi-label {
  font-size: 0.92rem;
  color: var(--muted);
  margin-bottom: 0.3rem;
}
.kpi-value {
  font-size: 1.72rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.15;
}
div[data-testid="stPlotlyChart"] {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: 0.9rem;
  padding: 0.4rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
div[data-testid="stDivider"] {
  margin: 0.9rem 0 1rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)


def section_header(text: str, *, color: str) -> None:
    st.markdown(
        f"""
<div style="
  font-weight: 700;
  font-size: 1.04rem;
  line-height: 1.2;
  margin: 0.15rem 0 0.65rem 0;
  color: #111111;
  background: linear-gradient(90deg, #F3F4F6 0%, #FFFFFF 95%);
  border: 1px solid #D4D4D8;
  border-left: 5px solid #52525B;
W  border-radius: 0.65rem;
  padding: 0.45rem 0.65rem;
">
  {text}
</div>
""",
        unsafe_allow_html=True,
    )


# ── Sidebar inputs ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Deal Parameters")

    segment = st.selectbox(
        "Customer segment",
        options=list(SEG_MULT.keys()),
        index=0,
    )

    committed_tb = st.number_input(
        "Committed storage (TB)",
        min_value=10,
        max_value=10_000,
        value=500,
        step=50,
    )

    contract_years = st.selectbox(
        "Contract length (years)",
        options=list(TERM_DISC.keys()),
        index=2,  # default: 3 years
    )

    competitor = st.selectbox(
        "Competitor in deal",
        options=list(COMP_DISC.keys()),
        index=0,
    )

    is_new_logo = st.toggle("New logo (vs. existing customer)", value=True)

    rep_disc = st.slider(
        "Rep discretionary discount (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
    ) / 100.0

    strategic = st.toggle(
        "Strategic account (2% churn rate)",
        value=False,
        disabled=is_new_logo,
    )

# ── Compute ───────────────────────────────────────────────────────────
deal = compute_deal(
    committed_tb=committed_tb,
    segment=segment,
    contract_years=contract_years,
    competitor=competitor,
    is_new_logo=is_new_logo,
    rep_disc=rep_disc,
    strategic=strategic and not is_new_logo,
)

# ── KPI row ───────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="kpi-sticky-row">
  <div class="kpi-title">Executive snapshot</div>
  <div class="kpi-grid">
    <div class="kpi-card rate">
      <div class="kpi-label">Effective rate</div>
      <div class="kpi-value">${deal['effective_rate']:.2f}/TB/mo</div>
    </div>
    <div class="kpi-card discount">
      <div class="kpi-label">Total discount</div>
      <div class="kpi-value">{deal['total_disc'] * 100:.1f}%</div>
    </div>
    <div class="kpi-card gross">
      <div class="kpi-label">Gross margin</div>
      <div class="kpi-value">{deal['gross_margin_pct'] * 100:.1f}%</div>
    </div>
    <div class="kpi-card net">
      <div class="kpi-label">Net margin (TCV)</div>
      <div class="kpi-value">{deal['net_margin_pct'] * 100:.1f}%</div>
    </div>
    <div class="kpi-card win">
      <div class="kpi-label">Win probability</div>
      <div class="kpi-value">{deal['win_prob'] * 100:.0f}%</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.divider()

# ── Approval badge ────────────────────────────────────────────────────
approval_color = {
    "Rep (no approval)": "green",
    "Manager approval":  "blue",
    "Deal desk":         "blue",
    "VP approval":       "orange",
    "Executive (SVP+)":  "red",
}.get(deal["approval_tier"], "gray")

st.markdown(
    f"**Approval required:** :{approval_color}[{deal['approval_tier']}]"
)

# ── Detail columns ────────────────────────────────────────────────────
col_stack, col_pl, col_signals = st.columns(3)

with col_stack:
    section_header("Discount stack", color="#7C3AED")
    # TODO: replace with a waterfall chart (e.g. plotly)
    st.write(f"Segment-adjusted list: **${deal['seg_adj_list']:.2f}**/TB/mo")
    st.write(f"Volume discount: **-{deal['vol_disc'] * 100:.1f}%**")
    st.write(f"Competitive discount: **-{deal['comp_disc'] * 100:.1f}%**")
    st.write(f"Term discount: **-{deal['term_disc'] * 100:.1f}%**")
    st.write(f"New-logo discount: **-{deal['logo_disc'] * 100:.1f}%**")
    st.write(f"Rep discretionary: **-{deal['rep_disc'] * 100:.1f}%**")
    st.write(f"**Total: -{deal['total_disc'] * 100:.1f}%  →  ${deal['effective_rate']:.2f}/TB/mo**")

with col_pl:
    section_header("Annual P&L", color="#2563EB")
    # TODO: replace with a stacked bar chart
    st.write(f"Committed revenue: **${deal['committed_rev_yr']:,.0f}**/yr")
    st.write(f"Burst revenue: **${deal['burst_rev_yr']:,.0f}**/yr")
    st.write(f"Total revenue: **${deal['total_rev_yr']:,.0f}**/yr")
    st.write(f"COGS: **-${deal['cogs_yr']:,.0f}**/yr")
    st.write(f"Gross margin: **${deal['gross_margin_yr']:,.0f}**/yr")
    st.divider()
    st.write(f"TCV ({contract_years} yr): **${deal['total_tcv']:,.0f}**")
    st.write(f"Sales cost: **-${deal['sales_cost']:,.0f}**")
    st.write(f"Overhead: **-${deal['overhead']:,.0f}**")
    st.write(f"Net margin: **${deal['net_margin_tcv']:,.0f}**")
    st.write(f"NPV (risk-adj): **${deal['npv_net']:,.0f}**")

with col_signals:
    section_header("Deal signals", color="#059669")
    # TODO: add win-prob vs. margin tradeoff chart
    st.write(f"Win probability: **{deal['win_prob'] * 100:.0f}%**")
    st.write(f"Annual churn: **{deal['churn_annual'] * 100:.0f}%**")
    st.write(f"Break-even rate: **${deal['breakeven_rate']:.2f}**/TB/mo")
    st.write(
        f"Margin buffer: **${deal['effective_rate'] - deal['breakeven_rate']:.2f}**/TB/mo "
        "above floor"
    )

st.divider()
section_header("Decision visuals", color="#DC2626")

# Shared chart data
discount_components = [
    ("Volume", -deal["seg_adj_list"] * deal["vol_disc"], deal["vol_disc"]),
    ("Competitive", -deal["seg_adj_list"] * deal["comp_disc"], deal["comp_disc"]),
    ("Term", -deal["seg_adj_list"] * deal["term_disc"], deal["term_disc"]),
    ("New logo", -deal["seg_adj_list"] * deal["logo_disc"], deal["logo_disc"]),
    ("Rep discretionary", -deal["seg_adj_list"] * deal["rep_disc"], deal["rep_disc"]),
]
non_zero_components = [c for c in discount_components if abs(c[1]) > 1e-6]
discount_labels = ["Segment list"] + [c[0] for c in non_zero_components] + ["Effective rate"]
discount_steps = [deal["seg_adj_list"]] + [c[1] for c in non_zero_components] + [0]
total_disc_sweep = np.linspace(0.0, 0.40, 81)
tradeoff_points = []
for total_disc in total_disc_sweep:
    effective_rate = deal["seg_adj_list"] * (1 - float(total_disc))
    burst_rate = effective_rate * (1 + BURST_PREM)
    rev_yr = committed_tb * (effective_rate + AVG_BURST * burst_rate) * 12
    tcv = rev_yr * contract_years
    sales_cost = tcv * 0.12
    overhead = tcv * 0.08
    net_margin_pct = (tcv - deal["cogs_yr"] * contract_years - sales_cost - overhead) / tcv if tcv else 0
    win_prob = 1 / (1 + np.exp(8 * (effective_rate / LIST_RATE - 0.90)))
    tradeoff_points.append((total_disc, net_margin_pct * 100, win_prob * 100))
discount_axis = np.linspace(0.05, 0.40, 15)
churn_axis = np.linspace(0.02, 0.15, 15)
npv_grid = []
for churn in churn_axis:
    row = []
    for total_disc in discount_axis:
        eff_rate = deal["seg_adj_list"] * (1 - total_disc)
        burst_rate = eff_rate * (1 + BURST_PREM)
        rev_yr = committed_tb * (eff_rate + AVG_BURST * burst_rate) * 12
        tcv = rev_yr * contract_years
        sales_cost = tcv * 0.12
        overhead = tcv * 0.08
        survival = [(1 - churn) ** yr for yr in range(1, contract_years + 1)]
        npv = (
            sum(
                (rev_yr - deal["cogs_yr"]) * s / (1 + WACC) ** yr
                for yr, s in enumerate(survival, 1)
            )
            - sales_cost
            - overhead
        )
        row.append(npv)
    npv_grid.append(row)
volume_axis = [50, 100, 250, 500, 1000, 2000, 5000]
segment_axis = list(SEG_MULT.keys())
price_grid = []
for seg_name in segment_axis:
    seg_row = []
    for vol in volume_axis:
        matrix_deal = compute_deal(
            committed_tb=vol,
            segment=seg_name,
            contract_years=contract_years,
            competitor=competitor,
            is_new_logo=is_new_logo,
            rep_disc=rep_disc,
            strategic=strategic and not is_new_logo,
        )
        seg_row.append(matrix_deal["effective_rate"])
    price_grid.append(seg_row)

st.caption("How price is constructed")
pricing_viz_left, pricing_viz_right = st.columns(2)

with pricing_viz_left:
    waterfall_measure = ["absolute"] + ["relative"] * len(non_zero_components) + ["total"]
    waterfall_text = [""] * len(discount_steps)
    waterfall_text[0] = f"${deal['seg_adj_list']:.2f}"
    waterfall_text[-1] = f"${deal['effective_rate']:.2f}"
    waterfall = go.Figure(
        go.Waterfall(
            name="Rate components",
            orientation="v",
            measure=waterfall_measure,
            x=discount_labels,
            y=discount_steps,
            text=waterfall_text,
            textposition="outside",
            connector={"line": {"color": "rgba(120,120,120,0.6)"}},
            decreasing={"marker": {"color": "#9CA3AF"}},
            increasing={"marker": {"color": "#71717A"}},
            totals={"marker": {"color": "#111111"}},
        )
    )
    waterfall.update_layout(
        title="Each discount step compounds into the final effective rate",
        yaxis_title="Monthly rate ($/TB)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=380,
    )
    st.plotly_chart(waterfall, use_container_width=True)

with pricing_viz_right:
    matrix = go.Figure(
        data=go.Heatmap(
            z=price_grid,
            x=volume_axis,
            y=segment_axis,
            colorscale="Blues",
            colorbar=dict(title="Effective rate ($/TB/mo)"),
            hovertemplate=(
                "Segment: %{y}<br>Volume: %{x} TB<br>Eff rate: $%{z:.2f}/TB/mo<extra></extra>"
            ),
        )
    )
    matrix.update_layout(
        title="Segment and volume materially shift realized price",
        xaxis_title="Committed volume (TB)",
        yaxis_title="Customer segment",
        margin=dict(l=20, r=20, t=50, b=20),
        height=380,
    )
    st.plotly_chart(matrix, use_container_width=True)

st.caption("Outcome and risk")
outcome_viz_left, outcome_viz_right = st.columns(2)

with outcome_viz_left:
    tradeoff = go.Figure()
    tradeoff.add_trace(
        go.Scatter(
            x=[p[1] for p in tradeoff_points],
            y=[p[2] for p in tradeoff_points],
            mode="lines+markers",
            name="Total discount sweep (0% to 40%)",
            line=dict(color="#7C3AED", width=3),
            marker=dict(size=5),
            hovertemplate="Net margin: %{x:.1f}%<br>Win prob: %{y:.1f}%<extra></extra>",
        )
    )
    tradeoff.add_trace(
        go.Scatter(
            x=[deal["net_margin_pct"] * 100],
            y=[deal["win_prob"] * 100],
            mode="markers",
            name="Current deal",
            marker=dict(color="#DC2626", size=11, symbol="diamond"),
            hovertemplate="Current deal<br>Net margin: %{x:.1f}%<br>Win prob: %{y:.1f}%<extra></extra>",
        )
    )
    tradeoff.update_layout(
        title="Discounting wins deals but erodes margin - gains flatten after deep cuts",
        xaxis_title="Net margin (% of TCV)",
        yaxis_title="Win probability (%)",
        yaxis=dict(range=[15, 95]),
        margin=dict(l=20, r=20, t=50, b=20),
        height=400,
    )
    st.plotly_chart(tradeoff, use_container_width=True)
    st.caption(
        "Assumption: win probability follows a logistic S-curve on effective rate vs list "
        f"(inflection at ~90% of list, slope=8). Current deal marker remains the live scenario."
    )

with outcome_viz_right:
    sensitivity = go.Figure(
        data=go.Heatmap(
            z=npv_grid,
            x=[d * 100 for d in discount_axis],
            y=[c * 100 for c in churn_axis],
            colorscale="RdYlGn",
            reversescale=False,
            colorbar=dict(title="NPV ($)"),
            hovertemplate="Discount: %{x:.1f}%<br>Churn: %{y:.1f}%<br>NPV: $%{z:,.0f}<extra></extra>",
        )
    )
    sensitivity.add_trace(
        go.Scatter(
            x=[deal["total_disc"] * 100],
            y=[deal["churn_annual"] * 100],
            mode="markers",
            marker=dict(color="#FFFFFF", size=16, symbol="diamond", line=dict(color="#111827", width=2.5)),
            name="Current assumption",
            hovertemplate="Current point<extra></extra>",
        )
    )
    sensitivity.update_layout(
        title="NPV is highly sensitive to discount-churn combinations",
        xaxis_title="Total discount (%)",
        yaxis_title="Annual churn (%)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=400,
    )
    st.plotly_chart(sensitivity, use_container_width=True)
