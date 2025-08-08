import subprocess
from playwright.sync_api import sync_playwright
import time
import pandas as pd
from bs4 import BeautifulSoup
import requests
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

nordvpn_path = r"C:\Program Files\NordVPN\nordvpn.exe"

def get_connection():
    return mysql.connector.connect(
            host=os.getenv("DB_HOST"),  
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
    )

conn = get_connection()

# Step 1: Connect to NordVPN and wait for US connection
def connect_to_us_vpn(max_wait_minutes=5):
    # First, try to connect to a US server
    subprocess.run([nordvpn_path, "-c", "-g", "United States"], check=True)
    time.sleep(15)  # Give it time to establish connection
    
    # Wait for the connection to establish and verify it's from the US
    start_time = time.time()
    timeout = max_wait_minutes * 60  # convert to seconds
    
    while time.time() - start_time < timeout:
        try:
            ip_info = requests.get("https://ipinfo.io").json()
            country = ip_info.get("country")
            ip = ip_info.get("ip")
            
            print(f"Current VPN IP: {ip} | Country: {country}")
            
            if country == "US":
                print(f"Successfully connected to US VPN after {int(time.time() - start_time)} seconds")
                return True
            else:
                print(f"Not connected to US yet, trying again... (Country: {country})")
                # Disconnect and try again
                subprocess.run([nordvpn_path, "--disconnect"], check=True)
                time.sleep(5)  # Wait a bit before reconnecting
                subprocess.run([nordvpn_path, "-c", "-g", "United States"], check=True)
                time.sleep(10)  # Give it time to establish connection
        except Exception as e:
            print(f"Error checking VPN connection: {e}")
            time.sleep(5)
    
    print(f"Failed to connect to US VPN after {max_wait_minutes} minutes")
    return False

def scrape_t_mobile_order_history():
    # Connect to US VPN with a maximum wait of 5 minutes
    if not connect_to_us_vpn(max_wait_minutes=5):
        print("Exiting: Could not establish US VPN connection")
        exit(1)

    
    dfs = []
    df = pd.read_sql("SELECT * FROM idoo.idoo_logins;", conn) # columns: Markets, Username, PW


    for index, row in df.iterrows():
        markets = row['Markets']
        username = row['Username']
        password = row['PW']

        # Step 2: Run Playwright task
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            response = page.goto("https://t-mobiledealerordering.com/", wait_until="domcontentloaded")
            content = page.content()

            if response and response.status == 200 and "Access Denied" not in content:
                
                print("Page loaded successfully. Proceeding to login...")

                # Wait for the page to load completely
                page.wait_for_load_state("networkidle")

                # Fill in user ID and password
                page.locator('xpath=//*[@id="userid"]').fill(username)
                page.locator('xpath=//*[@id="password"]').fill(password)

                # Tick the "Remember Me" checkbox
                page.locator('xpath=/html/body/div[2]/form/div[2]/div/table/tbody/tr[5]/td[2]/input').check()

                # Click the Login button
                page.locator('xpath=/html/body/div[2]/form/div[2]/div/table/tbody/tr[6]/td[2]/a').click()
                print("Login form submitted.")
                page.wait_for_load_state("networkidle")  # wait for page to load fully


                # Navigate to the history page after login
                page.goto("https://t-mobiledealerordering.com/b2b_tmo/b2b/history/updatehistory1.do?welcome=1")


                # Get the HTML content of the page
                html = page.content()

                #dump HTML content to a file for debugging
                with open("debug_page_content.html", "w", encoding="utf-8") as f:
                    f.write(html)

                # Wait for the table to appear (use appropriate selector or delay)
                page.wait_for_selector("table.history-table", state="visible", timeout=10000)

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")

                # Find the first table with class "history-table"
                table = soup.find("table", class_="history-table")

                # --- ✅ Get dynamic column headers ---
                headers = [th.get_text(strip=True) for th in table.find_all("th")]

                # --- ✅ Extract row data ---
                rows = []
                for row in table.find_all("tr")[1:]:  # skip header
                    cells = row.find_all("td")
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    rows.append(row_data)

                # Create DataFrame
                df = pd.DataFrame(rows, columns=headers)
                df["Market"] = markets

                dfs.append(df)
            
            else:
                print(f"Access blocked or page error. Skipping {username} | {markets}")
            
            browser.close()  # Close the browser after scraping


    # Concatenate all DataFrames
    if dfs:
        final_df = pd.concat(dfs, ignore_index=True)
        final_df.to_csv("order_history.csv", index=False)

        print("Data scraped and saved to order_history.csv")

        
    # Step 3: Disconnect VPN
    subprocess.run([nordvpn_path, "--disconnect"], check=True)
    print("VPN disconnected successfully.")


if __name__ == "__main__":
    scrape_t_mobile_order_history()

