# AJVRE Multifamily Deal Analyzer v2.2.1 (Fixed for Streamlit Cloud)
import streamlit as st
from math import pow
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="AJVRE Analyzer", layout="wide")

LOAN_PRODUCTS = {
    "30-Year Fixed": {"term": 30, "io": False},
    "10/1 ARM": {"term": 30, "io": False},
    "7/1 ARM": {"term": 30, "io": False},
    "5/1 I/O": {"term": 30, "io": True},
}

def analyze_deal(
    purchase_price,
    down_payment_pct,
    rents,
    market_rents,
    use_market_rents,
    interest_rate,
    expense_ratio,
    vacancy_rate,
    loan_product,
    renovation_cost_per_unit,
    capex_total,
    mgmt_override,
    rent_growth_enabled,
    annual_rent_increase_pct
):
    units = len(rents)
    loan_info = LOAN_PRODUCTS[loan_product]
    loan_term_years = loan_info["term"]
    use_interest_only = loan_info["io"]

    applied_rents = market_rents if use_market_rents else rents
    gross_rent_annual = sum(applied_rents) * 12
    vacancy_loss = gross_rent_annual * vacancy_rate
    gross_operating_income = gross_rent_annual - vacancy_loss

    base_expenses = gross_operating_income * expense_ratio
    if mgmt_override:
        base_expenses += gross_operating_income * 0.08

    loan_amount = purchase_price * (1 - down_payment_pct)
    monthly_interest_rate = interest_rate / 12
    num_payments = loan_term_years * 12

    if use_interest_only:
        monthly_pi = loan_amount * monthly_interest_rate
    else:
        monthly_pi = loan_amount * (monthly_interest_rate * pow(1 + monthly_interest_rate, num_payments)) / (pow(1 + monthly_interest_rate, num_payments) - 1)

    annual_pi = monthly_pi * 12

    noi = gross_operating_income - base_expenses
    dscr = noi / annual_pi if annual_pi else 0
    cash_invested = purchase_price * down_payment_pct + (renovation_cost_per_unit * units) + capex_total
    annual_cash_flow = noi - annual_pi
    principal_paydown = 0 if use_interest_only else (annual_pi - (monthly_interest_rate * loan_amount * 12))

    cap_rate = noi / purchase_price if purchase_price else 0
    coc_return = annual_cash_flow / cash_invested if cash_invested else 0
    total_roi = (annual_cash_flow + principal_paydown) / cash_invested if cash_invested else 0
    breakeven_rent = (annual_pi + base_expenses) / (units * 12) if units else 0

    projections = []
    if rent_growth_enabled:
        current_rent = sum(applied_rents)
        rent_growth_rate = 1 + annual_rent_increase_pct
        for year in range(1, 11):
            future_rent = current_rent * (rent_growth_rate ** year)
            future_income = future_rent * 12 - (future_rent * 12 * vacancy_rate)
            future_expenses = future_income * expense_ratio
            if mgmt_override:
                future_expenses += future_income * 0.08
            future_noi = future_income - future_expenses
            future_cash_flow = future_noi - annual_pi
            future_dscr = future_noi / annual_pi
            projections.append({"Year": year, "DSCR": future_dscr, "Cash Flow": future_cash_flow})

    return {
        "NOI": noi,
        "DSCR": dscr,
        "Annual Cash Flow": annual_cash_flow,
        "Cap Rate": cap_rate,
        "CoC Return": coc_return,
        "Total ROI": total_roi,
        "Breakeven Rent/Unit": breakeven_rent,
        "Monthly P&I Only": monthly_pi,
        "Cash Invested": cash_invested,
        "Principal Paydown": principal_paydown,
        "Projections": projections
    }

# Streamlit UI
st.title("🏘 AJVRE Multifamily Deal Analyzer v2.2.1")

st.sidebar.header("📋 Deal Inputs")
purchase_price = st.sidebar.number_input("Purchase Price ($)", value=1000000, step=50000)

st.sidebar.subheader("💰 Down Payment")
down_payment_pct = st.sidebar.number_input("Down Payment %", min_value=0.0, max_value=1.0, value=0.25, step=0.01)
down_payment_dollars = purchase_price * down_payment_pct
st.sidebar.write(f"Down Payment Amount: ${down_payment_dollars:,.0f}")

interest_rate = st.sidebar.number_input("Interest Rate (%)", value=5.5, step=0.01) / 100
loan_product = st.sidebar.selectbox("Loan Product", list(LOAN_PRODUCTS.keys()))

st.sidebar.header("🏢 Income & Units")
num_units = st.sidebar.number_input("Number of Units", min_value=1, max_value=50, value=4)
use_market_rents = st.sidebar.radio("Use Current or Market Rents?", ["Current", "Market"], index=0) == "Market"

rents = []
market_rents = []
for i in range(int(num_units)):
    col1, col2 = st.sidebar.columns(2)
    with col1:
        rents.append(st.number_input(f"Unit {i+1} Rent", value=1500, step=50, key=f"rent_{i}"))
    with col2:
        market_rents.append(st.number_input(f"Market Rent", value=1800, step=50, key=f"market_rent_{i}"))

st.sidebar.header("💸 Expenses")
expense_ratio = st.sidebar.slider("Base Operating Expense Ratio", 0.2, 0.6, 0.3, step=0.01)
vacancy_rate = st.sidebar.slider("Vacancy Rate", 0.0, 0.1, 0.03, step=0.01)
mgmt_override = st.sidebar.checkbox("Add 8% Management Fee?", False)

st.sidebar.header("🔧 Renovation & CapEx")
renovation_cost_per_unit = st.sidebar.number_input("Renovation Cost Per Unit ($)", value=10000, step=1000)
capex_total = st.sidebar.number_input("Total Property CapEx ($)", value=15000, step=5000)

st.sidebar.header("📈 Rent Growth")
rent_growth_enabled = st.sidebar.checkbox("Enable Annual Rent Increase?", value=False)
annual_rent_increase_pct = 0.03
if rent_growth_enabled:
    annual_rent_increase_pct = st.sidebar.number_input("Annual Rent Increase %", value=3.0, step=0.25) / 100

results = analyze_deal(
    purchase_price,
    down_payment_pct,
    rents,
    market_rents,
    use_market_rents,
    interest_rate,
    expense_ratio,
    vacancy_rate,
    loan_product,
    renovation_cost_per_unit,
    capex_total,
    mgmt_override,
    rent_growth_enabled,
    annual_rent_increase_pct
)

st.header("📊 Results")
col1, col2, col3 = st.columns(3)
col1.metric("Net Operating Income (NOI)", f"${results['NOI']:,.0f}")
col2.metric("DSCR", f"{results['DSCR']:.2f}")
col3.metric("Cash Flow (Annual)", f"${results['Annual Cash Flow']:,.0f}")

col4, col5, col6 = st.columns(3)
col4.metric("Cap Rate", f"{results['Cap Rate']:.2%}")
col5.metric("Cash-on-Cash", f"{results['CoC Return']:.2%}")
col6.metric("Total ROI", f"{results['Total ROI']:.2%}")

st.subheader("📌 Additional Insights")
st.write(f"**Total Cash Invested:** ${results['Cash Invested']:,.0f}")
st.write(f"**Monthly Payment (P&I Only):** ${results['Monthly P&I Only']:,.0f}")
st.write(f"**Principal Paydown (Annual):** ${results['Principal Paydown']:,.0f}")
st.write(f"**Required Avg Rent/Unit to Break Even:** ${results['Breakeven Rent/Unit']:,.0f}")

if rent_growth_enabled and results['Projections']:
    st.subheader("📈 Profitability Over Time")
    df = pd.DataFrame(results['Projections'])
    fig, ax1 = plt.subplots()
    ax1.plot(df['Year'], df['Cash Flow'], label='Cash Flow ($)', color='blue', marker='o')
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Cash Flow ($)", color='blue')
    ax2 = ax1.twinx()
    ax2.plot(df['Year'], df['DSCR'], label='DSCR', color='green', marker='x')
    ax2.set_ylabel("DSCR", color='green')
    ax1.set_title("10-Year Projection: Cash Flow & DSCR")
    fig.tight_layout()
    st.pyplot(fig)
# Trigger Streamlit redeploy
