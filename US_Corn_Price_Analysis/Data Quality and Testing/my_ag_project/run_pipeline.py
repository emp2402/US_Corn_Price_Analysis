import subprocess
import sys


def run_command(command, step_name):
    """Runs a shell command and stops the script if it fails."""
    print(f"\n🚀 Starting: {step_name}...")
    print("-" * 40)

    try:
        # shell=True allows us to run the command exactly like in the terminal
        # check=True will raise an error if the command fails (e.g., dbt build fails)
        subprocess.run(command, shell=True, check=True)
        print(f"✅ Success: {step_name} completed!")
    except subprocess.CalledProcessError:
        print(f"\n❌ Error: {step_name} failed. Stopping pipeline.")
        sys.exit(1)


if __name__ == "__main__":
    print("🌽 Starting US Corn Data Pipeline Automation")

    # Step 1: Build & Test (The Quality Gate)
    # If any test fails here, the script stops immediately.
    run_command("dbt build", "dbt Build & Test")

    # Step 2: Generate Documentation
    run_command("dbt docs generate", "Documentation Generation")

    # Step 3: Serve Documentation
    # This command blocks the terminal (keeps running) until you press Ctrl+C
    print("\n🌐 Launching Documentation Website...")
    print("   (Press Ctrl+C to stop the server)")
    run_command("dbt docs serve", "Docs Server")