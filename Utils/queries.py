# Utils/queries.py
"""
Central location for GraphQL query strings used in the project.
"""

def graphQL_user_exact_query(login): # Returns a query for GitHub user information, including followership and social accounts
    return """
    query getAllUserInformation($login: String!, $pageSize: Int = 100, $socialSize: Int = 10, $followingCursor: String, $followersCursor: String, $cursor: String) {
        user(login: $login) {
            login createdAt name email bio location company
            socialAccounts(first: $socialSize) {
                nodes { url }
            }
            organizations(first: $pageSize, after: $cursor) {
                totalCount
                nodes { login }
            }
            following(first: $pageSize, after: $followingCursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                    login createdAt name email bio location company
                    socialAccounts(first: $socialSize) {
                        nodes { url }
                    }
                    organizations(first: $pageSize, after: $cursor) {
                        nodes { login }
                    }
                }
            }
            followers(first: $pageSize, after: $followersCursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                    login createdAt name email bio location company
                    socialAccounts(first: $socialSize) {
                        nodes { url }
                    }
                    organizations(first: $pageSize, after: $cursor) {
                        nodes { login }
                    }
                }
            }
            starredRepositories(first: 100) {
                edges {
                    node {
                    owner { login } name
                }
            }
            pageInfo { endCursor hasNextPage }
        }
    }
}
    """

def graphQL_user_starred_repos_query(login): # Returns a query for repositories starred by a GitHub user
    return """
    query getStarredRepos($login: String!, $pageSize: Int = 100, $socialSize: Int = 10, $followingCursor: String, $followersCursor: String, $cursor: String) {
        user(login: $login) {
            starredRepositories(first: 100) {
                edges {
                    node { name description stargazerCount
                    owner { login }
                }
            }
            pageInfo { endCursor hasNextPage }
        }
    }
}
    """

def graphQL_build_partial_user_query(user_logins): # Builds and returns a query that fetches information on users that contain or partially match the input string
    """
    Assembles a GraphQL query string that fetches information for all users, in one request, returned
    by the User Search (Partial) method
    """
    query = f"""query partialUserQuery {{
"""

    for i, user in enumerate(user_logins):
        user_index = str(i)
        query += f"""   user{user_index}: user(login: "{user}") {{
            login createdAt name email bio location company
            socialAccounts(first: 10) {{
                nodes {{ url }}
                }}
            }}"""
    
        query = query.replace('{{', '{').replace('}}', '}') # Escape braces for f-string
        query += "}"
    
    return query

def graphQL_build_stargazing_query(user_logins): # Builds and returns a query that fetches (for each user) the repositories they have starred (including the repository name and owner)
    """
    For use in batch requesting the starred repositories of multiple users (enriching followership information)
    Explanation: Batching used to maintain speed while avoiding GraphQL rate limits.
    Explanation: Try requesting starredRepositories { totalCount } to limit querying in a single request.
    """
    query = f"""query userStargazingQuery {{
        """
    for i, user in enumerate(user_logins):
        user_index = str(i)
        query += f"""user{user_index}: user(login: "{user}") {{
            login starredRepositories(first: 100) {{
                nodes {{ nameWithOwner }}
                pageInfo {{ endCursor hasNextPage }}
                }}
            }}"""
        
        query = query.replace('{{', '{').replace('}}', '}') # Escape braces for f-string
        query += "}"
    
    return query

def graphQL_repo_insights_query(login): # Returns a query for repositories owned by a user, including users that forked and starred each repository
    return f"""query userReposInsightsQuery($login: String!, $repoCursor: String) {{
        user(login: $login) {{
            repositories(first: 100, after: $repoCursor) {{
                pageInfo {{ hasNextPage endCursor }}
                nodes {{
                    name
                    forks(first: 100) {{
                        nodes {{
                            owner {{ login }}
                        }}
                    }}
                    stargazers(first: 100) {{
                        nodes {{ login }}
                    }}
                }}
            }}
        }}
    }}
    """

def graphQL_organization_query(batch): # Returns a query for organizations, including members and repositories
    var_decl = ", ".join([f"$repoCursor{idx}: String, $memberCursor{idx}: String" for idx in range(len(batch))])
    query = f"""query({var_decl}) {{
        """
    
    for i, org in enumerate(batch):
        query += f"""org{i}: organization(login: "{org}") {{
            login name email location websiteUrl createdAt isVerified twitterUsername
            repositories(first: 100, after: $repoCursor{i}) {{
                nodes {{ name description }}
                pageInfo {{ hasNextPage endCursor }}
            }}
            membersWithRole(first: 100, after: $memberCursor{i}) {{
                nodes {{ login name email }}
                pageInfo {{ hasNextPage endCursor }}
            }}
        }}"""
        
    query += "}" # Closes the GraphQL query string
    
    return query