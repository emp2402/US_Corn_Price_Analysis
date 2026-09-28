import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from io import StringIO
import time

# Configure module-level logger
logger = logging.getLogger(__name__)

def run_scrape():
    """
    Scrapes Corn Condition data (WEEKLY) from USDA QuickStats.
    
    Returns:
        pd.DataFrame: DataFrame containing weekly corn condition ratings.
    """
    logger.info("Starting Corn Condition scrape (USDA Quickstats)...")

    # Configure Chrome to run headless
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://www.quickstats.nass.usda.gov/"
        driver.get(url)
        wait = WebDriverWait(driver, 60)

        logger.info("Waiting for Record Count element to appear in DOM...")
        wait.until(EC.presence_of_element_located((By.ID, "status_go")))
        time.sleep(2)
        
        # --- PHASE 1: INITIAL FILTERING ---
        selection_map = [
            ("sector_desc", "CROPS"),
            ("group_desc", "FIELD CROPS"),
            ("commodity_desc", "CORN"),
            ("statisticcat_desc", "CONDITION"),
            ("agg_level_desc", "NATIONAL")
        ]

        for dropdown_id, value in selection_map:
            logger.info(f"Selecting {value} in {dropdown_id}...")

            # Ensure the dropdown itself is clickable
            wait.until(EC.element_to_be_clickable((By.ID, dropdown_id)))

            # Capture record count
            record_element = driver.find_element(By.ID, "status_go")
            current_records = int(record_element.text.split()[0].replace(",", ""))

            select_element = driver.find_element(By.ID, dropdown_id)
            Select(select_element).select_by_value(value)

            # Wait for update
            try:
                wait.until(
                    lambda d: int(d.find_element(By.ID, "status_go").text.split()[0].replace(",", "")) != current_records
                )
            except:
                logger.warning(f"Record count did not change for {value}. Proceeding...")

        # --- PHASE 2: SELECT YEARS & FREQUENCY ---
        
        # 1. Select Years (1986 to Last Year)
        logger.info("Selecting years...")
        wait.until(EC.visibility_of_element_located((By.ID, "year")))
        year_dropdown = Select(driver.find_element(By.ID, "year"))

        current_year = datetime.now().year
        cutoff_year = current_year - 1
        
        selected_count = 0
        for option in year_dropdown.options:
            try:
                year_val = int(option.text)
                # Logic: 1986 <= Year <= (Current Year - 1)
                if 1986 <= year_val <= cutoff_year:
                    year_dropdown.select_by_value(option.get_attribute("value"))
                    selected_count += 1
            except ValueError:
                continue

        if selected_count == 0:
            logger.warning(f"No years selected! Check if data is available up to {cutoff_year}.")

        # Wait for update after year selection
        record_element = driver.find_element(By.ID, "status_go")
        current_records = int(record_element.text.split()[0].replace(",", ""))
        try:
             wait.until(
                lambda d: int(d.find_element(By.ID, "status_go").text.split()[0].replace(",", "")) != current_records
            )
        except:
             pass

        # 2. Select Frequency (WEEKLY)
        logger.info("Selecting Weekly frequency...")
        
        wait.until(EC.presence_of_element_located((By.ID, "freq_desc")))
        wait.until(lambda d: any(o.get_attribute("value") == "WEEKLY" for o in d.find_elements(By.CSS_SELECTOR, "#freq_desc option")))
        
        freq_dropdown = Select(driver.find_element(By.ID, "freq_desc"))
        freq_dropdown.select_by_value("WEEKLY")
        
        # Verify selection
        wait.until(lambda d: Select(d.find_element(By.ID, "freq_desc")).first_selected_option.get_attribute("value") == "WEEKLY")

        # --- PHASE 3: EXTRACT DATA ---
        logger.info("Submitting query...")
        submit_btn = driver.find_element(By.ID, "submit001_label")
        submit_btn.click()

        # Wait for results
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Printable")))
        driver.find_element(By.PARTIAL_LINK_TEXT, "Printable").click()

        # Handle new tab/window if necessary
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        logger.info("Parsing results table...")
        tables = pd.read_html(StringIO(driver.page_source))
        
        if not tables:
            raise ValueError("No tables found in the result page.")

        df = tables[0]
        
        # Cleanup empty rows
        df = df.dropna(how='all')

        logger.info(f"Scrape successful. Retrieved {len(df)} records.")
        return df

    except Exception as e:
        logger.error(f"Error during Corn Condition scrape: {e}")
        raise e
        
    finally:
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = run_scrape()
    print("\n--- Scraped Data Sample ---")
    print(data.head())