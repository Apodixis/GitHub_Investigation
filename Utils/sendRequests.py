# Utils/requests.py
import requests
from typing import List, Dict, Optional, Tuple

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
        "bio": node.get("bio"),
        "location": node.get("location"),
        "company": node.get("company"),
        "socialAccounts": normalized_urls,
        "organizations": organizations,
    }

def user_exact_request(
    token: str,
    query: str,
    login: str,
    max_following: int = 100,
    max_followers: int = 100,
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
        print(f"Fetched user payload: {user}")
        if not user:
            break

        # Always normalize the target user (overwrite with latest, or keep first only)
        normalized_user = _normalize_user(user)
        if target_user is None:
            target_user = [normalized_user]
        else:
            # Only keep the first user as target_user
            pass

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
    
    """
    PLACEHOLDER MAKE INTO CALLABLE FUNCTION
    starred_owner_logins = starred_repo_owners(user)
    
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
    """

    #return target_user or {"login": login}, following, followers, starred_owner_logins
    return target_user, following, followers

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
    
    """
    PLACEHOLDER MAKE INTO CALLABLE FUNCTION
    starred_owner_logins = starred_repo_owners(user)
    
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
    """
    
    return user_dicts