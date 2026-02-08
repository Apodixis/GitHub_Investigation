# Utils/dataTransformations.py
from collections import Counter

def compare_user_relations(following: list, followers: list, target_user: dict = None) -> list:
    """
    Inputs: Two lists of user dicts: (1) following and (2) followers and an optional target_user dict.
    Outputs: List of user dicts annotated with their relationship to the target user.
    Method: Membership testing and dictionary merging.
    Information (per User): Relation to target user ('mutual', 'following', 'follower', or 'target').
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

def starred_repo_owners(target_user: dict) -> list:
    """
    Inputs: Target_user dict.
    Outputs: Nested list of [unique repo owner names, count].
    Method: Membership testing and counting.
    Information (per repo owner): Owner login, number of occurrences.
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
def compare_repo_insights(forked_users: list, starred_users: list) -> list:
    """
    Inputs: Two lists: (1) users that forked repositories and (2) users that starred repositories owned by the target user.
    Outputs: Nested list of [user login, {'relation': relation}, {'count': count}].
    Method: Membership testing and counting.
    Information (per user): Owner login, relationship to target_user, number of occurrences.
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