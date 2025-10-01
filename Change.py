from github import Github
from dotenv import load_dotenv
import os
import logging

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
    env['LOG'] = os.getenv("Permission_Change_Log_File")

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
            file.write('\n' + '\n'.join(map(lambda u:u.login ,new_list)))
            logging.info("New collaborators added to log list")
            response = [True]
    # return the final list, or [True], or an empty list, depending on what was done
    return response

def list_out_all_collabs(connection, oc):
    print(f"Outside collaborators in {env['ORG_NAME']}:")
    for member in oc:
        # if member.login == connection.get_user().login:
        #     print(f" - {member.login} (You)")
        # else:
        print(f" - {member.login}")

def list_out_new_collabs(connection, oc, prev_oc) -> list:
    new_oc = [member for member in oc if member.login not in prev_oc]
    if len(new_oc) == 0:
        print("No new outside collaborators found.")
        return []
    print(f"New outside collaborators in {env['ORG_NAME']}:")
    for member in new_oc:
        if member.login == connection.get_user().login:
            print(f" - {member.login} (You)")
        else:
            print(f" - {member.login}")
    # save new collaborators?
    save = input("\nAdd new outside collaborators to logged list (yes/no)? ").strip().lower()
    if save == "yes" or save == "y":
        read_write_out_collab_log(env["OC_LOG"], 'a', new_oc)
        print("The new collaborators have been appended to the logged list.")
    return new_oc

def get_user(connection, oc, username:str):
    # try to find th given username
    if not username:
        print("Username cannot be empty.")
        return

    if username not in [member.login for member in oc]:
        print(f"User {username} is not an outside collaborator in {env['ORG_NAME']}.")
        return

    # Get user object
    return connection.get_user(username)

def get_user_repos(user, repos, include_read:bool=True, include_archived:bool=True):
    print(f"Finding repos for outside collaborator: {user.login}\n(this may take a minute)")
    # Get repos and check their permissions
    user_repos_read = []
    user_repos_notread = []
    for repo in repos:
        try:
            permission = repo.get_collaborator_permission(user)
            if permission == "read" and include_read:
                if include_archived or (not include_archived and not repo.archived):
                    user_repos_read.append((repo, permission))
            elif permission != "read" and permission != "none":
                if include_archived or (not include_archived and not repo.archived):
                    user_repos_notread.append((repo, permission))
        except Exception as e:
            print(f"Error checking {repo.name}: {e}")
    if include_read:
        return (user_repos_read, user_repos_notread)
    else:
        return user_repos_notread

def print_user_permissions(user, user_repos, show_archived:bool=True):
    # Show current permissions
    if len(user_repos) == 0:
        return
    print(f"\nUser {user.login} has access to the following repositories:")
    for repo, permission in user_repos:
        if show_archived:
            print(f" - {repo.name}: {permission} {'(archived)' if repo.archived else ''}")
        elif not repo.archived:
            print(f" - {repo.name}: {permission}")
    print()

def downgrade_all(full_list):
    for user, repo in full_list:
        downgrade_permissions(user, repo)

def downgrade_permissions(user, user_repos_notread:list):
    # Perform downgrade
    for repo, permission in user_repos_notread:
        if permission != "read" and not repo.archived:
            try:
                repo.remove_from_collaborators(user)
                repo.add_to_collaborators(user, permission="read")
                logging.info(f"✅ Downgraded {user.login}'s permission in {repo.name} to 'read'")
            except Exception as e:
                logging.error(f"❌ Failed to downgrade {repo.name}: {e}")
  
def check_list_permissions(repos, users_list):
    # print(f"Checking permissions for {user.login}")
    print("Checking permissions on those users. This may take awhile.\n")
    full_list = []
    for user in users_list:
        # get only repos with non-read permissions
        nonread = get_user_repos(user, repos, include_read=False, include_archived=False)
        print_user_permissions(user, nonread, show_archived=False)
        if len(nonread) > 0:
            full_list.append((user, nonread))
    return full_list

def manage_permissions(connection, oc, repos, prev_oc):
    # Ask for username
    username = input("\nEnter the username to modify, or 'exit' to exit: ").strip()
    if username=="exit":
        exit(0)
    user = get_user(connection, oc, username)
    read, notread = get_user_repos(user, repos)

    print_user_permissions(user, read + notread)

    # Confirm
    confirm = input(f"\nWould you like to downgrade {user.login}'s permissions to 'read' in all repositories? (yes/no): ").strip().lower()
    if confirm.lower() != "yes" and confirm.lower() != "y":
        print("No changes were made.")
        return
    else:
        print("Working on it. This may take a minute.")
        downgrade_permissions(user, notread)
        print("All done. Check the log file for details.")
    
    # if users is not on the logged list of outside collaborators, ask if they should be added
    if user.login not in prev_oc:
        log_user = input(f"Add this user to the logged list (yes/no)? ").strip().lower()
        if log_user.lower() == "yes" or log_user.lower() == 'y':
            read_write_out_collab_log(env["OC_LOG"], 'a', [user])

def main():
    # setup
    load_env_vars()
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        filename=env["LOG"],
        encoding="utf-8",
        filemode="a"
    )
    connection, org = connect()
    oc, repos = get_members_repos_lists(org)
    # read previous outside collabs list
    prev_oc = read_write_out_collab_log(env['OC_LOG'])
    request = input("Enter \"new\" to list only new outside collaborators, or blank to list all outside collaborators: ").strip().lower()
    # List outside collaborators
    if request == "new":
        new_oc = list_out_new_collabs(connection, oc, prev_oc)
        if len(new_oc) == 0:
            return
        # check for non-read permissions
        check = input("Check all new outside collaborators for non-read permissions on unarchived repos (yes/no)? ").strip().lower()
        if check == "yes" or check == "y":
            full_list = check_list_permissions(repos, new_oc)
            if len(full_list) == 0:
                print("No users found with non-read permissions.")
                return
            downgrade = input("Downgrade all non-read permissions found (yes/no)? ").strip().lower()
            if downgrade == "yes" or downgrade == "y":
                downgrade_all(full_list)

    else:
        list_out_all_collabs(connection, oc)
        # user will handle updates manually
    while True:
        # loop forever until user exits
        manage_permissions(connection, oc, repos, prev_oc)


if __name__ == "__main__":
    main()