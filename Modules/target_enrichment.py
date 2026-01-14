import requests, lxml, time
from bs4 import BeautifulSoup
from tldextract import extract
from urllib.parse import urlparse

## NOTES: I did not implement an Inclusion or Exclusion Sets for URLs to prevent over-filtering.
## An Inclusion Set would inevitably filter out relevant URLs for lesser-known, foreign, and emerging platforms.
## An Inclusion Set could never reliably include all freelancer platforms.
## An Exclusion Set would require constant updating and maintenance to remain effective.

## CONSIDERED FOR FUTURE UPDATES:
## 1) Exclude results based on subsequent call to confidence scoring module (to be developed).

def enrichment_profile_scraping(username, base_url="https://github.com/", start_time=None):
    """
    Inputs: Username (login) and a GitHub base URL. #Accepts lists of users when called in a for loop from followership.py.
    Outputs: Appends email addresses and social media links identified in a user's Readme file to user["email"] and user["links"] for each input user.
    Method: Scraping the anchor tags found on a GitHub user's Readme/Profile page. Only external links are collected
    Information (per User): user["email"] (list), user["links"] (list)
    """
    '''Scrapes a GitHub user's profile page to extract their achievements.'''
    
    if type(username) is str: # For handling test inputs
        user = username
        del username
        username = [{"login": user}]
    
    #TARGET URL CONSTRUCTION
    for user in username:
        achievements = set()
        emails = set() # Declaration for later use
        
        # Seed links with any existing links or socialAccounts from upstream data
        social_accounts = set(user.get("socialAccounts", {}))
        
        login = user['login']
        target_url = f"{base_url}{login}"
        
        #ADDS PROFILE ACHIEVEMENTS TO USER DICT
        try:
            response = requests.get(target_url, timeout=10)
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
        
        if user.get('email'):
            emails.add(user['email'])
        
        user['email'] = emails
        
        if user.get('socialAccounts'):
            existing_socials = set(user["socialAccounts"])
            for url in existing_socials:
                n_url = normalize_url(url)
                existing_socials.remove(url)
                existing_socials.add(n_url)
            user['socialAccounts'] = social_accounts.union(existing_socials)
    
    return username

def normalize_url(url):
    """Normalizes URLs by ensuring they use HTTPS, end with a slash, and do not contain 'www.'."""
    if url[-1] != '/': # adds trailing slash if missing
        url = url + "/"
    if url[:7] == "http://": # converts http to https
        url = "https://" + url[7:]
    if "www." in url: # removes 'www.' if present
        url = "https://" + url[12:]
    return url

if __name__ == '__main__':
    #FOR TESTING PURPOSES
    '''<---------- TEST def enrichment_profile_scraping_achievements(): OUTPUTS ---------->'''
    # SAMPLE OUTPUT FROM FOLLOWERSHIP MODULE
    #username = PASTE SAMPLE LIST CONTAINING ONE OR MORE USER DICTS HERE (GENERATED BY USER_EXACT_SEARCH.PY)
    start_time = time.perf_counter()
    #enriched_username = enrichment_profile_scraping(username)
    #print(f"Achievements enriched data: {enriched_username}")
    end_time = time.perf_counter()
    print(f"Execution time: {end_time - start_time} seconds")