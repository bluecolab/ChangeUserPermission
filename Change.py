"""
📜 Script: Change.py

🎯 Purpose:
    - This script allows an admin to audit and modify a user's repository permissions within a GitHub organization.
    - Specifically, it lists all repos where the user has access and downgrades their permissions to read-only ("pull").

🔧 Input:
    - GitHub username (entered interactively)
    - GitHub access token stored in a `.env` file (GH_TOKEN)
    - Organization  stored in a `.env` file  (ORG_NAME)

📤 Output:
    - Console log showing:
        • Repos the user has access to
        • Their current permission level
        • Confirmation of permission downgrade to "pull"
        • Final verification of updated access

📝 Notes:
    - Requires `PyGithub` and `python-dotenv`
    - Token must have: `admin:org`, `repo`, `read:org` scopes
    - Must be run by a user with admin rights in the organization
"""

from github import Github
from dotenv import load_dotenv
import os

# Make sure to have the right tokesn and repository name
load_dotenv()
TOKEN = os.getenv("GH_Token")
ORG_NAME = os.getenv("GH_Org")

# Connect to GitHub
g = Github(TOKEN)
org = g.get_organization(ORG_NAME)

# Print List of users in the organization
print(f"Users in the organization {ORG_NAME}:") 
for member in org.get_members():
    if member.login == g.get_user().login:
        print(f" - {member.login} (You)")
    else:
        print(f" - {member.login}")



# Get the username to modify
username= input("Enter the username to modify:".strip())

if not username:
    print("Username cannot be empty. Exiting.")
    exit(1)
if username not in [member.login for member in org.get_members()]:
    print(f"User {username} not found in the organization {ORG_NAME}. Exiting.")
    exit(1)

# Get the user object
user = g.get_user(username)
print(f" Finding repos for user: {user.login}")

# List all repositories where the user has access
repos = org.get_repos()
user_repos = []
for repo in repos:
    try:
        permission = repo.get_collaborator_permission(user)
        if permission != "none":
            user_repos.append((repo.name, permission))
    except Exception as e:
        print(f"Error accessing repo {repo.name}: {e}")

# Display the user's current repository
print(f"\nUser {user.login} has access to the following repositories:")
for repo_name, permission in user_repos:
    print(f" - {repo_name}: {permission}")


# Downgrade permissions to "pull" for each repository
for repo_name, permission in user_repos:
    if permission != "pull":
        try:
            repo = org.get_repo(repo_name) # Get the repository object
            repo.remove_from_collaborators(user) # Remove the user from collaborators
            repo.add_to_collaborators(user, "pull") # Add the user with "pull" permission
            print(f"Downgraded {user.login}'s permission in {repo_name} to 'pull'.")
        except Exception as e:
            print(f"Error downgrading permission for {repo_name}: {e}")