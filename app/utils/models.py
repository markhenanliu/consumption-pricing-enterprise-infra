"""
STaaS deal economics model extracted from notebooks/04_deal_profitability.ipynb.
All inputs are illustrative, drawn from publicly available industry benchmarks.
"""

import numpy as np

# ── Vendor cost structure (per TB per month) ─────────────────────────
COGS_PER_TB    = 14.00
SUPPORT_PER_TB =  3.50
SALES_COST_PCT =  0.12
OVERHEAD_PCT   =  0.08

# ── Published list pricing ────────────────────────────────────────────
LIST_RATE  = 35.00
BURST_PREM =  0.40
AVG_BURST  =  0.15
WACC       =  0.10

# ── Segment price sensitivity (multiplier on list) ────────────────────
SEG_MULT: dict[str, float] = {
    'Healthcare / Life Sciences': 1.10,
    'Financial Services':         1.08,
    'Government / Federal':       0.95,
    'Manufacturing / Industrial': 1.00,
    'Media & Entertainment':      0.97,
    'Technology / Cloud-Native':  0.88,
}

# ── Volume discount curve (committed TB → discount from segment list) ─
VOL_DISC: dict[int, float] = {
       50: 0.00,
      100: 0.03,
      250: 0.07,
      500: 0.12,
     1000: 0.17,
     2000: 0.22,
     5000: 0.28,
}

# ── Competitive discount unlock ───────────────────────────────────────
COMP_DISC: dict[str, float] = {
    'None':                        0.00,
    'Pure Storage':                0.05,
    'HPE GreenLake':               0.04,
    'Dell APEX':                   0.03,
    'Hyperscaler (AWS/Azure/GCP)': 0.06,
}

# ── Contract term incentives ──────────────────────────────────────────
TERM_DISC: dict[int, float] = {1: 0.00, 2: 0.03, 3: 0.06, 4: 0.08, 5: 0.10}

# ── Other discount parameters ─────────────────────────────────────────
NEW_LOGO_DISC = 0.04

# ── Churn rates by customer type ──────────────────────────────────────
BASE_CHURN: dict[str, float] = {
    'New logo':  0.12,
    'Existing':  0.05,
    'Strategic': 0.02,
}

# ── Discount approval authority tiers ─────────────────────────────────
AUTH_TIERS: dict[str, float] = {
    'Rep (no approval)': 0.10,
    'Manager approval':  0.18,
    'Deal desk':         0.25,
    'VP approval':       0.32,
    'Executive (SVP+)':  0.40,
}


def get_vol_disc(tb: float) -> float:
    """Interpolate volume discount from the non-linear tier curve."""
    t = sorted(VOL_DISC.keys())
    if tb <= t[0]:  return VOL_DISC[t[0]]
    if tb >= t[-1]: return VOL_DISC[t[-1]]
    for i in range(len(t) - 1):
        lo, hi = t[i], t[i + 1]
        if lo <= tb <= hi:
            frac = (tb - lo) / (hi - lo)
            return VOL_DISC[lo] + frac * (VOL_DISC[hi] - VOL_DISC[lo])
    return 0.0  # unreachable


def get_approval(disc: float) -> str:
    """Map total discount fraction to required approval tier."""
    for tier, mx in AUTH_TIERS.items():
        if disc <= mx:
            return tier
    return 'Executive (SVP+)'


def compute_deal(
    committed_tb: float,
    segment: str,
    contract_years: int,
    competitor: str,
    is_new_logo: bool,
    rep_disc: float = 0.0,
    strategic: bool = False,
) -> dict:
    """
    Full deal economics engine.

    Discount stack (additive, capped at 40%):
        Volume + Competitive + Term + New Logo + Rep discretionary

    Returns a dict with pricing, P&L, NPV, win probability, and approval tier.
    """
    vd = get_vol_disc(committed_tb)
    sm = SEG_MULT[segment]
    cd = COMP_DISC[competitor]
    td = TERM_DISC[contract_years]
    ld = NEW_LOGO_DISC if is_new_logo else 0.0
    total_d = min(vd + cd + td + ld + rep_disc, 0.40)

    seg_list = LIST_RATE * sm
    eff      = seg_list * (1 - total_d)
    burst_r  = eff * (1 + BURST_PREM)

    rev_yr       = committed_tb * (eff + AVG_BURST * burst_r) * 12
    comm_rev_yr  = committed_tb * eff * 12
    burst_rev_yr = committed_tb * AVG_BURST * burst_r * 12

    cogs_yr = committed_tb * (COGS_PER_TB + SUPPORT_PER_TB
                               + AVG_BURST * COGS_PER_TB * 0.4) * 12

    tcv = rev_yr * contract_years
    sc  = tcv * SALES_COST_PCT
    oh  = tcv * OVERHEAD_PCT

    gm  = rev_yr - cogs_yr
    net = tcv - cogs_yr * contract_years - sc - oh

    ct    = 'Strategic' if strategic else ('New logo' if is_new_logo else 'Existing')
    churn = BASE_CHURN[ct]
    sp    = [(1 - churn) ** yr for yr in range(1, contract_years + 1)]
    npv   = sum(
        (rev_yr - cogs_yr) * s / (1 + WACC) ** yr
        for yr, s in enumerate(sp, 1)
    ) - sc - oh

    be = (cogs_yr + (sc + oh) / contract_years) / (committed_tb * 12 * (1 + AVG_BURST))

    # Logistic S-curve: inflects at 10% below list (~50% win probability)
    wp = 1 / (1 + np.exp(8 * (eff / LIST_RATE - 0.90)))

    return dict(
        committed_tb=committed_tb, segment=segment, contract_years=contract_years,
        competitor=competitor, is_new_logo=is_new_logo,
        list_rate=LIST_RATE, seg_adj_list=seg_list, effective_rate=eff,
        burst_rate=burst_r, vol_disc=vd, comp_disc=cd, term_disc=td,
        logo_disc=ld, rep_disc=rep_disc, total_disc=total_d,
        committed_rev_yr=comm_rev_yr, burst_rev_yr=burst_rev_yr,
        total_rev_yr=rev_yr, total_tcv=tcv,
        cogs_yr=cogs_yr, sales_cost=sc, overhead=oh,
        gross_margin_yr=gm, gross_margin_pct=gm / rev_yr if rev_yr else 0,
        net_margin_tcv=net, net_margin_pct=net / tcv if tcv else 0,
        npv_net=npv, breakeven_rate=be,
        approval_tier=get_approval(total_d),
        win_prob=wp, churn_annual=churn,
    )
