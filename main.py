# main.py
import os, time # Time used to measure code execution times
from pathlib import Path
from Modules.userSearch import user_search_exact, user_search_partial
from Modules.organizationSearch import organization_search_info, organization_search_intersection
from Utils.menus import user_search_mode_menu, organization_search_mode_menu, clearTerminal
from Utils.writeToFile import write_user_search_exact_to_excel

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
    print("2) Organization Search")
    print("3) PLACEHOLDER")
    print("4) PLACEHOLDER")
    
    actions = {
        "1": lambda: user_search(token), 
        "2": lambda: organization_search(token),
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
    '''
    Broadens target analysis by fetching followership data and returning noteworthy followers:
    1. Exact: Returns info on the input user and their followership and stargazing relationships
    2. Partial: Returns info for users with similar names to the search string and returns their profile info
    '''
    search_mode = user_search_mode_menu()
    clearTerminal()
    
    target_user = input("Enter the GitHub username to analyze: ").strip()
    clearTerminal()
    
    start_time = time.perf_counter() # Start time measurement
    
    if search_mode == "1":
        user_data = user_search_exact(token, target_user) # ADD FUTURE ENRICHMENT FUNCTIONS HERE
        print(user_data)
        
    elif search_mode == "2":
        user_data = set()
        user_data = user_search_partial(token, target_user)
        print(user_data)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    
    try:
        clearTerminal()
        write_user_search_exact_to_excel(user_data, target_user)
        print(f"Results saved to Excel in your Downloads folder.")
    
    except Exception as e:
        clearTerminal()
        print(f"Error saving results to Excel: {e}")
        print(user_data)
        
    print(f"Execution time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)

def organization_search(token):
    '''
    Broadens target analysis by fetching organization and membership data:
    1. Organization(s): Returns information on the input organization(s) and the members of each input organization: (Members + Info, Repos, Contributors)
    2. Member Intersection: Returns users that are members of multiple organizations from the input organization names (Member Info)
    '''
    search_mode = organization_search_mode_menu()
    
    #Builds a list of target organizations from user input
    target_orgs = []
    while True:
        target_org = input("Enter the GitHub organization to analyze (leave blank to finish): ").strip()
        if not target_org:
            break
        target_orgs.append(target_org)
    
    start_time = time.perf_counter() # Start time measurement
    
    if search_mode == "1":
        org_data = organization_search_info(token, target_orgs) # ADD FUTURE ENRICHMENT FUNCTIONS HERE
        
        clearTerminal()
        print(org_data)
        
    elif search_mode == "2":
        org_data = organization_search_intersection(token, target_orgs)
        
        clearTerminal()
        print(org_data)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)

if __name__ == '__main__':
    #print(f"GitHub Token: {token}")
    _decision_tree()