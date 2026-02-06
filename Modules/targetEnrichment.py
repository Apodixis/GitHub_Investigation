# Modules/target_enrichment.py
import os, requests, lxml, time
from bs4 import BeautifulSoup
from tldextract import extract
from urllib.parse import urlparse

## NOTES: I did not implement an Inclusion or Exclusion Sets for URLs to prevent over-filtering.
## An Inclusion Set would inevitably filter out relevant URLs for lesser-known, foreign, and emerging platforms.
## An Inclusion Set could never reliably include all freelancer platforms.
## An Exclusion Set would require constant updating and maintenance to remain effective.

## CONSIDERED FOR FUTURE UPDATES:
## 1) Exclude results based on subsequent call to confidence scoring module (to be developed).

def _normalize_url(url):
    """Normalizes URLs by ensuring they use HTTPS, end with a slash, and do not contain 'www.'."""
    normal_url = url.replace('\xa0', '').rstrip(".,;:<>\"'[]{}-=+!?@#$%^&*()|\\/`~ \n\r") # Clean URL of whitespace and trailing punctuation
    if normal_url[:7] == "http://": # converts http to https
        normal_url = normal_url.replace("http://", "https://", 1)
    if "www." in normal_url: # removes 'www.' if present
        normal_url = normal_url.replace("www.", "")
    return normal_url

def enrich_user_data(users, base_url="https://github.com/", start_time=None):
    """
    Inputs: users (login) and a GitHub base URL. #Accepts lists of users when called in a for loop from followership.py.
    Outputs: Appends email addresses and social media links identified in a user's Readme file to user["email"] and user["links"] for each input user.
    Method: Scraping the anchor tags found on a GitHub user's Readme/Profile page. Only external links are collected
    Information (per User): user["email"] (list), user["links"] (list)
    """
    '''Scrapes a GitHub user's profile page to extract their achievements.'''
    
    print(type(users),": ", users)
    
    if type(users) is str: # For handling test inputs
        user = users
        del users
        users = [{"login": user}]
    
    #TARGET URL CONSTRUCTION
    for i, user in enumerate(users):
        achievements = set()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"ENRICHING USER: {user['login']} ({i+1} of {len(users)})")
        
        emails = set(user.get("emails", {}))  # Start with any emails from upstream
        
        # Seed links with any existing links or socialAccounts from upstream data
        social_accounts = set(user.get("socialAccounts", {}))
        
        login = user['login']
        target_url = f"{base_url}{login}"
        
        #ADDS PROFILE ACHIEVEMENTS TO USER DICT
        try:
            response = requests.get(target_url, timeout=120)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            #PROFILE ACHIEVEMENTS
            profile_achievements = set(el['alt'][13:] for el in soup.select('.border-top.color-border-muted.pt-3.mt-3.d-none.d-md-block [alt]'))
            user["achievements"] = profile_achievements
        
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        #ADDS HYPERLINKS TO SOCIAL MEDIA AND EMAIL ADDRESSES TO USER DICT
        try:
            for a_tag in soup.select('a[href]'):
                href = a_tag['href']
                
                # Skip empty hrefs
                if not href:
                    continue
                
                # Skip non-navigational hrefs quickly
                if href[0] == ('#') or href[:4] == 'java':
                    continue
                
                # Handle mailto early and cheaply
                if href[:7] == 'mailto:':
                    emails.add(href[7:])
                    continue
                
                parsed_url = urlparse(href).netloc
                
                #Identifies Relative links
                if not parsed_url:
                    # Relative link → internal; check for achievements directly
                    if 'achievement=' in href:
                        val = href.split('achievement=')[1]
                        if '&' in val:
                            val = val.split('&')[0]
                        achievements.add(val)
                    continue
                
                # Compare base domain only when needed
                base = extract(parsed_url).domain
                if "github" in base:
                    continue
                
                else:
                    social_accounts.add(href)
        
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        user['emails'] = emails
        
        if user.get('socialAccounts'):
            existing_socials = set(user["socialAccounts"])
            normalized_socials = {_normalize_url(url) for url in existing_socials}
            user['socialAccounts'] = normalized_socials
    
    return users

if __name__ == '__main__':
    #FOR TESTING PURPOSES
    '''<---------- TEST def enrichment_user_data(): OUTPUTS ---------->'''
    # SAMPLE OUTPUT FROM FOLLOWERSHIP MODULE
    username = "REPLACE WITH OUTPUT FORMAT OF USER_EXACT_SEARCH.PY"
    
    start_time = time.perf_counter()
    enriched_username = enrich_user_data(username)
    print(f"Achievements enriched data: {enriched_username}")
    
    end_time = time.perf_counter()
    print(f"Execution time: {end_time - start_time} seconds")