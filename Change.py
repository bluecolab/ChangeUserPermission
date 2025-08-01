from github import Github
from dotenv import load_dotenv
import os

# init global vars
env = {}

# define functions
def load_env_vars() -> None:
    # Load environment variables
    load_dotenv()
    env['TOKEN'] = os.getenv("GH_Token")
    env['ORG_NAME'] = os.getenv("GH_Org")
    # the previous list of outside collaborators
    env['OC_LOG'] = os.getenv("Out_Collab_Log_File")

def connect():        
    # Connect to GitHub
    github_connection = Github(env['TOKEN'])
    github_org = github_connection.get_organization(env['ORG_NAME'])
    return github_connection, github_org

def get_members_repos_lists(org):
    # get member and repo lists from GitHub
    outside_collabs = list(org.get_outside_collaborators())
    repos = org.get_repos()
    return outside_collabs, repos

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
            file.write('\n'.join(map(lambda u:u.login ,new_list)))
            response = [True]
    # return the final list, or [True], or an empty list, depending on what was done
    return response

def list_out_collabs(connection, oc, prev_oc):
    request = input("Enter \"new\" to list only new outside collaborators, or any key to list all outside collaborators: ").strip()
    # List outside collaborators
    if request == "new":
        print(f"New outside collaborators in {env['ORG_NAME']}:")
        new_oc = [member for member in oc if member.login not in prev_oc]
        for member in new_oc:
            if member.login == connection.get_user().login:
                print(f" - {member.login} (You)")
            else:
                print(f" - {member.login}")
        # save new collaborators?
        save = input("\nAdd new outside collaborators to logged list (yes/no)? ")
        if save == "yes" or save == "y":
            read_write_out_collab_log(env["OC_LOG"], 'a', new_oc)
            print("The new collaborators have been appended to the logged list.")
    else:
        print(f"Outside collaborators in {env['ORG_NAME']}:")
        for member in oc:
            if member.login == connection.get_user().login:
                print(f" - {member.login} (You)")
            else:
                print(f" - {member.login}")

def get_user(connection, oc, username:str):
    # try to find th given username
    if not username:
        print("Username cannot be empty.")
        manage_permissions()

    if username not in [member.login for member in oc]:
        print(f"User {username} is not an outside collaborator in {env['ORG_NAME']}.")
        manage_permissions()

    # Get user object
    return connection.get_user(username)

def get_user_repos(user, repos):
    print(f"Finding repos for outside collaborator: {user.login}\n(this may take a minute)")
    # Get repos and check their permissions
    user_repos_read = []
    user_repos_notread = []
    for repo in repos:
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
    

def manage_permissions(connection, oc, repos):
    # Ask for username
    username = input("\nEnter the username to modify, or 'exit' to exit: ").strip()
    if username=="exit":
        exit(0)
    user = get_user(connection, oc, username)
    read, notread = get_user_repos(user, repos)

    # Show current permissions
    print(f"\nUser {user.login} has access to the following repositories:")
    for repo, permission in read + notread:
        print(f" - {repo.name}: {permission} {'(archived)' if repo.archived else ''}")

    # Confirm
    confirm = input(f"\nWould you like to downgrade {user.login}'s permissions to 'read' in all repositories? (yes/no): ").strip().lower()
    if confirm.lower() != "yes" and confirm.lower() != "y":
        print("No changes were made.")
        manage_permissions(connection, oc, repos)
    else:
        downgrade_permissions(user, notread)

def main():
    # setup
    load_env_vars()
    connection, org = connect()
    oc, repos = get_members_repos_lists(org)
    # read previous outside collabs list
    prev_oc = read_write_out_collab_log(env['OC_LOG'])
    list_out_collabs(connection, oc, prev_oc)
    while True:
        # loop forever until user exits
        manage_permissions(connection, oc, repos)


if __name__ == "__main__":
    main()