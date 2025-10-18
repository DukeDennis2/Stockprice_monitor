import streamlit as st
import yfinance as yf
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go 
from plotly.subplots import make_subplots # New import for subplots

# --- Configuration and Setup ---
# Use the widest possible layout
st.set_page_config(
    page_title="Real-Time Stock Portfolio Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 1. Configuration: Define the stocks and controls
# ----------------------------------------------------
# Default list of tickers
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "JPM", "V", "NVDA", "ADBE"
]

# Initialize session state for tickers if it doesn't exist
if 'monitor_tickers' not in st.session_state:
    st.session_state.monitor_tickers = DEFAULT_TICKERS

# Function to add a ticker
def add_ticker_to_list():
    new_ticker = st.session_state.new_ticker_input.strip().upper()
    if new_ticker and new_ticker not in st.session_state.monitor_tickers:
        # Basic check to see if yfinance can access it (optional but helpful)
        try:
            test_data = yf.Ticker(new_ticker).info
            # Check for a fundamental price key to validate the ticker
            if test_data and ('regularMarketPrice' in test_data or 'previousClose' in test_data):
                st.session_state.monitor_tickers.append(new_ticker)
                st.session_state.new_ticker_input = "" # Clear input
            else:
                st.warning(f"Ticker '{new_ticker}' is a valid symbol but data is unavailable.")
        except:
            st.warning(f"Ticker '{new_ticker}' is not a valid stock symbol.")
    
# Function to remove a ticker (used in the sidebar list)
def remove_ticker_from_list(ticker_to_remove):
    if ticker_to_remove in st.session_state.monitor_tickers:
        st.session_state.monitor_tickers.remove(ticker_to_remove)

st.title("📈 Real-Time Stock Price Monitor")
st.markdown("---")

# --- ADD TICKER SEARCH BAR ON MAIN PAGE ---
col_search, col_add = st.columns([5, 1])
col_search.text_input(
    "Enter Ticker to Add (e.g., QCOM, BABA, WMT)", 
    key="new_ticker_input",
    on_change=add_ticker_to_list,
    label_visibility="collapsed",
    placeholder="Enter Ticker to Add (e.g., QCOM, BABA, WMT)"
)
col_add.button("Add Ticker", on_click=add_ticker_to_list, use_container_width=True)
st.markdown("---")
# --- END ADD TICKER SEARCH BAR ---


# --- SIDEBAR CONTROLS ---
st.sidebar.header("Current Watchlist")
st.sidebar.markdown(f"**Monitoring {len(st.session_state.monitor_tickers)} Stocks**")
# Display current list with remove buttons
for ticker in st.session_state.monitor_tickers:
    col_t, col_b = st.sidebar.columns([3, 1])
    col_t.markdown(f"**{ticker}**")
    # Use f-string key for uniqueness and a more visually appealing icon for removal
    col_b.button(":x:", key=f"remove_{ticker}", on_click=remove_ticker_from_list, args=(ticker,), help="Remove from watchlist", use_container_width=True)
st.sidebar.markdown("---")


st.sidebar.header("App Configuration")
# Refresh rate in seconds
REFRESH_RATE = st.sidebar.slider("Data Refresh Rate (seconds)", 30, 120, 60, 15)


# --- Charting Controls ---
st.sidebar.header("Chart Customization")

# Chart Type Selection (Defaulting to Candlestick to match screenshot request)
CHART_TYPE = st.sidebar.radio(
    "Select Chart Type",
    ["Candlestick", "Line"],
    index=0 # Candlestick is now the default
)

# Technical Indicator Controls
INDICATORS = st.sidebar.multiselect(
    "Overlay Technical Indicators",
    options=["SMA", "EMA"],
    default=[]
)

INDICATOR_PERIOD = st.sidebar.slider(
    "Indicator Period (e.g., 20-period)",
    min_value=5, max_value=60, value=20, step=5,
    disabled=(len(INDICATORS) == 0) 
)


# ----------------------------------------------------
# 2. Data Fetching Functions
# ----------------------------------------------------

# Use st.session_state.monitor_tickers here
MONITOR_TICKERS = st.session_state.monitor_tickers

@st.cache_data(ttl=REFRESH_RATE)
def get_stock_data(ticker):
    """
    Fetches 1-day/1-minute interval data for a single ticker.
    """
    try:
        # Fetch data for the last 1 day at 1-minute intervals
        data = yf.download(ticker, period="1d", interval="1m")
        if data.empty:
            return None
        
        # --- CRITICAL FIX FOR MultiIndex ERROR ---
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        # --- END CRITICAL FIX ---
        
        # Data Extraction
        latest_close = data['Close'].iloc[-1].item()
        latest_open = data['Open'].iloc[-1].item() # Added latest open for summary stat
        
        # Calculate change from the previous period (using the opening price of the day)
        if len(data) > 1:
            open_price_of_day = data['Open'].iloc[0].item() 
        else:
            open_price_of_day = latest_close 

        current_price = latest_close 
        dollar_change = current_price - open_price_of_day
        percent_change = (dollar_change / open_price_of_day) * 100 if open_price_of_day != 0 else 0
        
        # Extract period stats safely
        period_high = data['High'].max().item()
        period_low = data['Low'].min().item()
        latest_volume = data['Volume'].iloc[-1].item()
        total_volume = data['Volume'].sum().item() # Total volume for the period
        
        # Calculate Day's Range for summary stat
        day_range = f"{period_low:,.2f} - {period_high:,.2f}"

        
        stock_info = {
            "Ticker": ticker,
            "Price": current_price,
            "Change $": dollar_change,
            "Change %": percent_change,
            "High": period_high,
            "Low": period_low,
            "DayRange": day_range, # New summary stat
            "OpenPrice": latest_open, # New summary stat
            "Volume": latest_volume,
            "TotalVolume": total_volume, # New summary stat
            "Data": data 
        }
        return stock_info
    except Exception as e:
        # st.error(f"Error fetching data for {ticker}. Check console.")
        return None

# ----------------------------------------------------
# 3. Main Dashboard Layout and Loop
# ----------------------------------------------------

# Create an empty container to hold the dynamic content and enable refresh
placeholder = st.empty()

# --- Continuous Refresh Loop ---
while True:
    # Use the placeholder to update the content inside the 'with' block
    with placeholder.container():
        
        st.info(f"Last Updated: {pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')} (Refreshes every {REFRESH_RATE} seconds)")
        
        # Define the maximum number of metric cards per row
        MAX_METRIC_COLUMNS = 4
        
        all_stock_data = []

        # 1. Fetch and Display Metric Cards
        st.subheader("Current Market Snapshot")
        
        # Determine how many columns to use for the current row of metrics
        num_stocks_to_display = len(MONITOR_TICKERS)
        
        # Initialize column list
        cols = st.columns(min(num_stocks_to_display, MAX_METRIC_COLUMNS) or 1) # Ensure at least 1 column for layout
        
        for i, ticker in enumerate(MONITOR_TICKERS):
            if not ticker:
                continue
                
            stock_info = get_stock_data(ticker)
            
            if stock_info:
                all_stock_data.append(stock_info)
                
                # ... (Metric card display logic remains the same) ...
                delta_sign = "+" if stock_info['Change $'] >= 0 else ""
                delta_color = "normal" 
                
                col_index = i % MAX_METRIC_COLUMNS

                if col_index == 0 and i != 0:
                    cols = st.columns(min(num_stocks_to_display - i, MAX_METRIC_COLUMNS))

                if cols and col_index < len(cols):
                    with cols[col_index].container(border=True):
                        st.metric(
                            label=f"{stock_info['Ticker']}",
                            value=f"${stock_info['Price']:,.2f}",
                            delta=f"{delta_sign}{stock_info['Change $']:,.2f} ({delta_sign}{stock_info['Change %']:,.2f}%)",
                            delta_color=delta_color
                        )
                        st.markdown(f"""
                            <div style='font-size: 10px; display: flex; justify-content: space-between; margin-top: -10px;'>
                                <span style='color: #4CAF50;'>High: ${stock_info['High']:,.2f}</span>
                                <span style='color: #F44336;'>Low: ${stock_info['Low']:,.2f}</span>
                            </div>
                        """, unsafe_allow_html=True)
                # ... (End Metric card display logic) ...

        st.markdown("---")
                    
        # 2. Display Charts for TOP 3 PERFORMERS
        
        # --- NEW: Sort and limit to Top 3 ---
        sorted_stocks = sorted(all_stock_data, key=lambda x: x['Change %'], reverse=True)
        top_3_stocks = sorted_stocks[:3]
        
        st.subheader(f"Top {len(top_3_stocks)} Performers (Detailed View)")
        
        MAX_CHART_COLUMNS = 3 # Always show 3 charts side-by-side
        
        # Create 3 columns for the top 3 charts
        chart_cols = st.columns(MAX_CHART_COLUMNS)

        for i, stock in enumerate(top_3_stocks):
            
            with chart_cols[i]:
                data = stock["Data"]
                ticker = stock['Ticker']
                
                # --- Indicator Calculation ---
                if "SMA" in INDICATORS:
                    data['SMA'] = data['Close'].rolling(window=INDICATOR_PERIOD).mean()
                if "EMA" in INDICATORS:
                    data['EMA'] = data['Close'].ewm(span=INDICATOR_PERIOD, adjust=False).mean()
                # --- End Indicator Calculation ---
                
                # --- Subplots Setup: 2 rows (Price and Volume) ---
                fig = make_subplots(
                    rows=2, 
                    cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.05, 
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f"{ticker}", "") # Title is placed in the first subplot
                )
                
                # 1. PRICE TRACE (Row 1)
                if CHART_TYPE == "Candlestick":
                    fig.add_trace(go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name='Price'
                    ), row=1, col=1)
                else: # Line Chart
                     fig.add_trace(go.Scatter(
                        x=data.index, y=data['Close'], mode='lines', name='Price', line=dict(color='blue')
                    ), row=1, col=1)

                # 2. INDICATOR TRACES (Row 1)
                if "SMA" in INDICATORS:
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA'], mode='lines', name=f'SMA {INDICATOR_PERIOD}', line=dict(color='#FF9800', width=1.5)), row=1, col=1)
                if "EMA" in INDICATORS:
                    fig.add_trace(go.Scatter(x=data.index, y=data['EMA'], mode='lines', name=f'EMA {INDICATOR_PERIOD}', line=dict(color='#9C27B0', width=1.5)), row=1, col=1)

                # 3. VOLUME TRACE (Row 2)
                # Color volume bars based on change (Close > Open = Green, Close < Open = Red)
                colors = ['rgba(0, 128, 0, 0.5)' if data['Close'][j] > data['Open'][j] else 'rgba(255, 0, 0, 0.5)' for j in range(len(data))]
                fig.add_trace(go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color=colors
                ), row=2, col=1)

                # --- Chart Formatting ---
                fig.update_layout(
                    title_text=f"{ticker}",
                    margin={"r":10,"t":40,"l":10,"b":10},
                    height=500, # Increased height for better visibility of subplots
                    yaxis1_title="Price ($)",
                    yaxis2_title="Volume",
                    xaxis_title="",
                    showlegend=True, 
                    xaxis_rangeslider_visible=False,
                    xaxis2_rangeslider_visible=False # Hide volume range slider
                )
                # Ensure the candlestick/line chart doesn't show its own range slider
                fig.update_xaxes(rangeselector_visible=False, row=1, col=1)

                # Add unique key to prevent DuplicateElementId error
                st.plotly_chart(
                    fig, 
                    use_container_width=True, 
                    config={'displayModeBar': False},
                    key=f"chart_{ticker}_{CHART_TYPE}" 
                )

               

    # 3. Wait for the defined refresh rate before looping again
    time.sleep(REFRESH_RATE)
