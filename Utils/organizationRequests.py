# Utils/organizationRequests.py
import requests, math
from typing import List, Dict
from .queries import graphQL_organization_info_query, graphQL_organization_membership_query

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# Sends a POST request to the GitHub GraphQL endpoint for organizations
def organization_info_request(token: str, target_orgs: List[str]) -> Dict[str, any]:
    """
    Inputs: List of GitHub organization names (logins) and personal access token.
    Outputs: Dictionary containing organization info, all repository names, and all members for each organization in target_orgs.
    Method: Batched requests to the GitHub GraphQL endpoint for organizations with pagination.
    Information (per Organization): Organization info, all repositories, and all members.
    """
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
            query = graphQL_organization_info_query(batch)
            variables = {}
                
            for idx, org in enumerate(batch):
                # Set variables for this org
                state = org_states[org]
                variables[f"repoCursor{idx}"] = state["repo_cursor"]
                variables[f"memberCursor{idx}"] = state["member_cursor"]
            
            #Fetches data for this batch
            response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
            response.raise_for_status()
            data = response.json()["data"]
            
            #Handles logic for each org in the batch and changes the loop condition when complete
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
    
    # Build output: first n dicts are org info, then all members as dicts with 'organizations': [org_name]
    output = []
    # Add org info dicts
    for org_name in target_orgs:
        org_info = results.get(org_name, {}).get("organization", {})
        if org_info:
            output.append(org_info)
    # Add member dicts with 'organizations' key, deduplicated by (org_name, login)
    seen = set()
    for org_name in target_orgs:
        members = results.get(org_name, {}).get("members", [])
        for member in members:
            login = member.get("login")
            if (org_name, login) not in seen:
                seen.add((org_name, login))
                member_row = dict(member)  # copy
                member_row["organizations"] = [org_name]
                # Flatten socialAccounts if present
                if "socialAccounts" in member_row and isinstance(member_row["socialAccounts"], dict):
                    urls = [n.get("url") for n in member_row["socialAccounts"].get("nodes", []) if n.get("url")]
                    member_row["socialAccounts"] = urls
                output.append(member_row)
    return output

# Returns user logins that are members of at least 1/3 of the organizations (rounded up)
def organization_membership_request(token: str, target_orgs: List[str]) -> List[str]:
    """
    Inputs: List of GitHub organization names (logins) and personal access token.
    Outputs: List of user logins that are members of at least 1/3 of the organizations (rounded up).
    Method: Uses organization_request to fetch all members, then counts login occurrences.
    """
    headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}
    results = {}
    
    # Process orgs in batches of 2
    for i in range(0, len(target_orgs), 2):
        batch = target_orgs[i:i+2]
        
        # Initialize per-org state
        org_states = {}
        for idx, org in enumerate(batch):
            org_states[org] = {
                "all_members": [],
                "member_cursor": None,
                "members_done": False
            }
        
        # Paginate until all orgs in batch are done
        while not all(s["members_done"] for s in org_states.values()):
            
            # Build query and variables for this batch
            query = graphQL_organization_membership_query(batch)
            variables = {}
                
            for idx, org in enumerate(batch):
                # Set variables for this org
                state = org_states[org]
                variables[f"memberCursor{idx}"] = state["member_cursor"]
            
            #Fetches data for this batch
            response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
            response.raise_for_status()
            data = response.json()["data"]
            
            #Handles logic for each org in the batch and changes the loop condition when complete
            for idx, org in enumerate(batch):
                org_key = f"org{idx}"
                org_data = data.get(org_key)
                if not org_data:
                    org_states[org]["members_done"] = True
                    continue
                
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
            # Extract only the login for each member
            member_logins = {member.get("login") for member in org_states[org]["all_members"] if member.get("login")}
            results[org] = member_logins

    # Count occurrences of each login across all organizations
    login_counts = {}
    for member_list in results.values():
        for login in member_list:
            if login:
                login_counts[login] = login_counts.get(login, 0) + 1
    
    threshold = math.ceil(len(target_orgs) / 3) + 1 # Determines which users are significant relative to the supplied list of target_orgs
    
    return [login for login, count in login_counts.items() if count >= threshold] # Return list of users that meet the organization memberships threshold
