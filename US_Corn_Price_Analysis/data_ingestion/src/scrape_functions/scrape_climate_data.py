import logging
import requests
import pandas as pd
import time
from io import BytesIO
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger(__name__)

def parse_noaa_csv(content, metric_name):
    """
    Parses the NOAA NClimGrid wide-format CSV.
    Format detected: [ID, GeoID, Name, Year, Month, Metric, Day1, Day2, ... Day31]
    """
    # Read without header because the first row is actually data, not headers
    df = pd.read_csv(BytesIO(content), header=None)
    
    # Verify we have enough columns (Metadata takes 6 columns)
    if df.shape[1] < 7:
        return pd.DataFrame()

    # Extract Metadata
    year = df.iloc[0, 3]
    month = df.iloc[0, 4]
    
    # Extract Daily Data (Column 6 to End)
    # values represents [Day1, Day2, ..., Day31]
    daily_values = df.iloc[0, 6:].values
    
    records = []
    for day_idx, value in enumerate(daily_values):
        day = day_idx + 1
        
        # Filter out missing/fill values often used by NOAA (-999.99)
        if value <= -999:
            continue
            
        try:
            # Create a valid date object
            # This automatically handles months with < 31 days (raises ValueError for Feb 30, etc.)
            date_obj = datetime(year=int(year), month=int(month), day=day)
            
            records.append({
                "date": date_obj,
                metric_name: float(value)
            })
        except ValueError:
            # This catches "Day 31" in a month with only 30 days, etc.
            continue
            
    return pd.DataFrame(records)

def run_scrape():
    """
    Scrapes daily Precipitation (prcp) and Max Temperature (tmax) 
    from NOAA NClimGrid averages (CONUS scaled).
    Range: 1973 to 2024 (Previous Year).
    """
    logger.info("Starting Climate Data scrape (NOAA NClimGrid)...")
    
    base_url = "https://www.ncei.noaa.gov/data/nclimgrid-daily/access/averages"
    
    start_year = 1973
    current_year = datetime.now().year
    end_year = 2024
    
    combined_data = []
    
    # NOAA blocks standard python requests, so we spoof the User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    logger.info(f"Processing years {start_year} to {end_year}...")

    for year in range(start_year, end_year + 1):
        year_start_time = time.time()
        
        for month in range(1, 13):
            month_str = f"{month:02d}"
            
            # Construct URLs
            prcp_url = f"{base_url}/{year}/prcp-{year}{month_str}-cns-scaled.csv"
            tmax_url = f"{base_url}/{year}/tmax-{year}{month_str}-cns-scaled.csv"

            try:
                # --- Fetch & Parse Precipitation ---
                r_prcp = requests.get(prcp_url, headers=headers)
                if r_prcp.status_code == 200:
                    df_prcp = parse_noaa_csv(r_prcp.content, "Precipitation")
                else:
                    logger.warning(f"Missing PRCP for {year}-{month_str}")
                    df_prcp = pd.DataFrame()

                # --- Fetch & Parse Max Temp ---
                r_tmax = requests.get(tmax_url, headers=headers)
                if r_tmax.status_code == 200:
                    df_tmax = parse_noaa_csv(r_tmax.content, "Max_Temp")
                else:
                    df_tmax = pd.DataFrame()

                # --- Merge Data ---
                # If we have both, merge on date. If we miss one, keep what we have.
                if not df_prcp.empty and not df_tmax.empty:
                    df_merged = pd.merge(df_prcp, df_tmax, on='date', how='outer')
                elif not df_prcp.empty:
                    df_merged = df_prcp
                    df_merged['Max_Temp'] = None
                elif not df_tmax.empty:
                    df_merged = df_tmax
                    df_merged['Precipitation'] = None
                else:
                    continue

                combined_data.append(df_merged)

            except Exception as e:
                logger.error(f"Error processing {year}-{month_str}: {e}")
        
        # Polite pause
        logger.info(f"Finished {year} in {time.time() - year_start_time:.2f}s")
        time.sleep(1)

    if not combined_data:
        raise ValueError("No climate data was collected.")

    final_df = pd.concat(combined_data, ignore_index=True)
    
    # Ensure date is sorted
    final_df['date'] = pd.to_datetime(final_df['date'])
    final_df.sort_values(by='date', inplace=True)
    
    logger.info(f"Climate Scrape Complete. Total records: {len(final_df)}")
    return final_df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        data = run_scrape()
        print("\n--- Scraped Data Sample ---")
        print(data.head())
    except Exception as e:
        print(f"Failed: {e}")