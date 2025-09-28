import streamlit as st
import requests
from datetime import date

# --- API Function ---

# Caching the data fetching function for performance.
# It will only rerun after 1 hour (3600 seconds).
@st.cache_data(ttl=3600)
def get_live_rates(base_currency):
    """Fetches the latest exchange rates from the API."""
    api_url = f"https://open.er-api.com/v6/latest/{base_currency}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if data.get("result") == "success":
            return data["rates"]
        else:
            st.error(f"API Error: {data.get('error-type', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to the API. {e}")
        return None


# --- UI Configuration ---
st.set_page_config(page_title="Currency Converter", page_icon="💱", layout="centered")

st.title("💱 Live Currency Converter")
st.markdown("This app fetches the latest exchange rates to provide accurate conversions.")

# --- User Input Fields ---
common_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL", "RUB", "ZAR"]

col1, col2, col3 = st.columns(3)

with col1:
    amount = st.number_input("Amount", min_value=0.01, value=100.00, step=1.00, format="%.2f")

with col2:
    from_currency = st.selectbox("From", common_currencies, index=common_currencies.index("USD"))

with col3:
    to_currency = st.selectbox("To", common_currencies, index=common_currencies.index("INR"))

# --- Conversion Logic and Display ---
if st.button("Convert", type="primary", use_container_width=True):
    if from_currency and to_currency and amount > 0:
        rates = get_live_rates(from_currency)
        
        if rates:
            conversion_rate = rates.get(to_currency)
            
            if conversion_rate:
                converted_amount = amount * conversion_rate
                
                # --- Display Result ---
                st.success(f"**Result:**")
                result_text = f"## {amount:,.2f} {from_currency} = {converted_amount:,.2f} {to_currency}"
                st.markdown(result_text)
                st.info(f"**Live Exchange Rate:** `1 {from_currency} = {conversion_rate:.4f} {to_currency}`")
            else:
                st.error(f"Could not find the exchange rate for {to_currency}.")
    else:
        st.warning("Please fill in all the fields correctly.")

st.markdown("---")
st.markdown(f"Rates are fetched from [ExchangeRate-API](https://www.exchangerate-api.com/) and are valid as of **{date.today().strftime('%Y-%m-%d')}**.")

