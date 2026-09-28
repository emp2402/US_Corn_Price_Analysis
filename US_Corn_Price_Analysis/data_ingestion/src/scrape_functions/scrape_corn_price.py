import logging
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from io import StringIO

# Configure module-level logger
logger = logging.getLogger(__name__)

def run_scrape():
    """
    Scrapes Corn Price data from USDA QuickStats.
    """
    logger.info("Starting Corn Price scrape (USDA Quickstats)...")

    # --- DEBUG SETTINGS ---
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # <--- COMMENTED OUT FOR DEBUGGING
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://www.quickstats.nass.usda.gov/"
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Increased wait time for slow government servers
        wait = WebDriverWait(driver, 60)

        # --- FIX: ROBUST INITIAL WAIT ---
        # 1. Wait for the 'status_go' to be PRESENT in the DOM (lenient check)
        #    'visibility_of' requires it to have height/width, which might lag.
        logger.info("Waiting for Record Count element to appear in DOM...")
        wait.until(EC.presence_of_element_located((By.ID, "status_go")))
        
        # 2. Small pause to allow visual rendering to catch up
        time.sleep(2)

        # --- PHASE 1: INITIAL FILTERING ---
        selection_map = [
            ("sector_desc", "CROPS"),
            ("group_desc", "FIELD CROPS"),
            ("commodity_desc", "CORN"),
            ("statisticcat_desc", "PRICE RECEIVED"),
            ("short_desc", "CORN, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU"),
            ("agg_level_desc", "NATIONAL")
        ]

        for dropdown_id, value in selection_map:
            logger.info(f"Selecting {value} in {dropdown_id}...")

            # Ensure the dropdown itself is clickable
            wait.until(EC.element_to_be_clickable((By.ID, dropdown_id)))
            
            # Capture current record count BEFORE selection
            # Use 'presence' here too to be safe
            record_element = wait.until(EC.presence_of_element_located((By.ID, "status_go")))
            current_records = int(record_element.text.split()[0].replace(",", ""))

            # Select the option
            select_element = driver.find_element(By.ID, dropdown_id)
            Select(select_element).select_by_value(value)

            # Wait for the record count to CHANGE
            # This confirms the site processed the click
            try:
                wait.until(
                    lambda d: int(d.find_element(By.ID, "status_go").text.split()[0].replace(",", "")) != current_records
                )
            except Exception:
                logger.warning(f"Record count didn't update for {value} (might be unchanged). Continuing...")

        #     # --- PHASE 2: SELECT YEARS & FREQUENCY ---
        # Now that the main filters are set, we select Years and Frequency (Monthly).
        
        # 1. Select Years (1973 to Present)
        logger.info("Selecting years...")
        wait.until(EC.visibility_of_element_located((By.ID, "year")))
        year_dropdown = Select(driver.find_element(By.ID, "year"))
        
        current_year = datetime.now().year
        cutoff_year = current_year - 1
        selected_count = 0
        # Loop through options in the dropdown and select if they fall in our range
        for option in year_dropdown.options:
            try:
                year_val = int(option.text)
                if 1973 <= year_val <= cutoff_year:
                    if not option.is_selected():
                        # We don't use select_by_value here because we are multi-selecting
                        # Using click() with holding CTRL is standard, but USDA dropdown often accepts sequential clicks
                        # Or we iterate and use select_by_value. 
                        # Faster approach for USDA multiple select:
                        year_dropdown.select_by_value(option.get_attribute("value"))
            except ValueError:
                continue

        if selected_count == 0:
            logger.warning(f"No years selected! Check if data is available up to {cutoff_year}.")

        # 2. Select Frequency (Monthly)
        logger.info("Selecting Monthly frequency...")
        
        # Often the 'freq_desc' dropdown needs to be re-located after year selection
        wait.until(EC.presence_of_element_located((By.ID, "freq_desc")))
        
        # Wait for "MONTHLY" to actually appear in the DOM
        wait.until(lambda d: any(o.get_attribute("value") == "MONTHLY" for o in d.find_elements(By.CSS_SELECTOR, "#freq_desc option")))
        
        freq_dropdown = Select(driver.find_element(By.ID, "freq_desc"))
        freq_dropdown.select_by_value("MONTHLY")

        # Verify it stuck
        wait.until(lambda d: Select(d.find_element(By.ID, "freq_desc")).first_selected_option.get_attribute("value") == "MONTHLY")

        # --- PHASE 3: RE-VERIFY NATIONAL ---
        # USDA Quickstats often resets 'agg_level_desc' when Frequency changes.
        logger.info("Re-verifying National aggregation...")
        
        wait.until(EC.presence_of_element_located((By.ID, "agg_level_desc")))
        wait.until(lambda d: any(o.get_attribute("value") == "NATIONAL" for o in d.find_elements(By.CSS_SELECTOR, "#agg_level_desc option")))
        
        agg_select = Select(driver.find_element(By.ID, "agg_level_desc"))
        if agg_select.first_selected_option.get_attribute("value") != "NATIONAL":
             agg_select.select_by_value("NATIONAL")

        # --- PHASE 4: EXTRACT DATA ---
        logger.info("Submitting query...")
        submit_btn = driver.find_element(By.ID, "submit001_label")
        submit_btn.click()

        # Wait for "Printable" link which indicates results are ready
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Printable")))
        
        # Click printable to get a clean page
        driver.find_element(By.PARTIAL_LINK_TEXT, "Printable").click()
        
        # Switch to the new tab (Printable opens in new window usually)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # Parse table with Pandas
        logger.info("Parsing results table...")
        tables = pd.read_html(StringIO(driver.page_source))
        
        if not tables:
            raise ValueError("No tables found in the result page.")
            
        df = tables[0]
        
        # Basic Cleanup
        # USDA sometimes returns metadata rows at the bottom
        df = df.dropna(how='all') 
        
        logger.info(f"Scrape successful. Retrieved {len(df)} records.")
        return df

    except Exception as e:
        logger.error(f"Error during Corn Price scrape: {e}")
        raise e
        
    finally:
        driver.quit()


# def run_scrape():
    # """
    # Scrapes Corn Price data from USDA QuickStats.
    
    # Returns:
    #     pd.DataFrame: DataFrame containing monthly corn prices.
    # """
    # logger.info("Starting Corn Price scrape (USDA Quickstats)...")

    # # Configure Chrome to run headless
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")

    # driver = webdriver.Chrome(options=chrome_options)
    
    # try:
    #     url = "https://www.quickstats.nass.usda.gov/"
    #     driver.get(url)
    #     wait = WebDriverWait(driver, 30)

    #     # --- PHASE 1: INITIAL FILTERING ---
    #     # We select the broad categories first.
    #     # The site refreshes the record count (id="status_go") after every selection.
    #     logger.info("Waiting for page to fully load...")
    #     wait.until(EC.visibility_of_element_located((By.ID, "status_go")))

    #     selection_map = [
    #         ("sector_desc", "CROPS"),
    #         ("group_desc", "FIELD CROPS"),
    #         ("commodity_desc", "CORN"),
    #         ("statisticcat_desc", "PRICE RECEIVED"),
    #         ("short_desc", "CORN, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU"),
    #         ("agg_level_desc", "NATIONAL")
    #     ]

    #     for dropdown_id, value in selection_map:
    #         logger.info(f"Selecting {value} in {dropdown_id}...")

    #         # Capture current record count to detect when update happens
    #         record_element = wait.until(EC.visibility_of_element_located((By.ID, "status_go")))
    #         current_records = int(record_element.text.split()[0].replace(",", ""))

    #         # Wait for dropdown to be ready
    #         wait.until(EC.visibility_of_element_located((By.ID, dropdown_id)))
            
    #         # Select the option
    #         select_element = driver.find_element(By.ID, dropdown_id)
    #         Select(select_element).select_by_value(value)

    #         # Wait for the site to process (record count must change)
    #         # USDA Quickstats logic: if you filter, records usually decrease.
    #         # If they don't change (rare), the timeout catches it.
    #         try:
    #             wait.until(
    #                 lambda d: int(d.find_element(By.ID, "status_go").text.split()[0].replace(",", "")) != current_records
    #             )
    #         except:
    #             logger.warning(f"Record count did not change for {value}. Proceeding anyway...")

    #     # --- PHASE 2: SELECT YEARS & FREQUENCY ---
    #     # Now that the main filters are set, we select Years and Frequency (Monthly).
        
    #     # 1. Select Years (1973 to Present)
    #     logger.info("Selecting years...")
    #     wait.until(EC.visibility_of_element_located((By.ID, "year")))
    #     year_dropdown = Select(driver.find_element(By.ID, "year"))
        
    #     current_year = datetime.now().year
    #     cutoff_year = current_year - 1
    #     selected_count = 0
    #     # Loop through options in the dropdown and select if they fall in our range
    #     for option in year_dropdown.options:
    #         try:
    #             year_val = int(option.text)
    #             if 1973 <= year_val <= cutoff_year:
    #                 if not option.is_selected():
    #                     # We don't use select_by_value here because we are multi-selecting
    #                     # Using click() with holding CTRL is standard, but USDA dropdown often accepts sequential clicks
    #                     # Or we iterate and use select_by_value. 
    #                     # Faster approach for USDA multiple select:
    #                     year_dropdown.select_by_value(option.get_attribute("value"))
    #         except ValueError:
    #             continue

    #     if selected_count == 0:
    #         logger.warning(f"No years selected! Check if data is available up to {cutoff_year}.")

    #     # 2. Select Frequency (Monthly)
    #     logger.info("Selecting Monthly frequency...")
        
    #     # Often the 'freq_desc' dropdown needs to be re-located after year selection
    #     wait.until(EC.presence_of_element_located((By.ID, "freq_desc")))
        
    #     # Wait for "MONTHLY" to actually appear in the DOM
    #     wait.until(lambda d: any(o.get_attribute("value") == "MONTHLY" for o in d.find_elements(By.CSS_SELECTOR, "#freq_desc option")))
        
    #     freq_dropdown = Select(driver.find_element(By.ID, "freq_desc"))
    #     freq_dropdown.select_by_value("MONTHLY")

    #     # Verify it stuck
    #     wait.until(lambda d: Select(d.find_element(By.ID, "freq_desc")).first_selected_option.get_attribute("value") == "MONTHLY")

    #     # --- PHASE 3: RE-VERIFY NATIONAL ---
    #     # USDA Quickstats often resets 'agg_level_desc' when Frequency changes.
    #     logger.info("Re-verifying National aggregation...")
        
    #     wait.until(EC.presence_of_element_located((By.ID, "agg_level_desc")))
    #     wait.until(lambda d: any(o.get_attribute("value") == "NATIONAL" for o in d.find_elements(By.CSS_SELECTOR, "#agg_level_desc option")))
        
    #     agg_select = Select(driver.find_element(By.ID, "agg_level_desc"))
    #     if agg_select.first_selected_option.get_attribute("value") != "NATIONAL":
    #          agg_select.select_by_value("NATIONAL")

    #     # --- PHASE 4: EXTRACT DATA ---
    #     logger.info("Submitting query...")
    #     submit_btn = driver.find_element(By.ID, "submit001_label")
    #     submit_btn.click()

    #     # Wait for "Printable" link which indicates results are ready
    #     wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Printable")))
        
    #     # Click printable to get a clean page
    #     driver.find_element(By.PARTIAL_LINK_TEXT, "Printable").click()
        
    #     # Switch to the new tab (Printable opens in new window usually)
    #     if len(driver.window_handles) > 1:
    #         driver.switch_to.window(driver.window_handles[-1])

    #     # Parse table with Pandas
    #     logger.info("Parsing results table...")
    #     tables = pd.read_html(driver.page_source)
        
    #     if not tables:
    #         raise ValueError("No tables found in the result page.")
            
    #     df = tables[0]
        
    #     # Basic Cleanup
    #     # USDA sometimes returns metadata rows at the bottom
    #     df = df.dropna(how='all') 
        
    #     logger.info(f"Scrape successful. Retrieved {len(df)} records.")
    #     return df

    # except Exception as e:
    #     logger.error(f"Error during Corn Price scrape: {e}")
    #     raise e
        
    # finally:
    #     driver.quit()


# Allow running this file directly for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = run_scrape()
    print("\n--- Scraped Data Sample ---")
    print(data.head())

    