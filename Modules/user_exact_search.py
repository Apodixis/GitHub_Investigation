import os, requests, time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import GraphQL query from Utils
try:
    from Utils.GraphQL_Queries import get_user_information_query
except ImportError:
    print("Error: Could not import get_user_information_query from Utils.GraphQL_Queries") #Placeholder

## CONSIDERED FOR FUTURE UPDATES:
## 1) Verify the module import statements functionality for test and primary execution contexts.
## 2) Preprocess followership data to drop users not meeting criteria for futher comparison

try: # Import used when this module is imported elsewhere (primary execution context)
    from Modules.target_enrichment import enrichment_profile_scraping
except ImportError: # Adjust import to facilitate testing within this module 
    from target_enrichment import enrichment_profile_scraping

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def _normalize_user(node: Dict) -> Dict:
    """Convert GraphQL user node to a flat dict including socialAccounts URLs."""
    social_nodes = (node.get("socialAccounts") or {}).get("nodes") or []
    social_urls = {n.get("url") for n in social_nodes if n and n.get("url")}
    
    # Extract organizations (list of org logins)
    organization_nodes = (node.get("organizations") or {}).get("nodes") or []
    organizations = {org.get("login") for org in organization_nodes if org and org.get("login")}
    
    # Always return emails as a set (if present, else empty set)
    email_val = node.get("email")
    emails = set()
    
    if email_val:
        emails.add(email_val)
        
    return {
        "login": node.get("login"),
        "name": node.get("name"),
        "emails": emails,
        "bio": node.get("bio"),
        "location": node.get("location"),
        "company": node.get("company"),
        "socialAccounts": social_urls,
        "organizations": organizations,
    }

def get_followership(
    token: str,
    login: str,
    max_following: int = 500,
    max_followers: int = 500,
    page_size: int = 100,
    social_size: int = 10,
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Inputs: GitHub username (login) and personal access token.
    Outputs: Target user profile dict, list of following, list of followers.
    Method: GitHub GraphQL API with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    
    following: List[Dict] = []
    followers: List[Dict] = []
    target_user: Optional[Dict] = None
    following_cursor: Optional[str] = None
    followers_cursor: Optional[str] = None
    more_following = True
    more_followers = True
    
    query = get_user_information_query()
    while (more_following or more_followers) and (len(following) < max_following or len(followers) < max_followers):
        variables = {
            "login": login,
            "pageSize": min(page_size, 100),
            "socialSize": social_size,
            "followingCursor": following_cursor,
            "followersCursor": followers_cursor,
        }
        response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        payload = response.json()
        
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL error: {payload['errors']}")
        
        user = payload.get("data", {}).get("user")
        #print(f"Fetched user payload: {user}")
        
        if not user:
            break
        
        if target_user is None:
            target_user = _normalize_user(user)
        
        # Following
        following_conn = user["following"]
        following_nodes_raw = following_conn.get("nodes") or []
        following_nodes = [_normalize_user(n) for n in following_nodes_raw]
        
        remaining_following = max_following - len(following)
        if remaining_following > 0:
            following.extend(following_nodes[:remaining_following])
        
        following_cursor = following_conn["pageInfo"]["endCursor"]
        more_following = following_conn["pageInfo"]["hasNextPage"] and len(following) < max_following

        # Followers
        followers_conn = user["followers"]
        followers_nodes_raw = followers_conn.get("nodes") or []
        followers_nodes = [_normalize_user(n) for n in followers_nodes_raw]
        
        remaining_followers = max_followers - len(followers)
        if remaining_followers > 0:
            followers.extend(followers_nodes[:remaining_followers])
        
        followers_cursor = followers_conn["pageInfo"]["endCursor"]
        more_followers = followers_conn["pageInfo"]["hasNextPage"] and len(followers) < max_followers
    
    
    # Extract starred repository owner logins from the last fetched user payload
    starred_owner_logins = []
    try:
        # 'user' comes from the last loop iteration where payload was fetched
        starred = (user or {}).get("starredRepositories") or {}
        edges = starred.get("edges") or []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            owner = node.get("owner") or {}
            owner_login = owner.get("login")
            if owner_login:
                starred_owner_logins.append(owner_login)
    
    except Exception: # Non-critical: if structure not present, leave list empty
        pass
    
    return target_user or {"login": login}, following, followers, starred_owner_logins

def get_mutual_followership(following: List[Dict], followers: List[Dict]):
    """
    Returns target user profile and enriched mutual followers.
    """
    following_logins = {user["login"] for user in following}
    mutuals = [user for user in followers if user["login"] in following_logins]
    
    return mutuals

def user_exact_search(token: str, username: str, start_time=None) -> List[Dict]:
    """
    Input: (1) Target user's name, (2) start_time for measuring execution time of intermediate steps.
    Output: List of unique user dicts with relationship (string) to the searched account and achievements added.
    Method: Membership testing via a mapping dictionary; Append Boolean value to new 'mutual' key.
    Information (per User): Followership, "relationship," (Mutual/Followed by, Follows) and achievements.
    Note: Achievement data is added by the enrichment_profile_scraping() function.
    """
    target_user, following, followers, starred_owner_logins = get_followership(token, username)
    print(f"Starred Owner Logins: {starred_owner_logins}")
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Followership time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)
    
    followership_data = unique_followership(following, followers)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Unique Follower time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)
    
    # Enriches user data with achievements (inaccessible via GraphQL or REST APIs)
    e_user = enrichment_profile_scraping([target_user])
    e_followership = enrichment_profile_scraping(followership_data)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Enrichment time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)
    
    return e_user, e_followership

def unique_followership(following: List[Dict], followers: List[Dict]) -> List[Dict]:
    """
    Input: (1) List of following user dicts, (2) List of followers user dicts.
    Output: List of unique user dicts with relationship (string) to the searched account added.
    Method: Membership testing via a mapping dictionary; Append Boolean value to new 'mutual' key.
    Information (per User): Mutual Followership (True/False) and Relationship label.
    """
    # Build quick membership sets for relationship labeling
    followership = following + followers

    following_set = {u.get("login") for u in following if u.get("login")}
    followers_set = {u.get("login") for u in followers if u.get("login")}

    # Apply relationship labels based on membership
    for user in followership:
        if user["login"] in following_set and user["login"] in followers_set:
            user["relationship"] = "Mutual"
        
        elif user["login"] in following_set:
            user["relationship"] = "Followed by"
        
        elif user["login"] in followers_set:
            user["relationship"] = "Follower of"
    
    return followership

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    ENV_PATH = BASE_DIR / ".." / ".env"
    
    try:
        from dotenv import load_dotenv
        
        if ENV_PATH.exists():
            load_dotenv(dotenv_path=ENV_PATH, override=False)
        else:
            # Optional: warn or raise if the file is expected to exist
            print(f"[env] No env file found at: {ENV_PATH}")
        token = os.getenv("GITHUB_API_TOKEN")
        
    except ImportError:
        # Fallback: if python-dotenv is not installed, you can manually enter your personal access token
        token = input("Enter your GitHub Personal Access Token: ")
    
    '''<------- TEST user_exact_search() OUTPUTS ------->'''
    target_user = input("Enter the GitHub user to research: ").strip()
    start_time = time.perf_counter() # Start time measurement
    
    e_target, e_followership = user_exact_search(token, target_user, start_time)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Total Execution time: {elapsed_time:.4f} seconds") # Prints execution time (without user input delay)
    
    print(f"Enriched Target Profile: {e_target}")
    print(f"Enriched Followership Info: {len(e_followership)}:\n{e_followership}")