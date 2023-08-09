import requests
import os
import csv

# Bitbucket Server (self-hosted) details
bitbucket_server="52.136.127.92:7990"
bitbucket_server_username = "SyncUser"
bitbucket_server_http_token = "MTI1NTY1NDY0NzU4OuTEZRishBCg8QkF9ANqQDEbNceA"

# Specify the Bitbucket Server project key
bitbucket_server_project_keys = ["P1", "P2", "P3"]
all_repo = []
all_proj=[]
    
for bitbucket_server_project_key in bitbucket_server_project_keys:
    print(f"\nExecution started for Project key: {bitbucket_server_project_key}")
    # Bitbucket Server API endpoint for projects
    bitbucket_server_projects_api_url = f"http://{bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"

    # Fetch repository list from Bitbucket Server project
    response = requests.get(bitbucket_server_projects_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token))
    if response.status_code == 200:
        print(f"Successfully fetched repository list from Bitbucket Server")
    else:
        print(f"Failed to fetch repository list from Bitbucket Server.\nError: {response.text}")
        exit(1)

    repo_list = response.json()["values"]

    for repo_data in repo_list:
        bitbucket_server_repo_slug = repo_data["slug"]
        all_repo.append(bitbucket_server_repo_slug)
        all_proj.append( bitbucket_server_project_key)

# Export the all_repo list to a CSV file
csv_filename = "repository_list.csv"
cdir = os.getcwd()
with open(csv_filename, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Project", "Repository"])  # Write header
    #csv_writer.writerows([[name] for name in all_repo])  # Write repo name row by row
    for proj, repo in zip(all_proj, all_repo):
        csv_writer.writerow([proj, repo])

print(f"Repository list have been exported to {cdir}\{csv_filename}")