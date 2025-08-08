# Web Scraping with VPN

A Python-based web scraping tool that uses a VPN connection to safely scrape data from websites. This project demonstrates how to:

1. Connect to a NordVPN server using the command-line interface
2. Perform web scraping using Playwright for browser automation
3. Extract and process data from websites
4. Present the results through a user-friendly Streamlit interface

## Features

- Automatic VPN connection with country selection
- Web scraping with Playwright for modern websites
- Beautiful Soup for HTML parsing and data extraction
- Streamlit UI for easy interaction and data visualization
- Status tracking that persists through VPN connection resets
- CSV export of scraped data

## Requirements

- Python 3.10 or higher
- NordVPN desktop application installed
- Required Python packages (see requirements.txt)

## Setup

1. Clone this repository
2. Install required dependencies: `pip install -r requirements.txt`
3. Make sure NordVPN is installed and configured

## Usage

1. Run the Streamlit app: `streamlit run app.py`
2. Click "Scrape Data" to start the scraping process
3. Wait for the VPN connection and scraping to complete
4. View and download the results

## Note

If the VPN connection causes a page refresh in the Streamlit UI, simply refresh your browser to see the current status and results.
