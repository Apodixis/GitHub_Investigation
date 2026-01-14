# Utils/GraphQL_Queries.py
"""
Central location for GraphQL query strings used in the project.
"""

# Query for GitHub user information, including followership and social accounts
def get_user_information_query():
    return """
    query getUserInformation($login: String="healer-125", $pageSize: Int = 100, $socialSize: Int = 10, $followingCursor: String, $followersCursor: String, $cursor: String) {
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
                        totalCount
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
                        totalCount
                        nodes { login }
                    }
                }
            }
            starredRepositories(first: 100, orderBy: {field: STARRED_AT, direction: DESC}) {
                edges {
                    node { name description url stargazerCount
                    owner {
                        login
                    }
                }
            }
            pageInfo { endCursor hasNextPage }
        }
    }
}
    """
