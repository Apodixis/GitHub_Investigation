# Utils/userRequests.py
import requests
from typing import List, Dict, Optional, Tuple
from .dataTransformations import compare_user_relations, starred_repo_owners
from .queries import graphQL_repo_insights_query

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def _normalize_user(node: Dict) -> Dict:
    """
    Inputs: User dict from GraphQL response.
    Outputs: Normalized user dict.
    Method: Normalizing URLs to eliminate erroneous duplicates in later steps, reduce dimensionality of objects by discarding less relevant information, and reorganizes dict value ordering based on significance for the written output form.
    Information (per User): Convert GraphQL user node to a flat dict including socialAccounts URLs.
    """
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
        "createdAt": node.get("createdAt"),
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
    variables: dict
    ) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Inputs: GitHub username (login), personal access token, and variables dictionary.
    Outputs: Target user profile dict, list of following, list of followers.
    Method: Batched requests to the GitHub GraphQL endpoint for users with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    
    following: List[Dict] = []
    followers: List[Dict] = []
    more_following = True
    more_followers = True
    
    while (more_following or more_followers) and (len(following) < variables.get("max_following") or len(followers) < variables.get("max_followers")):
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
        remaining_following = variables.get("max_following", 250) - len(following)
        if remaining_following > 0:
            following.extend(following_nodes[:remaining_following])
        following_cursor = following_conn["pageInfo"]["endCursor"]
        more_following = following_conn["pageInfo"]["hasNextPage"] and len(following) < variables.get("max_following")
        variables["followingCursor"] = following_cursor
        
        # Followers
        followers_conn = user["followers"]
        followers_nodes_raw = followers_conn.get("nodes") or []
        followers_nodes = [_normalize_user(n) for n in followers_nodes_raw]
        remaining_followers = variables.get("max_followers") - len(followers)
        if remaining_followers > 0:
            followers.extend(followers_nodes[:remaining_followers])
        followers_cursor = followers_conn["pageInfo"]["endCursor"]
        more_followers = followers_conn["pageInfo"]["hasNextPage"] and len(followers) < variables.get("max_followers")
        variables["followersCursor"] = followers_cursor
        
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

def user_bulk_request(token: str, query: str) -> Dict:
    """
    Inputs: GitHub usernames (logins) list and personal access token.
    Outputs: GraphQL response JSON for bulk user queries.
    Method: Batched requests to the GitHub GraphQL endpoint for users.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query}, headers=headers)
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    
    user_dicts = list(payload["data"].values())
    
    normalized_users = [_normalize_user(user) for user in user_dicts if user]
    return normalized_users

def user_exact_results_requests(token: str,
    query: str,
    variables: dict
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Inputs: GitHub username (login), personal access token, and variables dictionary.
    Outputs: Target user profile dicts, listing user stargazing information.
    Method: Batched requests to the GitHub GraphQL endpoint for users with pagination.
    Information (per User): Owner & Repository names of starred repositories.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    
    starred_edges = []
    starred_cursor = variables.get("starredCursor")
    starred_fetched = 0
    max_starred = variables.get("maxStarred", 250)

    while starred_fetched < max_starred:
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
        more_starred = starred.get("pageInfo", {}).get("hasNextPage", False) and len(starred_edges) < variables.get("maxStarred", 250)
        variables["starredCursor"] = starred_cursor
        
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

def starred_repos_request(token: str, query: str, variables: dict = None) -> Dict:
    """
    Inputs: Personal access token, GraphQL query string, and variables dictionary.
    Outputs: GraphQL response JSON: name, description, and stargazerCount (for each repo starred by the input user) and the owner of each starred repo.
    Method: Batched requests to the GitHub GraphQL endpoint for users with pagination.
    Information (per User): Owner & Repository names of starred repositories.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    response = requests.post(GITHUB_GRAPHQL_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

#============================================================================================

def user_partial_request(
    token: str,
    query: str,
    variables: dict
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Inputs: GitHub username (login), personal access token, and variables dictionary.
    Outputs: Target user profile dict, list of following, list of followers.
    Method: Batched requests to the GitHub GraphQL endpoint for users with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    
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
    Inputs: GitHub username (login) and personal access token.
    Outputs: Two lists - (1) Users who have forked any repo, (2) Users who have starred any repo.
    Method: Batched requests to the GitHub GraphQL endpoint for repositories with pagination.
    Information (per Repository): Users who have forked or starred the repository.
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