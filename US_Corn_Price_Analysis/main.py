# main.py
from data_ingestion.src.web_scrape_controller import run_ingestion_pipeline
import json
import sys

# Define the menu options mapping (Display Name -> Job ID)
MENU_OPTIONS = {
    "1": {"id": "supply",     "label": "Corn Supply & Demand"},
    "2": {"id": "conditions", "label": "Corn Conditions"},
    "3": {"id": "plantings",  "label": "Corn Plantings"},
    "4": {"id": "climate",    "label": "Climate Data"},
    "5": {"id": "prices",     "label": "Corn Prices"}
}

def interactive_menu():
    """Displays a menu and returns a list of selected job IDs."""
    print("\n" + "="*40)
    print("      🌽 US CORN DATA INGESTION MENU      ")
    print("="*40)
    print("Select which datasets to update (e.g., 1,3,5)")
    print("Leave empty and hit ENTER to run ALL.")
    print("Type 'Exit' to terminate the program.")
    print("-" * 40)
    
    for key, val in MENU_OPTIONS.items():
        print(f" [{key}] {val['label']}")
    print("="*40)

    # Get user input
    choice = input("Enter selection: ").strip()

    # Logic: Empty input = Run All
    if not choice:
        print("\n> No selection made. Running ALL jobs...")
        return []

    # Check for exit command
    if choice.lower() == "exit":
        print("\n> Exiting program. Goodbye!")
        sys.exit(0)

    # Parse inputs (e.g., "1, 3, 5" -> ["supply", "plantings", "prices"])
    selected_ids = []
    # Split by comma, remove spaces
    user_selections = [x.strip() for x in choice.split(',')]

    for selection in user_selections:
        if selection in MENU_OPTIONS:
            selected_ids.append(MENU_OPTIONS[selection]["id"])
        else:
            print(f"> ⚠️  Warning: '{selection}' is not a valid option. Skipping.")

    return selected_ids

if __name__ == "__main__":
    
    # 1. Check for Command Line Arguments
    if len(sys.argv) > 1:
        selected_jobs = sys.argv[1:]
    else:
        selected_jobs = interactive_menu()

    # 2. Execution
    # If interactive menu returned empty list but user typed something invalid, we might want to exit.
    # But our logic above returns [] for "Run All", so we just pass it through.
    
    if selected_jobs:
        print(f"\n> Queuing jobs: {selected_jobs}")
    
    report = run_ingestion_pipeline(jobs=selected_jobs)

    # Pretty print the Scraping and Transformation JSON report
    print("\n--- PIPELINE REPORT ---")
    print(json.dumps(report, indent=4, default=str))