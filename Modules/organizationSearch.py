# Modules/organizationSearch.py
from Utils.queries import graphQL_organization_query
from Utils.sendRequests import organization_request

def organization_search_info(token: str, target_orgs: list) -> dict: # Add organization selection before return prompting for enrichment
    """
    Inputs: GitHub organization (login) and personal access token.
    Outputs: Target org info, dictionary of members, list of followers.
    Method: GitHub GraphQL API with pagination.
    Information (per User): Login, Name, Email, Bio, Location, Company, socialAccounts URLs.
    """
    #query = graphQL_organization_query(target_orgs) # Fetch the GraphQL query string
    #print(query)
    results = organization_request(token, target_orgs)
    return results

def organization_search_intersection(token, target_orgs):
    """PLACEHOLDER"""
    return "PLACEHOLDER"