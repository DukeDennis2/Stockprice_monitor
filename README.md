📈 Real-Time Stock Monitor System

This is a dynamic, real-time stock price monitoring dashboard built using Streamlit and powered by yfinance. It allows users to track a custom watchlist of stocks, view key market metrics, and analyze the top performers using professional, customizable candlestick charts with technical indicators.

✨ Features

Real-Time Monitoring: Data automatically refreshes at a configurable interval (default is 60 seconds).

Top 3 Performers: The main dashboard automatically highlights and displays detailed charts for the top 3 best-performing stocks in your current watchlist based on daily percentage change.

Professional Charting: Uses Plotly to generate advanced charts featuring a two-row subplot layout:

Row 1 (Price): Candlestick or Line chart display.

Row 2 (Volume): Detailed volume bars.

Technical Indicators: Ability to overlay Simple Moving Average (SMA) and Exponential Moving Average (EMA) with configurable periods.

Customizable Watchlist: Easily add or remove stock tickers via the main page or the sidebar.

Key Metrics Snapshot: Displays up-to-date price, change, day's high/low, open price, and total volume for each stock.

🛠️ Requirements

The application requires Python and a few key libraries.

Prerequisites

You must have Python 3.8+ installed on your system.

Installation

Clone or download the project files.

Install the necessary Python packages using pip:

pip install streamlit yfinance pandas plotly


🚀 How to Run the App

Save the provided Python code as stock_monitor_system.py.

Open your terminal or command prompt.

Navigate to the directory where you saved the file.

Execute the Streamlit command:

streamlit run stock_monitor_system.py


The application will automatically open in your web browser. If it doesn't, copy the local URL displayed in your terminal (usually http://localhost:8501).

⚙️ Customization

All major settings can be configured using the sidebar:

Watchlist: Add/remove tickers at the top of the main screen or in the sidebar list.

Refresh Rate: Adjust how often the data is fetched (in seconds).

Chart Type: Switch between Candlestick and Line charts.

Indicators: Select SMA and/or EMA and set the lookback Indicator Period.