import requests
import argparse
import csv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define your GitHub token and headers
def headers(token):
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

def team_exists(org, team_slug, token):
    url = f"https://api.github.com/orgs/{org}/teams/{team_slug}"
    response = requests.get(url, headers=headers(token))
    return response.status_code == 200

def add_team_to_repo(org, token, team_slug, repo_name, permission='read'):
    """
    Add a team to a repository with the specified permission.
    """
    url = f'https://api.github.com/orgs/{org}/teams/{team_slug}/repos/{org}/{repo_name}'
    data = {
        'permission': permission
    }
    response = requests.put(url, headers=headers(token), json=data)
    
    if response.status_code == 204:
        return {"message": "Team added successfully"}
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        response.raise_for_status()

def get_repo_names_from_csv(csv_file):
    """
    Fetch the list of repository names from a CSV file.
    """
    repo_names = []
    with open(csv_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            repo_names.append(row[0])  # Assuming the repo names are in the first column
    return repo_names

def handle_rate_limiting(response):
    """
    Handle GitHub API rate limiting.
    """
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
        reset_time = int(response.headers['X-RateLimit-Reset'])
        sleep_time = max(0, reset_time - time.time())
        logging.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        return True
    return False

def list_teams_for_repo(org, token, repo_name):
    """
    List all associated teams and their roles for a repository.
    """
    url = f'https://api.github.com/repos/{org}/{repo_name}/teams'
    response = requests.get(url, headers=headers(token))
    response.raise_for_status()
    return response.json()

def list_all_repos(org, token):
    """
    List all repositories in an organization.
    """
    url = f'https://api.github.com/orgs/{org}/repos'
    repos = []
    while url:
        response = requests.get(url, headers=headers(token))
        response.raise_for_status()
        repos.extend(response.json())
        url = response.links.get('next', {}).get('url')
    return [repo['name'] for repo in repos]

def write_teams_to_csv(org, token, csv_filename):
    """
    Write all associated teams and their roles for all repositories in the organization to a CSV file.
    """
    repos = list_all_repos(org, token)
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Repository', 'Team', 'Role'])  # Write the header
        for repo_name in repos:
            try:
                teams = list_teams_for_repo(org, token, repo_name)
                if teams:
                    logging.info(f"Teams associated with repository '{repo_name}':")
                    for team in teams:
                        logging.info(f"Team: {team['name']}, Role: {team['permission']}")
                        writer.writerow([repo_name, team['name'], team['permission']])  # Write the data
                else:
                    logging.info(f"No teams associated with repository '{repo_name}'.")
            except requests.exceptions.HTTPError as e:
                logging.error(f"Failed to list teams for repository '{repo_name}': {e}")
    logging.info(f"CSV report generated: {csv_filename}")

def add_teams_to_repos(org, token, team_slug, repo_names, permission):
    """
    Add a team to multiple repositories with the specified permission.
    """
    for repo_name in repo_names:
        while True:
            try:
                add_team_to_repo(org, token, team_slug, repo_name, permission)
                logging.info(f"Team '{team_slug}' has been added to repository '{repo_name}' with '{permission}' permission.")
                break
            except requests.exceptions.HTTPError as e:
                if handle_rate_limiting(e.response):
                    continue
                logging.error(f"Failed to add team to repository '{repo_name}': {e}")
                break

def main():
    parser = argparse.ArgumentParser(description='GitHub repository team management.')
    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-command help')

    # Subparser for adding teams
    add_parser = subparsers.add_parser('add-team', help='Add a GitHub team to a repository.')
    add_parser.add_argument('--org', required=True, help='GitHub organization name')
    add_parser.add_argument('--token', required=True, help='GitHub personal access token')
    add_parser.add_argument('--team-slug', required=True, help='Slug of the GitHub team')
    add_parser.add_argument('--repo-name', help='Name of the repository')
    add_parser.add_argument('--csv-file', help='CSV file containing repository names')
    add_parser.add_argument('--permission', default='read', choices=['read', 'write', 'admin', 'maintain', 'triage'], help='Roles: admin, maintain, write, triage, read. Default role: read')

    # Subparser for listing teams
    list_parser = subparsers.add_parser('list-teams', help='List all associated teams and their roles for all repositories in the organization.')
    list_parser.add_argument('--org', required=True, help='GitHub organization name')
    list_parser.add_argument('--token', required=True, help='GitHub personal access token')

    args = parser.parse_args()

    if args.command == 'list-teams':
        csv_filename = f'{args.org}_teams_roles.csv'
        write_teams_to_csv(args.org, args.token, csv_filename)
    elif args.command == 'add-team':
        permission = args.permission.lower()
        permission = 'pull' if permission == 'read' else permission
        permission = 'push' if permission == 'write' else permission

        if args.csv_file:
            repo_names = get_repo_names_from_csv(args.csv_file)
        elif args.repo_name:
            repo_names = [args.repo_name]
        else:
            logging.error("Error: You must provide either --repo-name or --csv-file.")
            exit(1)
            
        if team_exists(args.org, args.team_slug, args.token):
            add_teams_to_repos(args.org, args.token, args.team_slug, repo_names, permission)
        else:
            print(f"Team '{args.team_slug}' does not exist in organization '{args.org}'.")

if __name__ == "__main__":
    main()
