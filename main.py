import os, time # Time used to measure code execution times
from pathlib import Path
from Modules.search import user_search_exact, user_search_partial
from Utils.menus import search_mode_menu, clearTerminal

## CONSIDERED FOR FUTURE UPDATES:
## 1) Implement a scoring module to rank attribution confidence based on multiple factors (e.g., name/email syntax, location, company, social links, achievements, etc.).
## n) Optimize code to reduce time complexity where possible.

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        # Optional: warn or raise if the file is expected to exist
        print(f"[env] No env file found at: {ENV_PATH}")
    token = os.getenv("GITHUB_API_TOKEN")
    
except ImportError:
    token = input("Enter your GitHub Personal Access Token: ")

def _decision_tree():
    clearTerminal()
    
    print("1) User Search")
    print("2) PLACEHOLDER")
    print("3) PLACEHOLDER")
    print("4) PLACEHOLDER")
    
    actions = {
        "1": lambda: user_search(token), 
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

def user_search(token):
    '''Broadens target analysis by fetching followership data and returning noteworthy followers:
    1. Exact: Returns info on the input user and their followership and stargazing relationships
    2. Partial: Searches for users with similar names to the search string and returns their profile info'''
    
    search_mode = search_mode_menu()
    clearTerminal()
    
    target_user = input("Enter the GitHub username to analyze: ").strip()
    clearTerminal()
    
    start_time = time.perf_counter() # Start time measurement
    
    if search_mode == "1":
        user_data = user_search_exact(token, target_user) # ADD FUTURE ENRICHMENT FUNCTIONS HERE
        
        print(user_data)
        
    elif search_mode == "2":
        result = set()
        result = user_search_partial(token, target_user)
        print(result)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)

if __name__ == '__main__':
    #print(f"GitHub Token: {token}")
    _decision_tree()