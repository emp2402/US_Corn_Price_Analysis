# US Corn Price Analysis Pipeline

This project implements an end-to-end data engineering pipeline for analyzing US Corn prices between the years 1973 and 2024. It automates data extraction, transformation using dbt (data build tool), and structured data quality validation.

## Architecture
The pipeline is modular by design and divided into four main phases:

### 0. Environment Setup and Dependency Installation
- This phase only needs to be run once and installs the dependencies needed for subsequent phases

### 1. Data Scraping
- Scrapes or fetches raw US corn price data
- Uploads the data into **Google BigQuery**
- Implemented in Python

### 2. Data Transformation
- Uses **dbt** to clean, model, and aggregate raw data
- Produces analytics-ready tables
- Includes dbt tests, seeds, and snapshots

### 3. Data Quality & Testing
- Independent validation layer in **dbt**
- Runs regression checks and data integrity tests
- Designed to be executed after transformations have completed


------


## Prerequisites

- **Operating System**:  
  - Windows (the orchestration relies on a `.bat` file)  

- **Python**:  
  - Version **3.8+**

- **Google Cloud**:
  - A valid **service account key** with BigQuery access will be provided in the source code under the `./keys/` folder and deactivated upon grading of this project 


------


## Installation & Setup

### 1. GitLab Repository Method

```bash
git clone https://gitlab.com/commodities-analysis/US_Corn_Price_Analysis
cd US_Corn_Price_Analysis
```

### 2. Google Drive Method

- If running the project from a Google Drive File, start by downloading the folder and making sure it is unziped
- Open the `US_Corn_Price_Analysis` file by double clicking the folder
- You should now be in the same position as if you had cloned the repository. All steps are identical from this point onwards

------


## How to Run the Pipeline

- Inside the 1 `./US_Corn_Price_Analysis/` folder you will see a `run_project.bat` file
- Double clicking on this file will open the terminal and begin execution of the project
- The user has the option to select which data sources they would like to run/update via onscreen prompts
- The rest of the jobs will proceed automatically
- If you would like to break the process, you can press `ctl + c` to interrupt 
- The entire pipeline is orchestrated via a single script.

**Please note, it is normal for the program to open your local Chrome browser to perform the scraping operations. The browser windows will close automatically**


------


## Project Structure

US_CORN_PRICE_ANALYSIS/
│
├── .idea/                         # IDE configuration
│
├── Data Quality and Testing/
│   ├── logs/                      # Quality pipeline logs
│   └── my_ag_project/
│       ├── analyses/              # dbt analyses
│       ├── macros/                # Custom dbt macros
│       ├── models/                # Quality-focused dbt models
│       ├── snapshots/             # dbt snapshots
│       ├── tests/                 # dbt tests
│       ├── .gitignore
│       ├── dbt_project.yml
│       ├── package-lock.yml
│       ├── packages.yml
│       ├── README.md
│       └── run_pipeline.py        # Quality & validation entry point
│
├── data_ingestion/
│   └── src/
│       ├── scrape_functions/      # Web scraping utilities
│       ├── bigquery_api_client.py # BigQuery upload logic
│       ├── project.ipynb          # Exploration / prototyping
│       └── web_scrape_controller.py
│
├── data_transformation/
│   ├── dbt_packages/              # Installed dbt packages
│   ├── logs/                      # dbt logs
│   ├── models/                    # Core transformation models
│   ├── seeds/                     # Static seed data
│   ├── target/                    # dbt compiled artifacts
│   ├── tests/                     # dbt tests
│   ├── .user.yml
│   ├── dbt_project.yml
│   └── profiles.yml
│
├── eda/                           # Exploratory data analysis
├── keys/                          # GCP service account keys (ignored)
│
├── main.py                        # Ingestion entry point
├── setup_env.py                   # Environment setup helper
├── run_project.bat                # Windows orchestration script
├── run_project.sh                 # Unix-based orchestration script
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation


------