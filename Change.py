from github import Github
from dotenv import load_dotenv
import os

# init global vars
env = {}
globals = {
    'github_connection': None,
    'github_org': None,
    'outside_collabs': [],
    'repos': []
}

# define functions
def load_env_vars() -> None:
    # Load environment variables
    load_dotenv()
    env['TOKEN'] = os.getenv("GH_Token")
    env['ORG_NAME'] = os.getenv("GH_Org")

def connect():        
    # Connect to GitHub
    globals['github_connection'] = Github(env['TOKEN'])
    globals['github_org'] = globals['github_connection'].get_organization(env['ORG_NAME'])

def get_members_repos_lists():
    # get member and repo lists from GitHub
    globals['outside_collabs'] = list(globals['github_org'].get_outside_collaborators())
    globals['repos'] = globals['github_org'].get_repos()

def read_write_out_collab_log(file_path:str, mode:str='r', new_list:list=[]) -> list:
    # read or write to the outside collaborator log
    # r for read, w for write, a for append
    response = []
    with open(file_path, mode) as file:
        if mode == 'r':
            # return the file contents
            response = file.read()
        elif mode == 'w' or mode == 'a':
            # overwrite or append the new list, return true
            file.write('\n'.join(new_list))
            response = [True]
    # return the final list, or [True], or an empty list, depending on what was done
    return response

def list_out_collabs():
    # List outside collaborators
    print(f"Outside collaborators in {env['ORG_NAME']}:")
    for member in globals['outside_collabs']:
        if member.login == globals['github_connection'].get_user().login:
            print(f" - {member.login} (You)")
        else:
            print(f" - {member.login}")

def get_user():
    # Ask for username
    username = input("\nEnter the username to modify: ").strip()

    if not username:
        print("Username cannot be empty.")
        manage_permissions()

    if username not in [member.login for member in globals['outside_collabs']]:
        print(f"User {username} is not an outside collaborator in {env['ORG_NAME']}.")
        manage_permissions()

    # Get user object
    return globals['github_connection'].get_user(username)

def get_user_repos(user):
    print(f"Finding repos for outside collaborator: {user.login}\n(this may take a minute)")
    # Get repos and check their permissions
    user_repos_read = []
    user_repos_notread = []
    for repo in globals['repos']:
        try:
            permission = repo.get_collaborator_permission(user)
            if permission == "read":
                user_repos_read.append((repo, permission))
            elif permission != "none":
                user_repos_notread.append((repo, permission))
        except Exception as e:
            print(f"Error checking {repo.name}: {e}")
    return (user_repos_read, user_repos_notread)

def downgrade_permissions(user, user_repos_notread:list):
    # Perform downgrade
    print("Working on it. This may take a minute.")
    for repo, permission in user_repos_notread:
        if permission != "read" and not repo.archived:
            try:
                repo.remove_from_collaborators(user)
                repo.add_to_collaborators(user, permission="read")
                print(f"✅ Downgraded {user.login}'s permission in {repo.name} to 'read'")
            except Exception as e:
                print(f"❌ Failed to downgrade {repo.name}: {e}")
    print("Finished.")
    

def manage_permissions():
    user = get_user()
    read, notread = get_user_repos(user)

    # Show current permissions
    print(f"\nUser {user.login} has access to the following repositories:")
    for repo, permission in read + notread:
        print(f" - {repo.name}: {permission} {'(archived)' if repo.archived else ''}")

    # Confirm
    confirm = input(f"\nWould you like to downgrade {user.login}'s permissions to 'read' in all repositories? (yes/no): ").strip().lower()
    if confirm.lower() != "yes" and confirm.lower() != "y":
        # print("Exiting without changes.")
        # exit(0)
        manage_permissions()
    else:
        downgrade_permissions(user, notread)


def main():
    load_env_vars()
    connect()
    get_members_repos_lists()
    list_out_collabs()
    while True:
        # loop forever until user exits
        manage_permissions()


if __name__ == "__main__":
    main()