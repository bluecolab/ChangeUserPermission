from github import Github
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
TOKEN = os.getenv("GH_Token")
ORG_NAME = os.getenv("GH_Org")

# Connect to GitHub
g = Github(TOKEN)
org = g.get_organization(ORG_NAME)

# List outside collaborators
outside_collabs = list(org.get_outside_collaborators())

print(f"Outside collaborators in {ORG_NAME}:")
for member in outside_collabs:
    if member.login == g.get_user().login:
        print(f" - {member.login} (You)")
    else:
        print(f" - {member.login}")

# Ask for username
username = input("\nEnter the username to modify: ").strip()

if not username:
    print("Username cannot be empty. Exiting.")
    exit(1)

if username not in [member.login for member in outside_collabs]:
    print(f"User {username} is not an outside collaborator in {ORG_NAME}. Exiting.")
    exit(1)

# Get user object
user = g.get_user(username)
print(f"Finding repos for outside collaborator: {user.login}")

# Get repos and check their permissions
repos = org.get_repos()
user_repos = []
for repo in repos:
    try:
        permission = repo.get_collaborator_permission(user)
        if permission != "none":
            user_repos.append((repo, permission))
    except Exception as e:
        print(f"Error checking {repo.name}: {e}")

# Show current permissions
print(f"\nUser {user.login} has access to the following repositories:")
for repo, permission in user_repos:
    print(f" - {repo.name}: {permission}")

# Confirm
confirm = input(f"\nWould you like to downgrade {user.login}'s permissions to 'pull' in all repositories? (yes/no): ").strip().lower()
if confirm.lower() != "yes" and confirm.lower() != "y":
    print("Exiting without changes.")
    exit(0)

# Perform downgrade
for repo, permission in user_repos:
    if permission != "pull":
        try:
            repo.remove_from_collaborators(user)
            repo.add_to_collaborators(user, permission="pull")
            print(f"✅ Downgraded {user.login}'s permission in {repo.name} to 'pull'")
        except Exception as e:
            print(f"❌ Failed to downgrade {repo.name}: {e}")