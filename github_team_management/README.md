# GitHub Team Management Script

This directory contains a script for managing GitHub repository teams. The script allows you to add a team to multiple repositories and list all associated teams and their roles for all repositories in an organization.

## Prerequisites

- Python 3.x
- `requests` library

You can install the required dependencies using the following command:

```sh
pip install -r requirements.txt
```

## Usage

### The script provides two main functionalities:

  1. Adding a team to repositories.
  2. Listing all associated teams and their roles for all repositories in an organization.
  
### Adding a Team to Repositories
  To add a team to a single repository:
```sh    
python add_teams_to_repositories.py add-team --org your_org --token your_token --team-slug your_team_slug --repo-name your_repo_name --permission push
```

To add a team to multiple repositories from a CSV file:
```sh
python add_teams_to_repositories.py add-team --org your_org --token your_token --team-slug your_team_slug --csv-file repos.csv --permission push
```

### Arguments
- `--org`: GitHub organization name (required)
- `--token`: GitHub personal access token (required)
- `--team-slug`: Slug of the GitHub team (required)
- `--repo-name`: Name of the repository (optional if --csv-file is provided)
- `--csv-file`: CSV file containing repository names (optional if --repo-name is provided)
- `--permission`: Permission level for the team (default: push). Choices are pull, push, admin, maintain, triage.

## Listing Teams and Their Roles
To list all associated teams and their roles for all repositories in the organization and export the data to a CSV file:
```sh
python add_teams_to_repositories.py list-teams --org your_org --token your_token
```

### Arguments
- `--org`: GitHub organization name (required)
- `--token`: GitHub personal access token (required)

The script will generate a CSV report named `<org>`_teams_roles.csv containing the following columns:

- Repository: Name of the repository
- Team: Name of the team
Role: Role of the team in the repository