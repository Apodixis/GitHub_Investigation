import requests

from Utils.GraphQL_Queries import graphQL_user_exact_query, build_partial_user_query
from Utils.sendRequests import user_exact_request, user_partial_request
from Utils.menus import enrichment_menu
from .target_enrichment import enrich_user_data

def user_search_exact(token, target_user): # Add user selection before return prompting for enrichment
    """
    Inputs: GitHub username (login) and personal access token.
    Outputs: Target user profile dict, list of following, list of followers.
    Method: GitHub GraphQL API with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    query = graphQL_user_exact_query(target_user) # Fetch the GraphQL query string
    user, following, followers = user_exact_request(token, query, target_user)
    
    enrich = enrichment_menu()
    
    if enrich == "1":
        e_users = enrich_user_data(user+following+followers)
        return e_users
        #return user, following, followers # PLACEHOLDER
    
    else:
        return user+following+followers

#=============================================================================================

def user_search_partial(token, target_user):
    """
    Search GitHub users by partial match using the REST API /search/users endpoint.
    Args:
        target_user (str): The partial username to search for.
        github_token (str, optional): GitHub personal access token for authentication (recommended for higher rate limits).
    Returns:
        dict: The JSON response from GitHub containing user matches.
    """
    url = f"https://api.github.com/search/users?q={target_user}+in:login&per_page=100"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    users = response.json()
    
    logins = []
    for user in users.get("items", []):
        if user.get("type") == "User":
            logins.append(user["login"])
        else:
            continue
    #print(f"users: {logins}")
    
    query = build_partial_user_query(logins)
    #print(query)
    
    results = user_partial_request(token, query)
    #print(result)
    
    enrich = enrichment_menu()
    
    if enrich == "1":
        e_users = enrich_user_data(results)
        return e_users
    
    else:
        return results