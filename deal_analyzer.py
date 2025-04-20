# AJVRE Multifamily Deal Analyzer v2.0
import streamlit as st
from math import pow

st.set_page_config(page_title="AJVRE Analyzer", layout="wide")

# -------------------- DEAL ANALYSIS FUNCTION -------------------- #
def analyze_deal(
    purchase_price,
    down_payment_pct,
    rents,
    market_rents,
    use_market_rents,
    interest_rate,
    impounds,
    expense_ratio,
    vacancy_rate,
    loan_term_years,
    tax_rate,
    insurance_annual,
    renovation_cost_per_unit,
    capex_total,
    use_interest_only,
    mgmt_override
):
    units = len(rents)

    # --- Income ---
    applied_rents = market_rents if use_market_rents else rents
    gross_rent_annual = sum(applied_rents) * 12
    vacancy_loss = gross_rent_annual * vacancy_rate
    gross_operating_income = gross_rent_annual - vacancy_loss

    # --- Expenses ---
    base_expenses = gross_operating_income * expense_ratio
    if mgmt_override:
        base_expenses += gross_operating_income * 0.08  # 8% mgmt fee override

    # --- Financing ---
    loan_amount = purchase_price * (1 - down_payment_pct)
    monthly_interest_rate = interest_rate / 12
    num_payments = loan_term_years * 12

    if use_interest_only:
        monthly_pi = loan_amount * monthly_interest_rate
    else:
        monthly_pi = loan_amount * (monthly_interest_rate * pow(1 + monthly_interest_rate, num_payments)) / (pow(1 + monthly_interest_rate, num_payments) - 1)

    annual_pi = monthly_pi * 12

    # --- Impounds ---
    annual_taxes = purchase_price * tax_rate
    monthly_impounds = (annual_taxes + insurance_annual) / 12 if impounds else 0
    monthly_total_payment = monthly_pi + monthly_impounds
    annual_total_payment = monthly_total_payment * 12

    # --- NOI, DSCR, Returns ---
    noi = gross_operating_income - base_expenses
    dscr = noi / annual_total_payment if annual_total_payment else 0

    cash_invested = purchase_price * down_payment_pct + (renovation_cost_per_unit * units) + capex_total
    annual_cash_flow = noi - annual_total_payment
    principal_paydown = 0 if use_interest_only else (annual_total_payment - (monthly_interest_rate * loan_amount * 12))

    cap_rate = noi / purchase_price if purchase_price else 0
    coc_return = annual_cash_flow / cash_invested if cash_invested else 0
    total_roi = (annual_cash_flow + principal_paydown) / cash_invested if cash_invested else 0

    breakeven_rent = (annual_total_payment + base_expenses) / (units * 12) if units else 0

    return {
        "NOI": noi,
        "DSCR": dscr,
        "Annual Cash Flow": annual_cash_flow,
        "Cap Rate": cap_rate,
        "CoC Return": coc_return,
        "Total ROI": total_roi,
        "Breakeven Rent/Unit": breakeven_rent,
        "Total Monthly Payment": monthly_total_payment,
        "Cash Invested": cash_invested,
        "Principal Paydown": principal_paydown
    }

# -------------------- STREAMLIT UI -------------------- #
st.title("🏘 AJVRE Multifamily Deal Analyzer v2.0")

st.sidebar.header("📋 Deal Inputs")
purchase_price = st.sidebar.number_input("Purchase Price ($)", value=1000000, step=50000)
down_payment_pct = st.sidebar.slider("Down Payment %", 0.1, 0.5, 0.25, step=0.01)
interest_rate = st.sidebar.slider("Interest Rate (%)", 0.03, 0.09, 0.055, step=0.001)
loan_term_years = st.sidebar.selectbox("Loan Term (years)", [30, 25, 20], index=0)
impounds = st.sidebar.checkbox("Include Taxes & Insurance (Impounds)?", True)
use_interest_only = st.sidebar.checkbox("Interest-Only Loan?", False)

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
insurance_annual = st.sidebar.number_input("Annual Insurance ($)", value=2000, step=250)
tax_rate = st.sidebar.number_input("Property Tax Rate (%)", value=1.25) / 100

st.sidebar.header("🔧 Renovation & CapEx")
renovation_cost_per_unit = st.sidebar.number_input("Renovation Cost Per Unit ($)", value=10000, step=1000)
capex_total = st.sidebar.number_input("Total Property CapEx ($)", value=15000, step=5000)

# -------------------- CALCULATION -------------------- #
results = analyze_deal(
    purchase_price,
    down_payment_pct,
    rents,
    market_rents,
    use_market_rents,
    interest_rate,
    impounds,
    expense_ratio,
    vacancy_rate,
    loan_term_years,
    tax_rate,
    insurance_annual,
    renovation_cost_per_unit,
    capex_total,
    use_interest_only,
    mgmt_override
)

# -------------------- OUTPUT -------------------- #
st.header("📊 Results")
col1, col2, col3 = st.columns(3)
col1.metric("Net Operating Income (NOI)", f"${results['NOI']:,.0f}")
col2.metric("DSCR", f"{results['DSCR']:.2f}", delta=None)
col3.metric("Cash Flow (Annual)", f"${results['Annual Cash Flow']:,.0f}")

col4, col5, col6 = st.columns(3)
col4.metric("Cap Rate", f"{results['Cap Rate']:.2%}")
col5.metric("Cash-on-Cash", f"{results['CoC Return']:.2%}")
col6.metric("Total ROI", f"{results['Total ROI']:.2%}")

st.subheader("📌 Additional Insights")
st.write(f"**Total Cash Invested:** ${results['Cash Invested']:,.0f}")
st.write(f"**Monthly Payment (P&I + Impounds):** ${results['Total Monthly Payment']:,.0f}")
st.write(f"**Principal Paydown (Annual):** ${results['Principal Paydown']:,.0f}")
st.write(f"**Required Avg Rent/Unit to Break Even:** ${results['Breakeven Rent/Unit']:,.0f}")
