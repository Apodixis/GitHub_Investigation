# Utils/requests.py
import requests
from typing import List, Dict, Optional, Tuple
from .dataTransformations import compare_user_relations, starred_repo_owners
from .queries import graphQL_repo_insights_query

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def _normalize_user(node: Dict) -> Dict:
    """Convert GraphQL user node to a flat dict including socialAccounts URLs."""
    social_nodes = (node.get("socialAccounts") or {}).get("nodes") or []
    social_urls = {n.get("url") for n in social_nodes if n and n.get("url")}
    
    normalized_urls = set()
    for url in social_urls:
        """Normalizes URLs by ensuring they use HTTPS, end without punctuation, and do not contain 'www.'"""
        normal_url = url.replace('\xa0', '').rstrip(".,;:<>\"'[]{}-=+!?@#$%^&*()|\\/`~ \n\r") # Clean URL of whitespace and trailing punctuation
        if normal_url[:7] == "http://": # converts http to https
            normal_url = normal_url.replace("http://", "https://", 1)
        if "www." in normal_url: # removes 'www.' if present
            normal_url = normal_url.replace("www.", "")
        normalized_urls.add(normal_url)
    
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
        "socialAccounts": normalized_urls,
        "location": node.get("location"),
        "company": node.get("company"),
        "bio": node.get("bio"),
        "organizations": organizations
    }

def user_exact_request(
    token: str,
    query: str,
    login: str,
    max_following: int = 250,
    max_followers: int = 250,
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
    
    following_cursor: Optional[str] = None
    followers_cursor: Optional[str] = None
    more_following = True
    more_followers = True
    
    while (more_following or more_followers) and (len(following) < max_following or len(followers) < max_followers):
        variables = {
            "login": login,
            "pageSize": min(page_size, 500),
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
        print(f"Fetched user payload: {user}")
        if not user:
            break
        
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
        
        # If no more to fetch, break
        if not (more_following or more_followers):
            break
        
    # Normalize target_user and perform some data transformations
    if user:
        normalized_target = _normalize_user(user)
        
    else:
        normalized_target = None
    
    # Sets user['relation'] value for each user based on followership (mutual, following, follower)
    followership = compare_user_relations(following, followers, normalized_target)
    
    return [normalized_target], followership

def user_exact_results_requests(token: str,
    query: str,
    page_size: int = 100
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Inputs: GitHub usernames (logins) and personal access token.
    Outputs: Target user profile dicts, listing user stargazing information.
    Method: GitHub GraphQL API with pagination.
    Information (per User): Owner & Repository names of starred repositories.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    
    starred_edges = []
    starred_cursor = None
    starred_fetched = 0
    max_starred = 250
    
    while starred_fetched < max_starred:
        variables = {
            "pageSize": min(page_size, 100),
            "starredCursor": starred_cursor
        }
        
        response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        payload = response.json()
        
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL error: {payload['errors']}")
        
        user = payload.get("data", {}).get("user")
        print(f"Fetched user payload: {user}")
        if not user:
            break
        
        # Starred Repositories Pagination
        starred = (user or {}).get("starredRepositories") or {}
        edges = starred.get("edges") or []
        starred_edges.extend(edges)
        starred_cursor = starred.get("pageInfo", {}).get("endCursor")
        more_starred = starred.get("pageInfo", {}).get("hasNextPage", False) and len(starred_edges) < max_starred
        
        # If no more to fetch, break
        if not (more_starred):
            break
    
    # Normalize target_user and perform some data transformations
    if user:
        user["starredRepositories"] = {"edges": starred_edges}
        normalized_target = _normalize_user(user)
        normalized_target['stargazing'] = starred_repo_owners(user)
    
    else:
        normalized_target = None

def starred_repos_request(token: str, query: str) -> Dict:
    """
    
    Sends a POST request to the provided GitHub GraphQL endpoint for starred repositories.
    Args:
        query (str): The REST API URL for the user's starred repositories.
        token (str, optional): GitHub personal access token for authentication.
    Returns:
        list: List of starred repositories (as dicts).
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query}, headers=headers)
    response.raise_for_status()
    return response.json()

#============================================================================================

def user_partial_request(
    token: str,
    query: str,
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
    
    variables = {
            "pageSize": min(page_size, 100),
            "socialSize": social_size,
        }
    
    response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
    response.raise_for_status()
    payload = response.json()
    
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    
    user_dicts = list(payload["data"].values())
    
    print(f"Fetched user payload: {user_dicts}")
    
    return user_dicts

#============================================================================================

# Fetches users who forked and starred repositories for a given user (up to 250 repos, paginated)
def repo_insights_request(token: str, login: str):
    """
    Args:
        token: GitHub personal access token
        query: GraphQL query string from graphQL_repo_insights_query()
        login: GitHub username to pull repo insights for
    Returns:
        (forked_users, starred_users):
            forked_users: list of user logins who have forked any repo
            starred_users: list of user logins who have starred any repo
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    repo_cursor = None
    forked_users = set()
    starred_users = set()
    total_repos = 0
    max_repos = 250
    query = graphQL_repo_insights_query(login)
    
    while total_repos < max_repos:
        variables = {"login": login, "repoCursor": repo_cursor}
        response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        payload = response.json()
        
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL error: {payload['errors']}")
        
        user = payload.get("data", {}).get("user")
        if not user:
            break
        
        repos = user.get("repositories", {}).get("nodes", [])
        for repo in repos:
            
            # Forks
            for fork in repo.get("forks", {}).get("nodes", []):
                owner = fork.get("owner", {})
                login_val = owner.get("login")
                if login_val:
                    forked_users.add(login_val)
            
            # Stargazers
            for stargazer in repo.get("stargazers", {}).get("nodes", []):
                login_val = stargazer.get("login")
                if login_val:
                    starred_users.add(login_val)
        
        total_repos += len(repos)
        page_info = user.get("repositories", {}).get("pageInfo", {})
        
        if page_info.get("hasNextPage") and total_repos < max_repos:
            repo_cursor = page_info.get("endCursor")
            
        else:
            break
    return list(forked_users), list(starred_users)

#============================================================================================

# Sends a POST request to the GitHub GraphQL endpoint for organizations
def organization_request(token: str, target_orgs: List[str]) -> Dict[str, any]:
    """
    Fetches organization info, all repositories, and all members for each organization in org_names.
    Sends requests for up to two orgs at a time, paginating each independently.
    Returns a dict keyed by org login, with org info, repos, and members.
    """
    GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    results = {}
    
    # Process orgs in batches of 2
    for i in range(0, len(target_orgs), 2):
            batch = target_orgs[i:i+2]
            # Initialize per-org state
            org_states = {}
            for idx, org in enumerate(batch):
                    org_states[org] = {
                            "org_info": None,
                            "all_repos": [],
                            "all_members": [],
                            "repo_cursor": None,
                            "member_cursor": None,
                            "repos_done": False,
                            "members_done": False
                    }
            # Paginate until all orgs in batch are done
            while not all(s["repos_done"] and s["members_done"] for s in org_states.values()):
                    # Build query and variables for this batch
                    query = "query organizationRequest("
                    variables = {}
                    query += f"""$repoCursor0: String, $memberCursor0: String, $repoCursor1: String, $memberCursor1: String) {{
                        """
                        
                    for idx, org in enumerate(batch):
                        query +=f"""org{idx}: organization(login: "{org}") {{
                            login name email location websiteUrl createdAt isVerified twitterUsername
                            repositories(first: 100, after: $repoCursor{idx}) {{
                                nodes {{ name description }}
                                pageInfo {{ hasNextPage endCursor }}
                            }}
                            membersWithRole(first: 100, after: $memberCursor{idx}) {{
                                nodes {{ login name email }}
                                pageInfo {{ hasNextPage endCursor }}
                            }}
                        }}
                        """
                        # Set variables for this org
                        state = org_states[org]
                        variables[f"repoCursor{idx}"] = state["repo_cursor"]
                        variables[f"memberCursor{idx}"] = state["member_cursor"]
                    query += "}" #Closes the query string
                    
                    response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
                    response.raise_for_status()
                    data = response.json()["data"]
                    
                    for idx, org in enumerate(batch):
                        org_key = f"org{idx}"
                        org_data = data.get(org_key)
                        if not org_data:
                                org_states[org]["repos_done"] = True
                                org_states[org]["members_done"] = True
                                continue
                            
                        # Org info (only set once)
                        if not org_states[org]["org_info"]:
                                org_states[org]["org_info"] = {k: org_data[k] for k in ["login", "name", "email", "location", "websiteUrl", "createdAt", "isVerified", "twitterUsername"]}
                                
                        # Repos
                        repos = org_data["repositories"]["nodes"]
                        org_states[org]["all_repos"].extend(repos)
                        repo_page = org_data["repositories"]["pageInfo"]
                        if repo_page["hasNextPage"]:
                                org_states[org]["repo_cursor"] = repo_page["endCursor"]
                        else:
                                org_states[org]["repos_done"] = True
                                
                        # Members
                        members = org_data["membersWithRole"]["nodes"]
                        org_states[org]["all_members"].extend(members)
                        member_page = org_data["membersWithRole"]["pageInfo"]
                        if member_page["hasNextPage"]:
                                org_states[org]["member_cursor"] = member_page["endCursor"]
                        else:
                                org_states[org]["members_done"] = True
            
            # Store results for this batch
            for org in batch:
                    results[org] = {
                            "organization": org_states[org]["org_info"],
                            "repositories": org_states[org]["all_repos"],
                            "members": org_states[org]["all_members"]
                    }
    return results