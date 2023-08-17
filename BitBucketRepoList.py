import requests
import os
import csv
import logging

# Configure logging to write to both log file and console
logging.basicConfig(filename='script_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger('').addHandler(console_handler)

# Bitbucket Server (self-hosted) details
bitbucket_server="<BITBUCKET-SERVER-URL-WITHOUT-HTTP>"
bitbucket_server_username = "<BITBUCKET-SERVER-USERNAME>"
bitbucket_server_http_token = "<HTTP-TOKEN>"

# Specify the Bitbucket Server project key
bitbucket_server_project_keys = ["P1", "P2", "P3"]
all_repo = []
all_proj = []
all_proj_name =[]

for bitbucket_server_project_key in bitbucket_server_project_keys:
    logging.info(f"Execution started for Project key: {bitbucket_server_project_key}")
    bitbucket_server_projects_api_url = f"http://{bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"

    next_page_start = 0
    while True:
        params = {"start": next_page_start}
        response = requests.get(bitbucket_server_projects_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token), params=params)
        
        if response.status_code == 200:
            repo_list = response.json()["values"]
            for repo_data in repo_list:
                project_name = repo_data["project"]["name"]
                bitbucket_server_repo_slug = repo_data["slug"]
                
                all_repo.append(bitbucket_server_repo_slug)
                all_proj.append(bitbucket_server_project_key)
                all_proj_name.append(project_name)

            if "isLastPage" in response.json() and response.json()["isLastPage"]:
                break  # Break the loop if it's the last page
            
            next_page_start = response.json()["nextPageStart"]
        else:
            logging.info(f"Failed to fetch repository list from Bitbucket Server.\nError: {response.text}")
            break
            #exit(1)

# Export the all_repo list to a CSV file
csv_filename = "repository_list.csv"
cdir = os.getcwd()
with open(csv_filename, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Project Name","Project Key", "Repository"])  # Write header
    for proj_n, proj_k, repo in zip(all_proj_name, all_proj, all_repo):
        csv_writer.writerow([proj_n, proj_k, repo])

logging.info(f"Repository list has been exported to {cdir}/{csv_filename}")