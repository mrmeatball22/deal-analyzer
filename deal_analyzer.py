import streamlit as st
from math import pow

def analyze_deal(purchase_price, down_payment_pct, rents, interest_rate, impounds=True, expense_ratio=0.3, vacancy_rate=0.03, loan_term_years=30, tax_rate=0.0125, insurance_annual=1500):
    # --- Income ---
    gross_rent_annual = sum(rents) * 12
    vacancy_loss = gross_rent_annual * vacancy_rate
    gross_operating_income = gross_rent_annual - vacancy_loss

    # --- Expenses ---
    operating_expenses = gross_operating_income * expense_ratio

    # --- Loan ---
    loan_amount = purchase_price * (1 - down_payment_pct)
    monthly_interest_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    monthly_pi = loan_amount * (monthly_interest_rate * pow(1 + monthly_interest_rate, num_payments)) / (pow(1 + monthly_interest_rate, num_payments) - 1)
    annual_pi = monthly_pi * 12

    # --- Impounds ---
    annual_taxes = purchase_price * tax_rate
    annual_insurance = insurance_annual
    monthly_impounds = (annual_taxes + annual_insurance) / 12 if impounds else 0
    monthly_total_payment = monthly_pi + monthly_impounds
    annual_total_payment = monthly_total_payment * 12

    # --- NOI & DSCR ---
    noi = gross_operating_income - operating_expenses
    dscr = noi / annual_total_payment if annual_total_payment > 0 else 0

    return {
        "Purchase Price": purchase_price,
        "Down Payment %": down_payment_pct,
        "Gross Rent (Annual)": gross_rent_annual,
        "Vacancy Loss": vacancy_loss,
        "GOI": gross_operating_income,
        "Operating Expenses": operating_expenses,
        "NOI": noi,
        "Monthly P&I": monthly_pi,
        "Monthly Impounds": monthly_impounds,
        "Monthly Total Payment": monthly_total_payment,
        "Annual Debt Service": annual_total_payment,
        "DSCR": dscr
    }

# Streamlit UI
st.title("Multifamily Deal Analyzer")

st.sidebar.header("Input Parameters")
purchase_price = st.sidebar.number_input("Purchase Price ($)", value=400000, step=10000)
down_payment_pct = st.sidebar.slider("Down Payment %", min_value=0.1, max_value=0.5, value=0.25, step=0.01)
interest_rate = st.sidebar.slider("Interest Rate (%)", min_value=0.03, max_value=0.09, value=0.055, step=0.001)
impounds = st.sidebar.checkbox("Include Impounds (Taxes & Insurance)", value=True)
expense_ratio = st.sidebar.slider("Operating Expense Ratio (%)", min_value=0.2, max_value=0.6, value=0.3, step=0.01)
vacancy_rate = st.sidebar.slider("Vacancy Rate (%)", min_value=0.0, max_value=0.1, value=0.03, step=0.01)

num_units = st.sidebar.number_input("Number of Units", min_value=1, max_value=20, value=2)
rents = []
st.sidebar.markdown("### Unit Rents")
for i in range(int(num_units)):
    rent = st.sidebar.number_input(f"Unit {i+1} Rent ($/mo)", value=1500, step=50)
    rents.append(rent)

# Analysis
results = analyze_deal(
    purchase_price=purchase_price,
    down_payment_pct=down_payment_pct,
    rents=rents,
    interest_rate=interest_rate,
    impounds=impounds,
    expense_ratio=expense_ratio,
    vacancy_rate=vacancy_rate
)

st.header("Deal Summary")
for k, v in results.items():
    st.write(f"**{k}**: ${v:,.2f}" if isinstance(v, float) else f"**{k}**: {v}")
