import os, time # Time used to measure code execution times
from pathlib import Path
from Modules.user_exact_search import *

## CONSIDERED FOR FUTURE UPDATES:
## 1) Implement a scoring module to rank attribution confidence based on multiple factors (e.g., name/email syntax, location, company, social links, achievements, etc.).
## n) Optimize code to reduce time complexity where possible.

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=False)
    else:
        # Optional: warn or raise if the file is expected to exist
        print(f"[env] No env file found at: {ENV_PATH}")
    token = os.getenv("GITHUB_API_TOKEN")
    
except ImportError:
    token = input("Enter your GitHub Personal Access Token: ")

def decision_tree():
    
    print("1) User Followership Lookup (Target Broadening)") # Username (Exact Match)
    print("2) PLACEHOLDER")
    print("3) PLACEHOLDER")
    print("4) PLACEHOLDER")
    
    actions = {
        "1": lambda: user_followership_lookup(token), #Target Broadening
        "2": lambda: print("Placeholder '2' Selected"),
        "3": lambda: print("Placeholder '3' Selected"),
        "4": lambda: print("Placeholder '4' Selected"),
    }
    
    while True:
        choice = input("Enter 1-4: ").strip()
        action = actions.get(choice)
        if action:
            action()
            break
        else:
            print("Invalid selection. Please enter 1, 2, 3, or 4.")

def user_followership_lookup(token):
    '''Broadens target analysis by fetching followership data and returning noteworthy followers:
    (1) Users with a Mutual Followership to the Target User
    (2) Users exhibiting specific attributes (e.g., login & email syntax, company, location)'''
    target_user = input("Enter the GitHub username to analyze: ").strip()
    start_time = time.perf_counter() # Start time measurement
    time.sleep(1)
    user_info = user_exact_search(token, target_user, start_time)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Target User Info: {user_info[0]}")
    print(f"Related User Info: {user_info[1:]}")
    print(f"Execution time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)

if __name__ == '__main__':
    #print(f"GitHub Token: {token}")
    decision_tree()