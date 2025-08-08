import streamlit as st
import pandas as pd
import subprocess
import os.path
import time
import json
import mysql.connector
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="T-Mobile Order History Scraper", layout="wide")

st.title("T-Mobile Order History Scraper")

# Constants for status tracking
STATUS_FILE = "scraper_status.json"

# Check if a job is running or recently completed
def get_job_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                status_data = json.load(f)
            return status_data
        except:
            return {"status": "unknown", "timestamp": None}
    return {"status": "none", "timestamp": None}

# Update job status
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

def import_data():
    # Create a placeholder for the spinner and status updates
    status_placeholder = st.empty()
    
    # Update status to running
    update_job_status("running", "Scraping process started")
    
    try:
        with status_placeholder.container():
            st.write("Starting the scraping process...")
            st.write("This may take a few minutes. If the spinner disappears when VPN connects, please refresh the page.")
            
            # Start the scraping process in the background and allow output to show in terminal
            process = subprocess.Popen(
                [r"C:\Program Files\Python312\python.exe", "main.py"],
                # Don't redirect stdout/stderr to allow terminal visibility
            )
            
            # Monitor the process while showing a spinner
            spinner_text = "Connecting to VPN and scraping T-Mobile order history..."
            with st.spinner(spinner_text):
                # Wait until the process completes
                process.wait()
                
                # Check if the process was successful
                if process.returncode != 0:
                    update_job_status("failed", "Error during scraping")
                    st.error(f"Error during scraping. Check your terminal for details.")
                    return None
                
                # Check if the CSV file was created
                if not os.path.exists("order_history.csv"):
                    update_job_status("failed", "No data file was created")
                    st.error("Scraping completed but no data file was created.")
                    return None
                
                # Update status to completed
                update_job_status("completed", "Scraping completed successfully")
                
                # Load the data
                df = pd.read_csv("order_history.csv")
                return df
    except Exception as e:
        update_job_status("failed", f"Error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return None

# Check for existing status
job_status = get_job_status()
current_status = job_status.get("status", "none")
status_message = job_status.get("message", "")
timestamp = job_status.get("timestamp")

# Display information about the job status
if current_status == "running":
    st.warning("⚠️ A scraping job is currently running")
    st.info("Note: When VPN connects, the page may refresh. If this happens, just refresh your browser to see updated status.")
    
    if timestamp:
        try:
            start_time = datetime.fromisoformat(timestamp)
            elapsed = datetime.now() - start_time
            minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
            st.write(f"Job has been running for approximately {minutes} minutes and {seconds} seconds")
        except:
            pass
elif current_status == "completed" and os.path.exists("order_history.csv"):
    st.success("✅ Previous scraping job completed successfully!")
    
    # Clear status button
    if st.button("Start New Scraping Job", key="clear_status"):
        # Remove status file
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)
        st.rerun()
elif current_status == "failed":
    st.error(f"❌ Previous scraping job failed: {status_message}")
    
    # Clear status button
    if st.button("Clear Error and Try Again", key="clear_error"):
        # Remove status file
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)
        st.rerun()

# Main scraping button - only show if not currently running
if current_status != "running":
    if st.button("Scrape Data", use_container_width=True, key="scrape_button"):
        df = import_data()
        
        if df is not None and not df.empty:
            st.success("✅ Data scraped successfully!")
            st.rerun()
    
# Display results if available (regardless of current status)
if os.path.exists("order_history.csv") and os.path.getsize("order_history.csv") > 0:
    try:
        # Get file modification time as a fallback for last scraped time
        file_mod_time = datetime.fromtimestamp(os.path.getmtime("order_history.csv"))
        
        # Get the completed time from status file if available
        completed_time = None
        if 'completed_time' in job_status and job_status['completed_time']:
            try:
                completed_time = datetime.fromisoformat(job_status['completed_time'])
            except:
                completed_time = file_mod_time
        else:
            completed_time = file_mod_time
            
        # Format the last scraped time
        last_scraped = completed_time.strftime("%B %d, %Y at %I:%M %p")
        
        # Load the data
        df = pd.read_csv("order_history.csv")
        
        # Create columns for the information display
        col1, col2 = st.columns(2)
        
        with col1:
            # Show data count
            st.metric("Orders Retrieved", len(df))
        
        with col2:
            # Show last scraped time
            st.metric("Last Scraped", last_scraped)
        
        # Try to find the date column in the dataframe
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        
        if date_columns:
            # Get the most recent date from the dataframe
            try:
                for date_col in date_columns:
                    # Try to convert to datetime
                    try:
                        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        most_recent = df[date_col].max()
                        if pd.notna(most_recent):
                            st.info(f"Most recent order date: {most_recent.strftime('%B %d, %Y')}")
                            break
                    except:
                        continue
            except Exception as e:
                # If there's an error finding the date, just continue without showing it
                pass
        
        # Show the data
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f"t_mobile_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
elif current_status != "running":
    st.write("Click the 'Scrape Data' button above to start scraping T-Mobile order history.")