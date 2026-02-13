# Modules/organizationSearch.py
from Utils.queries import graphQL_build_bulk_user_query
from Utils.organizationRequests import organization_info_request, organization_membership_request
from Utils.userRequests import user_bulk_request

def organization_search_info(token: str, target_orgs: list) -> dict: # Add organization selection before return prompting for enrichment
    """
    Inputs: GitHub organization (login) and personal access token.
    Outputs: Target org info, dictionary of members, list of followers.
    Method: GitHub GraphQL API with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    org_info = organization_info_request(token, target_orgs)
    
    return org_info

def organization_search_intersection(token: str, target_orgs: list):
    """
    Inputs: List of GitHub organizations (logins) and personal access token.
    Outputs: List of users that are members of ~50% of the organization names in target_orgs.
    Method: GitHub GraphQL API with pagination. Membership testing across multiple organizations.
    Information (per User): Login, Name, Email, Bio, Location, Company, social
    """
    users = organization_membership_request(token, target_orgs) # Fetches list of users that are members of at least (1/3 + 1) of the organizations (rounded up)
    #print(f"Users: {users}")
    
    results = []
    
    batch_size = 50
    for i in range(0, len(users), batch_size):
        user_batch = users[i:i+batch_size]
        query = graphQL_build_bulk_user_query(user_batch)
        #print(query)
        
        results += user_bulk_request(token, query)
        print(results)
        
        return results