# Modules/userSearch.py

import requests, time

from Utils.queries import graphQL_user_exact_query, graphQL_build_partial_user_query, graphQL_build_stargazing_query, graphQL_build_stargazing_query, graphQL_repo_insights_query
from Utils.sendRequests import user_exact_request, user_partial_request, starred_repos_request, repo_insights_request
from Utils.menus import enrichment_menu
from Utils.dataTransformations import compare_repo_insights
from .targetEnrichment import enrich_user_data

def user_search_exact(token, target_user): # Add user selection before return prompting for enrichment
    """
    Inputs: GitHub username (login) and personal access token.
    Outputs: Target user profile dict, list of following, list of followers.
    Method: GitHub GraphQL API with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    query = graphQL_user_exact_query(target_user) # Fetch the GraphQL query string
    
    target_user, followership = user_exact_request(token, query, target_user)
    
    # ================== BATCHED STARGAZING ENRICHMENT =====================
    
    
    # Collect all user logins to enrich (excluding None logins)
    all_users = target_user + followership
    all_user_logins = [user for user in all_users if user.get('login')]
    batch_size = 5
    
    for i in range(0, len(all_user_logins), batch_size):
        batch = all_user_logins[i:i+batch_size]
        logins = [user['login'] for user in batch]
        
        # Build the GraphQL query for this batch
        query = graphQL_build_stargazing_query(logins)
        
        # Send the GraphQL request for this batch with retry logic
        if i+batch_size < len(all_user_logins):
            print(f"Requesting stargazing data for users: {i+batch_size} of {len(all_user_logins)}")
        else:
            print(f"Requesting stargazing data for users: {len(all_user_logins)} of {len(all_user_logins)}")
        
        max_retries = 3
        attempt = 0
        result = None
        
        while attempt < max_retries:
            try:
                result = starred_repos_request(token, query)
                break  # Success, exit retry loop
            
            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as ce:
                attempt += 1
                print(f"Connection error during stargazing request (attempt {attempt}): {ce}")
                
                if attempt < max_retries:
                    print("Waiting 15 seconds before retrying...")
                    time.sleep(15)
                    
                else:
                    print("Max retries reached. Skipping this batch.")
                    result = {}
                    
        # For each user in the batch, extract their stargazing repos
        for idx, user in enumerate(batch):
            user_key = f'user{idx}'
            user_data = result.get('data', {}).get(user_key, {}) if result else {}
            stargazing = []
            
            try:
                starred = user_data.get('starredRepositories', {})
                nodes = starred.get('nodes', [])
                stargazing = [repo.get('nameWithOwner') for repo in nodes if repo.get('nameWithOwner')]
            
            except Exception:
                pass
            
            user['stargazing'] = stargazing
            
            ''' # COMMENTED OUT FOR NOW - POTENTIAL FUTURE USE
            # Derive insights from stargazing data (Strength of Relationship to Repo Owners): [[repoOwner, count]]
            owners = [name.split('/')[0] for name in stargazing if '/' in name]
            owner_counts = Counter(owners)
            stargazing_insights = [[owner, count] for owner, count in owner_counts.items()]
            stargazing_insights.sort(key=lambda x: x[1], reverse=True)
            user['stargazing_owners'] = stargazing_insights
            '''
            
        # Sleep to mitigate rate limiting
        time.sleep(1)
    
    # For the target_user, adds contextual repo insights based on users that forked and starred target_user-owned repos
    forked_users, starred_users = repo_insights_request(token, all_users[0].get('login'))
    repo_insights = compare_repo_insights(forked_users, starred_users)
    all_users[0]['repo_insights'] = repo_insights
    
    enrich = enrichment_menu()
    
    if enrich == "1":
        e_users = enrich_user_data(all_users)
        return e_users
    
    else:
        return all_users
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
    
    query = graphQL_build_partial_user_query(logins)
    #print(query)
    
    results = user_partial_request(token, query)
    #print(result)
    
    enrich = enrichment_menu()
    
    if enrich == "1":
        e_users = enrich_user_data(results)
        return e_users
    
    else:
        return results