import streamlit as st
import requests
from datetime import date, timedelta

# --- API Functions ---

# Cache data for 1 hour for live rates
@st.cache_data(ttl=3600)
def get_live_rates(base_currency):
    """Fetches the latest exchange rates from the API."""
    api_url = f"https://open.er-api.com/v6/latest/{base_currency}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return data["rates"], date.today().strftime("%Y-%m-%d")
        else:
            st.error(f"API Error: {data.get('error-type', 'Unknown error')}")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to the API. {e}")
        return None, None

# Cache historical data forever, as it doesn't change
@st.cache_data
def get_historical_rates(base_currency, query_date):
    """Fetches historical exchange rates from the API for a specific date."""
    date_str = query_date.strftime("%Y/%m/%d")
    api_url = f"https://open.er-api.com/v6/historical/{date_str}"
    # The historical endpoint's base is always USD, so we fetch that and convert
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            # Manual conversion if base is not USD
            rates = data["rates"]
            base_rate_vs_usd = rates.get(base_currency)
            if not base_rate_vs_usd:
                st.error(f"Historical data for {base_currency} not available.")
                return None, None
            # Convert all rates to be relative to the selected base currency
            adjusted_rates = {currency: rate / base_rate_vs_usd for currency, rate in rates.items()}
            return adjusted_rates, query_date.strftime("%Y-%m-%d")
        else:
            st.error(f"API Error: {data.get('error-type', 'Unknown error')}")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to the API. {e}")
        return None, None


# --- UI Configuration ---
st.set_page_config(page_title="Currency Converter", page_icon="💱", layout="centered")

st.title("💱 Advanced Currency Converter")
st.markdown("Get both live and historical exchange rates.")

# --- User Input Fields ---
common_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL", "RUB", "ZAR"]

col1, col2 = st.columns([1, 2])
with col1:
    amount = st.number_input("Amount", min_value=0.01, value=100.00, step=1.00, format="%.2f")
with col2:
    from_currency = st.selectbox("From", common_currencies, index=common_currencies.index("USD"))
    to_currency = st.selectbox("To", common_currencies, index=common_currencies.index("INR"))

# --- Historical Rate Feature ---
use_historical = st.toggle("Get Historical Rate")
query_date = None
if use_historical:
    query_date = st.date_input(
        "Select a Date",
        value=date.today() - timedelta(days=365), # Default to one year ago
        min_value=date(1999, 1, 1), # API limit
        max_value=date.today() - timedelta(days=1), # Cannot get future/today's historical
        format="YYYY-MM-DD"
    )

# --- Conversion Logic and Display ---
if st.button("Convert", type="primary", use_container_width=True):
    rates, rate_date = None, None
    if use_historical and query_date:
        rates, rate_date = get_historical_rates(from_currency, query_date)
    else:
        rates, rate_date = get_live_rates(from_currency)
    
    if rates:
        conversion_rate = rates.get(to_currency)
        if conversion_rate:
            converted_amount = amount * conversion_rate
            
            # --- Display Result ---
            st.success(f"**Conversion Result:**")
            result_text = f"## {amount:,.2f} {from_currency} = {converted_amount:,.2f} {to_currency}"
            st.markdown(result_text)
            st.info(f"**Exchange Rate as of {rate_date}:**\n\n`1 {from_currency} = {conversion_rate:.4f} {to_currency}`")
        else:
            st.error(f"Could not find the exchange rate for {to_currency}.")
