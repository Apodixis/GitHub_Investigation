import os

def clearTerminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def search_mode_menu():
    # Menu for selecting user search mode when running main.py
    clearTerminal()
    print("1) User Search - Exact Match") # Finds information for a specific user: (User, Followership, and Stargazing)
    print("2) User Search - Partial Match") #Finds users based on partial matches (will likely return multiple results)
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1" or choice == "2":
            return choice
        else:
            print("Invalid selection. Please enter 1 or 2.")

def enrichment_menu():
    # Menu for electing to enrich results or not. Used after initial results are collected.
    clearTerminal()
    print("1) Enrich Results (Can take several minutes)")
    print("2) Skip Enrichment (Return results now)")
    
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1" or choice == "2":
            return choice
        else:
            print("Invalid selection. Please enter 1 or 2.")