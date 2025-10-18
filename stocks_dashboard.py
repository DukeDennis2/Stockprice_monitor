import streamlit as st
import yfinance as yf
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go # Added for Candlestick chart

# --- Configuration and Setup ---
st.set_page_config(
    page_title="Real-Time Stock Portfolio Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 1. Configuration: Define the stocks you want to monitor
# ----------------------------------------------------
# You can edit this list to include any valid stock tickers.
DEFAULT_TICKERS = [
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corp
    "GOOGL", # Alphabet Inc. (Google)
    "TSLA",  # Tesla, Inc.
    "AMZN",  # Amazon.com, Inc.
    "JPM",   # JPMorgan Chase & Co.
    "V",     # Visa Inc.
]
TICKER_LIST = st.sidebar.text_area(
    "Edit Tickers (comma-separated)",
    ", ".join(DEFAULT_TICKERS)
)
MONITOR_TICKERS = [t.strip().upper() for t in TICKER_LIST.split(',') if t.strip()]

# Refresh rate in seconds
REFRESH_RATE = st.sidebar.slider("Data Refresh Rate (seconds)", 30, 120, 60, 15)

# New Chart Type Selection
CHART_TYPE = st.sidebar.radio(
    "Select Chart Type",
    ["Line", "Candlestick"]
)

# ----------------------------------------------------
# 2. Data Fetching Functions
# ----------------------------------------------------

@st.cache_data(ttl=REFRESH_RATE)
def get_stock_data(ticker):
    """
    Fetches 1-day/1-minute interval data for a single ticker.
    This function is cached and will only run again after REFRESH_RATE seconds.
    """
    try:
        # Fetch data for the last 1 day at 1-minute intervals
        data = yf.download(ticker, period="1d", interval="1m")
        if data.empty:
            if not data.index.empty:
                st.warning(f"No minute data available for {ticker} for the 1-day interval.")
            return None
        
        # --- CRITICAL FIX FOR MultiIndex ERROR ---
        # Check if the columns are MultiIndex (e.g., ('Close', 'AAPL')) and flatten them
        if isinstance(data.columns, pd.MultiIndex):
            # Dropping the second level leaves the column names as 'Close', 'Open', etc.
            data.columns = data.columns.droplevel(1)
        # --- END CRITICAL FIX ---
        
        # --- Using .item() to ensure pure float values ---
        latest_close = data['Close'].iloc[-1].item()
        
        # Use previous close if available, otherwise use open
        if len(data) > 1:
            # Use the close of the previous interval for accurate delta
            open_price = data['Close'].iloc[-2].item() 
        else:
            # Fallback to today's open
            open_price = data['Open'].iloc[0].item() 

        current_price = latest_close 
        
        # The change is calculated from the start of the day (Open/Prev Close) to the current price
        dollar_change = current_price - open_price
        
        percent_change = (dollar_change / open_price) * 100 if open_price != 0 else 0
        
        # Extract High and Low for the period safely
        period_high = data['High'].max().item()
        period_low = data['Low'].min().item()
        latest_volume = data['Volume'].iloc[-1].item()

        
        # Prepare the data dictionary
        stock_info = {
            "Ticker": ticker,
            "Price": current_price,
            "Change $": dollar_change,
            "Change %": percent_change,
            "High": period_high,
            "Low": period_low,
            "Volume": latest_volume,
            "Data": data # Keep the historical data for charting
        }
        return stock_info
    except Exception as e:
        # We can log the error but avoid crashing the app
        # print(f"Error fetching data for {ticker}: {e}")
        # st.error(f"Error fetching data for {ticker}. Check console for details.")
        return None

# ----------------------------------------------------
# 3. Main Dashboard Layout
# ----------------------------------------------------

st.title("📈 Real-Time Stock Price Monitor")
st.markdown("Monitoring key performance indicators with automatic refresh.")


# Create an empty container to hold the dynamic content
placeholder = st.empty()

# --- Continuous Refresh Loop ---
while True:
    # Use the placeholder to update the content inside the 'with' block
    with placeholder.container():
        
        st.subheader(f"Last Updated: {pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')}")
        
        col_count = 3 # Number of columns for the monitor cards
        cols = st.columns(col_count)
        
        all_stock_data = []

        # 1. Fetch and Display Cards
        for i, ticker in enumerate(MONITOR_TICKERS):
            if not ticker:
                continue
                
            stock_info = get_stock_data(ticker)
            
            if stock_info:
                all_stock_data.append(stock_info)
                
                # Determine the delta sign
                delta_sign = "+" if stock_info['Change $'] >= 0 else ""
                
                # Use 'normal' for delta_color to allow Streamlit to handle green/red coloring
                delta_color = "normal" 
                
                # Place the stock card in the appropriate column
                col = cols[i % col_count]
                
                with col.container(border=True):
                    # Display the metric card
                    st.metric(
                        label=f"{stock_info['Ticker']}",
                        value=f"${stock_info['Price']:,.2f}",
                        delta=f"{delta_sign}{stock_info['Change $']:,.2f} ({delta_sign}{stock_info['Change %']:,.2f}%)",
                        delta_color=delta_color
                    )
                    
                    # Display summary stats below the main metric
                    st.markdown(f"""
                        <div style='font-size: 10px; display: flex; justify-content: space-between;'>
                            <span>High: ${stock_info['High']:,.2f}</span>
                            <span>Low: ${stock_info['Low']:,.2f}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
        # 2. Display Charts below the cards
        st.markdown("---")
        st.subheader(f"Price Movement ({CHART_TYPE} View - Last Trading Day)")
        
        # Create columns for the charts, dynamic based on the number of stocks
        chart_cols = st.columns(len(all_stock_data) if len(all_stock_data) <= 4 else 4)

        for i, stock in enumerate(all_stock_data):
            # Only show up to 4 charts across the screen for better viewing
            if i < len(chart_cols):
                with chart_cols[i]:
                    data = stock["Data"]
                    
                    if CHART_TYPE == "Line":
                        fig = px.line(
                            data,
                            y='Close',
                            x=data.index,
                            title=f"{stock['Ticker']} (Line)",
                            height=250,
                        )
                    else: # Candlestick Chart
                        fig = go.Figure(data=[go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name=stock['Ticker']
                        )])
                        fig.update_layout(title=f"{stock['Ticker']} (Candlestick)", height=250)
                    
                    # Format the chart look
                    fig.update_layout(
                        margin={"r":10,"t":40,"l":10,"b":10},
                        yaxis_title="",
                        xaxis_title="",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


    # 3. Wait for the defined refresh rate before looping again
    time.sleep(REFRESH_RATE)