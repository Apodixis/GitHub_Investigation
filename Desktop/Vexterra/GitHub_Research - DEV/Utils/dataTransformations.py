from collections import Counter

def compare_user_relations(following: list, followers: list, target_user: dict = None) -> list:
    """
    Compares users in following and followers lists, annotating each user with their relation:
    - 'mutual' if in both
    - 'following' if only in following
    - 'follower' if only in followers
    Returns a combined list of users with 'relation' set.
    """
    if target_user:
        target_user['relation'] = 'target'
    
    following_dict = {user['login']: user for user in following if user.get('login')}
    followers_dict = {user['login']: user for user in followers if user.get('login')}
    all_logins = set(following_dict.keys()) | set(followers_dict.keys())
    relations = []
    
    for login in all_logins:
        if login in following_dict and login in followers_dict:
            user = following_dict[login].copy()
            user['relation'] = 'mutual'
            relations.append(user)
            
        elif login in following_dict:
            user = following_dict[login].copy()
            user['relation'] = 'following'
            relations.append(user)
            
        elif login in followers_dict:
            user = followers_dict[login].copy()
            user['relation'] = 'follower'
            relations.append(user)
            
    return relations

def starred_repo_owners(target_user: dict):
    """
    Extracts all starred repositories' owner logins and returns a list of [unique owner name, number of occurrences].
    """
    from collections import Counter
    owner_names = []
    try:
        target_login = (target_user or {}).get('login')
        starred = (target_user or {}).get("starredRepositories") or {}
        edges = starred.get("edges") or []
        
        for edge in edges:
            node = (edge or {}).get("node") or {}
            owner = node.get("owner") or {}
            owner_login = owner.get('login')
            
            if owner_login and owner_login != target_login:
                owner_names.append(owner_login)
    
    except Exception:
        pass
    
    owner_counts = Counter(owner_names)
    
    #sorts the nested lists by number of occurences (indicates potential relationship) in descending order
    sorted_owners = sorted(owner_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [[owner, count] for owner, count in sorted_owners]

# Compares forked_users and starred_users, returning repo_insights as specified
def compare_repo_insights(forked_users, starred_users):
    """
    For each unique login in forked_users and starred_users, returns a nested list:
    [login, {'relation': relationship}, {'count': count}]
    relationship: 'forked', 'starred', or 'forked and starred'
    count: total number of times the login appeared in both lists
    """
    forked_counter = Counter(forked_users)
    starred_counter = Counter(starred_users)
    repo_insights = []
    
    all_logins = set(forked_counter.keys()) | set(starred_counter.keys())
    
    for login in all_logins:
        in_forked = login in forked_counter
        in_starred = login in starred_counter
        
        if in_forked and in_starred:
            relation = 'forked and starred'
        
        elif in_forked:
            relation = 'forked'
        
        else:
            relation = 'starred'
        
        count = forked_counter.get(login, 0) + starred_counter.get(login, 0)
        
        repo_insights.append([login, {'relation': relation}, {'count': count}])
    
    return repo_insights