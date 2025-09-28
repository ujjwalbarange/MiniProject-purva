import streamlit as st
import google.generativeai as genai
from datetime import date, timedelta

# --- Configuration and API Key Setup ---
st.set_page_config(page_title="Gemini Currency Converter", page_icon="🔮", layout="centered")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except (FileNotFoundError, KeyError):
    st.error("ERROR: `GOOGLE_API_KEY` not found. Please create `.streamlit/secrets.toml` and add your key.")
    st.stop()

# --- Gemini API Function ---
@st.cache_data
def get_gemini_historical_rate(from_currency, to_currency, query_date):
    """
    Asks the Gemini API for a historical exchange rate with a specially crafted prompt
    to force a numerical-only response.
    """
    date_str = query_date.strftime("%Y-%m-%d")
    prompt = (
        f"What was the conversion rate for 1 {from_currency} to {to_currency} on the date {date_str}? "
        "Provide only the numerical value of the exchange rate as a floating-point number. "
        "Do not include any other text, currency symbols, or explanations. Just the number."
    )

    try:
        # --- THIS IS THE ONLY LINE THAT CHANGED ---
        model = genai.GenerativeModel('gemini-pro') # Formerly 'gemini-1.5-flash'
        
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace(",", "")
        rate = float(cleaned_text)
        return rate
    
    except ValueError:
        st.error(f"Gemini's response was not a valid number. Response: '{response.text}'")
        return None
    except Exception as e:
        st.error(f"An error occurred with the Gemini API: {e}")
        return None

# --- UI ---
st.title("🔮 Gemini Historical Currency Converter")
st.markdown("This converter uses the Gemini API to find historical exchange rates.")

common_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL", "RUB", "ZAR"]

col1, col2 = st.columns([1, 2])
with col1:
    amount = st.number_input("Amount", min_value=0.01, value=100.00, step=1.00, format="%.2f")
with col2:
    from_currency = st.selectbox("From Currency", common_currencies, index=common_currencies.index("USD"))
    to_currency = st.selectbox("To Currency", common_currencies, index=common_currencies.index("INR"))

query_date = st.date_input(
    "Select a Historical Date",
    value=date.today() - timedelta(days=365),
    max_value=date.today() - timedelta(days=1),
    format="YYYY-MM-DD"
)

if st.button("Convert using Gemini", type="primary", use_container_width=True):
    if amount > 0 and from_currency and to_currency and query_date:
        rate = get_gemini_historical_rate(from_currency, to_currency, query_date)
        
        if rate is not None:
            converted_amount = amount * rate
            
            st.success(f"**Conversion Result:**")
            st.markdown(f"## {amount:,.2f} {from_currency} = {converted_amount:,.2f} {to_currency}")
            st.info(f"**Rate from Gemini for {query_date.strftime('%Y-%m-%d')}:**\n\n`1 {from_currency} = {rate:.4f} {to_currency}`")
        else:
            st.warning("Could not perform conversion. Please check the error message above.")

