# Utils/GraphQL_Queries.py
"""
Central location for GraphQL query strings used in the project.
"""

# Query for GitHub user information, including followership and social accounts
def graphQL_user_exact_query(login):
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

def graphQL_user_starred_repos_query(login):
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

def graphQL_build_partial_user_query(user_logins):
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

def graphQL_build_stargazing_query(user_logins):
    """
    For use in batch requesting the starred repositories of multiple users (enriching followership information)
    Explanation: Batching used to maintain speed while avoiding GraphQL rate limits.
    Explanation: Try requesting starredRepositories { totalCount } to limit querying in a single request.
    """
    query = f"""query userStargazingQuery {{
"""
    for i, user in enumerate(user_logins):
        user_index = str(i)
        query += f"""    user{user_index}: user(login: "{user}") {{
            login starredRepositories(first: 100) {{
                nodes {{ nameWithOwner }}
                pageInfo {{ endCursor hasNextPage }}
                }}
            }}"""
        
        query = query.replace('{{', '{').replace('}}', '}') # Escape braces for f-string
        query += "}"
    
    return query

def graphQL_repo_insights_query(login):
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