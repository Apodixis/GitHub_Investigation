def starred_repo_owners(user):
    # Extract starred repository owner logins from the last fetched user payload
    repoOwners = []
    try:
        # 'user' comes from the last loop iteration where payload was fetched
        starred = (user or {}).get("starredRepositories") or {}
        edges = starred.get("edges") or []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            owner = node.get("owner") or {}
            owner_login = owner.get("login")
            stargazer_count = node.get("stargazerCount")
            if owner_login is not None and stargazer_count is not None:
                repoOwners.append([owner_login, stargazer_count])
    except Exception:
        pass
    return repoOwners