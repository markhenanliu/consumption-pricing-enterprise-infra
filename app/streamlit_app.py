import streamlit as st

st.set_page_config(
    page_title="Consumption Pricing — Enterprise Infra",
    page_icon="💾",
    layout="wide",
)

st.title("Consumption Pricing Models for Enterprise Infrastructure")
st.caption("Home")
st.markdown(
    """
    Interactive companion to the four financial models in this repo.
    Use the sidebar to navigate between models.

    | Page | Model |
    |------|-------|
    | Deal Profitability | Model 4 — STaaS deal P&L, discount stack, win probability |

    > **Data note:** All inputs are illustrative, drawn from publicly available industry
    > benchmarks. No proprietary vendor data is used.
    """
)
