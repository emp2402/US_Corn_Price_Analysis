import logging
import pandas as pd
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger(__name__)

def sanitize_data_types(df):
    # The target schema we *want* to achieve
    target_schema = {
        "Year": "Int64",
        "Planted Acres": "Int64",
        "Harvested Acres": "Int64",
        "Production": "Int64",
        "Stocks": "Int64", 
        "Exports": "Int64",
        "Imports": "Int64",
        "Total Supply": "Int64", 
        "Total Usage": "Int64", 
        "All Dom. Use": "Int64",
        "Ending Stocks": "Int64",
        "Actual Yield": "float64"
    }

    print("\n--- Starting Data Type Diagnosis ---")
    
    for col, dtype in target_schema.items():
        if col not in df.columns:
            continue

        # Convert to numeric first to handle any potential strings
        # We use a temporary series so we don't mutate the DF if it fails
        series = pd.to_numeric(df[col], errors='coerce')
        
        try:
            if dtype == "Int64":
                # We round to eliminate floating point drift (e.g. 99.9999 -> 100)
                # Then we cast to Int64. 
                df[col] = series.round().astype("Int64")
            else:
                # For floats, just cast normally
                df[col] = series.astype(dtype)
        except TypeError as e:
            # If we are here, pandas refused to cast because of data loss
            print(f"\n[FAIL] Column '{col}' refused cast to {dtype}.")
            
            # Find the specific culprits: values that are not null but have a decimal part
            # x % 1 != 0 finds decimals (e.g. 5.5 % 1 = 0.5)
            bad_rows = series[
                (series.notna()) & 
                (series % 1 != 0)
            ]
            
            print(f"   Reason: Found {len(bad_rows)} non-integer values.")
            print(f"   Sample offending values:")
            print(bad_rows.head(5).to_string()) 
            
            # Optional: Stop script execution here so you can look at the logs
            # raise e 

    print("\n--- Diagnosis Complete ---\n")
    return df

def run_scrape():
    """
    Scrapes Corn Supply and Demand data from agmanager.info.
    """
    logger.info("Starting Corn Supply & Demand scrape...")

    # Configure Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out to debug visually
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # FIX 1: Set Window Size
    # Headless mode often defaults to mobile size, hiding the menu. 
    # We force desktop size to ensure the navigation bar is visible.
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://www.agmanager.info/"
        logger.info(f"Navigating to {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)

        # FIX 2: Use Text instead of internal CMS ID
        # Old ID (menu-mlid-1183) is brittle. Partial Link Text is robust.
        logger.info("Locating 'Grain Supply and Demand' link...")
        wasde_link = wait.until(EC.element_to_be_clickable(
            (By.PARTIAL_LINK_TEXT, "Grain Supply and Demand (WASDE)")
        ))
        wasde_link.click()

        # FIX 3: Robust "Download" button handling
        # We wait for the 'btn-group' that likely contains the download options
        logger.info("Opening download options...")
        download_btn = wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "btn-group")
        ))
        download_btn.click()

        # Find the specific Excel link
        logger.info("Locating Excel download link...")
        excel_link_element = wait.until(EC.element_to_be_clickable(
            (By.PARTIAL_LINK_TEXT, "Corn Supply and Demand Spreadsheet (WASDE)")
        ))
        file_url = excel_link_element.get_attribute("href")
        
        logger.info(f"Found file URL: {file_url}")

        # Download the excel file
        response = requests.get(file_url)
        response.raise_for_status()
        
        # Load directly into pandas
        # 'openpyxl' engine is required for .xlsx files (ensure it's in requirements.txt)
        df = pd.read_excel(BytesIO(response.content), sheet_name='Annual Data', skiprows=9)

        # Select specific columns
        target_columns = [
            "Year", "Planted Acres", "Harvested Acres", "Actual Yield",
            "Production", "Stocks", "Exports", "Imports",
            "Total Supply", "Total Usage", "All Dom. Use", "Ending Stocks"
        ]
        
        # Validate columns
        missing_cols = [col for col in target_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Source file is missing expected columns: {missing_cols}")

        df_selected = df[target_columns].copy()

        # Filter years
        current_year = datetime.now().year
        df_selected["Year"] = pd.to_numeric(df_selected["Year"], errors='coerce')
        
        # FIX 4: Correct Year Logic
        # We want data up to the previous year. 
        # Old code: < (current - 1) which EXCLUDED the previous year.
        # Correct logic: <= (current - 1)
        df_clean = df_selected[
            (df_selected["Year"] > 1972) & 
            (df_selected["Year"] <= (current_year - 1))
        ].copy()

        # Sanitize data types
        df_clean = sanitize_data_types(df_clean)

        # Reset index
        df_clean.reset_index(drop=True, inplace=True)
        
        logger.info(f"Scrape successful. Retrieved {len(df_clean)} records.")
        return df_clean

    except Exception as e:
        logger.error(f"Error during scrape: {e}")
        raise e
        
    finally:
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        data = run_scrape()
        print("\n--- Scraped Data Sample ---")
        print(data.head())
    except Exception as e:
        print(f"Failed: {e}")