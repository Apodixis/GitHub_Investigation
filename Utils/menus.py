# Utils/menus.py
import os

def clearTerminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def user_search_mode_menu(): # Menu for selecting user search mode when running main.py
    """Presents a menu for selecting user search mode and returns the selected option."""
    clearTerminal()
    print("1) User Search - Exact Match") # Finds information for a specific user: (User, Followership, and Stargazing)
    print("2) User Search - Partial Match") #Finds users based on partial matches (will likely return multiple results)
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1" or choice == "2":
            return choice
        else:
            print("Invalid selection. Please enter 1 or 2.")

def organization_search_mode_menu(): # Menu for selecting user search mode when running main.py
    """Presents a menu for selecting organization search mode and returns the selected option."""
    clearTerminal()
    print("1) Organization Search") # Finds information on an organization and its members: (Members + Info, Repos, Contributors)
    print("2) Intersection Search") # Finds users that are members of multiple organizations from the input list of organization names (Member Info)
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1" or choice == "2":
            return choice
        else:
            print("Invalid selection. Please enter 1 or 2.")

def enrichment_menu(): # Menu for electing to enrich results or not. Used after initial results are collected.
    """Prompts a user to decide if they want to enrich search results (often adds several minutes due to scraping) and returns the selected option."""
    clearTerminal()
    print("1) Enrich Results (Can take several minutes)")
    print("2) Skip Enrichment (Return results now)")
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1" or choice == "2":
            return choice
        else:
            print("Invalid selection. Please enter 1 or 2.")