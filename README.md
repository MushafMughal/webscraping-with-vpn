# Web Scraping with VPN

A Python-based web scraping tool that uses a VPN connection to safely scrape data from websites. This project specifically focuses on scraping T-Mobile dealer ordering history while ensuring anonymity and avoiding IP blocks through NordVPN integration.

## Project Description

This application provides a seamless way to collect order history data from the T-Mobile dealer ordering platform. It handles the entire process from establishing a secure VPN connection to presenting the scraped data in a user-friendly interface.

### Key Components:

1. **VPN Integration**: Automatically connects to a NordVPN server in the United States, verifies the connection, and waits until a US-based IP is confirmed before proceeding
2. **Web Automation**: Uses Playwright to navigate through authentication and data collection pages
3. **Data Parsing**: Employs BeautifulSoup to extract structured data from complex HTML tables
4. **User Interface**: Provides a clean Streamlit dashboard to initiate scraping and view results
5. **Connection Resilience**: Handles the network disruption that occurs when the VPN connects by implementing file-based status tracking

### Technical Highlights:

- Implements retry logic for VPN connections to ensure US-based IP
- Manages browser automation with proper waiting and error handling
- Extracts data from dynamic tables with flexible column handling
- Uses file-based state management to survive connection resets
- Provides real-time feedback on scraping progress

This project demonstrates advanced web scraping techniques while addressing practical challenges like VPN-induced connection disruptions and headless browser automation.

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

## Implementation Details

### VPN Connection Management

The script connects to NordVPN and verifies a US-based IP before proceeding:

```python
def connect_to_us_vpn(max_wait_minutes=5):
    # Connect to a US server
    subprocess.run([nordvpn_path, "-c", "-g", "United States"], check=True)
    
    # Wait for the connection to establish and verify it's from the US
    start_time = time.time()
    timeout = max_wait_minutes * 60
    
    while time.time() - start_time < timeout:
        ip_info = requests.get("https://ipinfo.io").json()
        country = ip_info.get("country")
        
        if country == "US":
            return True
        else:
            # Disconnect and try again
            subprocess.run([nordvpn_path, "--disconnect"], check=True)
            time.sleep(5)
            subprocess.run([nordvpn_path, "-c", "-g", "United States"], check=True)
            time.sleep(10)
    
    return False
```

### Playwright Browser Automation

The application uses Playwright for navigating the website and handling login:

```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate and login
    page.goto("https://t-mobiledealerordering.com/")
    page.locator('xpath=//*[@id="userid"]').fill("username")
    page.locator('xpath=//*[@id="password"]').fill("password")
    page.locator('xpath=//input[@type="checkbox"]').check()
    page.locator('xpath=//a[contains(@onclick, "login")]').click()
```

### Data Extraction with BeautifulSoup

BeautifulSoup is used to parse the HTML and extract table data:

```python
soup = BeautifulSoup(html, "html.parser")
table = soup.find("table", class_="history-table")

# Get dynamic column headers
headers = [th.get_text(strip=True) for th in table.find_all("th")]

# Extract row data
rows = []
for row in table.find_all("tr")[1:]:
    cells = row.find_all("td")
    row_data = [cell.get_text(strip=True) for cell in cells]
    rows.append(row_data)

df = pd.DataFrame(rows, columns=headers)
```

### Streamlit UI with Status Persistence

The Streamlit UI implements file-based status tracking to handle connection disruptions:

```python
def update_job_status(status, message=""):
    status_data = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "completed_time": datetime.now().isoformat() if status == "completed" else None
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f)
    return status_data
```

## Contributing

Contributions are welcome! Here are some ways you can contribute to this project:

1. Report bugs and issues
2. Improve documentation
3. Add new features and enhancements
4. Provide suggestions for improvements

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Playwright](https://playwright.dev/) for browser automation
- [Streamlit](https://streamlit.io/) for the user interface
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [NordVPN](https://nordvpn.com/) for VPN services
