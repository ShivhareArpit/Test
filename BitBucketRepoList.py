import requests
import os
import csv

# Bitbucket Server (self-hosted) details
bitbucket_server="<BITBUCKET-SERVER-URL-WITHOUT-HTTP>"
bitbucket_server_username = "<BITBUCKET-SERVER-USERNAME>"
bitbucket_server_http_token = "<HTTP-TOKEN>"

# Specify the Bitbucket Server project key
bitbucket_server_project_keys = ["P1", "P2", "P3"]
all_repo = []
all_proj = []

for bitbucket_server_project_key in bitbucket_server_project_keys:
    print(f"\nExecution started for Project key: {bitbucket_server_project_key}")
    bitbucket_server_projects_api_url = f"https://{bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"

    next_page_start = 0
    while True:
        params = {"start": next_page_start}
        response = requests.get(bitbucket_server_projects_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token), params=params)
        
        if response.status_code == 200:
            repo_list = response.json()["values"]
            
            for repo_data in repo_list:
                bitbucket_server_repo_slug = repo_data["slug"]
                all_repo.append(bitbucket_server_repo_slug)
                all_proj.append(bitbucket_server_project_key)

            if "isLastPage" in response.json() and response.json()["isLastPage"]:
                break  # Break the loop if it's the last page
            
            next_page_start = response.json()["nextPageStart"]
        else:
            print(f"Failed to fetch repository list from Bitbucket Server.\nError: {response.text}")
            exit(1)

# Export the all_repo list to a CSV file
csv_filename = "repository_list.csv"
cdir = os.getcwd()
with open(csv_filename, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Project", "Repository"])  # Write header
    for proj, repo in zip(all_proj, all_repo):
        csv_writer.writerow([proj, repo])

print(f"Repository list has been exported to {cdir}/{csv_filename}")
