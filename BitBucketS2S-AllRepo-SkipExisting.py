import requests
import subprocess
import platform
import time
import os
import logging

# Configure logging to write to both log file and console
logging.basicConfig(filename='script_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger('').addHandler(console_handler)

# Gartner's Bitbucket Server (self-hosted) details
gt_bitbucket_server= "<GARTNER's-BITBUCKET-SERVER-URL-WITHOUT-HTTP/HTTPS>"
gt_bitbucket_server_username = "<GARTNER's-BITBUCKET-SERVER-USER>"
gt_bitbucket_server_http_token = "<GARTNER's-HTTP-TOKEN-WITH-READ-ACCESS>"

# TN's Bitbucket Server (self-hosted) details
tn_bitbucket_server= "<TN's-BITBUCKET-SERVER-URL-WITHOUT-HTTP/HTTPS>"
tn_bitbucket_server_username = "<TN's-BITBUCKET-SERVER-USER-WHICH-HAS-ADMIN-ACCESS>"
tn_bitbucket_server_http_token = "<TN's-HTTP-TOKEN-WITH-ADMIN-ACCESS>"

# Sleep time in seconds
sleep_time = 1

# Specify the Gartner's Bitbucket Server project key
bitbucket_server_project_keys = ["P1", "P2", "P3", "P4"]

#Add repository name if you want to skip (ex: ["repo1", "repo2"])
skip_repo = []

gt_auth = (gt_bitbucket_server_username, gt_bitbucket_server_http_token)
tn_auth = (tn_bitbucket_server_username, tn_bitbucket_server_http_token)

# Function to delete .git folder
def remove_gitfolder(new_dir):
    try:
        system_platform = platform.system()
        if system_platform == "Windows":
            cmd = f'rmdir /s /q "{new_dir}"'
        else:
            cmd = f'rm -rf "{new_dir}"'
        
        subprocess.run(cmd, shell=True, check=True)
        logging.info(f"Removed '{new_dir}' directory and its contents successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while removing '{new_dir}': {e} \n")

# Function to fetch and sync pull requests from Gartner's Bitbucket Server to TN's Bitbucket Server
def pull_requests(gt_bitbucket_server_pr_api_url, gt_auth, tn_bitbucket_server_pr_api_url, tn_auth):
    pr_response = requests.get(gt_bitbucket_server_pr_api_url, auth=gt_auth)
    if pr_response.status_code == 200:
        logging.info("Fetched pull requests data from Gartner's Bitbucket Server.")
        pr_data = pr_response.json()
        for pr in pr_data["values"]:
            pr_title = pr["title"]
            pr_source_branch = pr["fromRef"]["displayId"]
            pr_destination_branch = pr["toRef"]["displayId"]
            pr_author_name = pr["author"]["user"]["displayName"]

            reviewers = []
            for reviewer in pr["reviewers"]:
                reviewers.append(reviewer["user"]["name"])

            if "description" in pr:
                pr_description = pr["description"]
                pr_payload = {
                    "title": pr_title,
                    #"description": pr_description,  # Add description if not empty
                    "description": f"Original Author: {pr_author_name}\n\nReviewers: {', '.join(reviewers)}\n\n{pr_description}",
                    "fromRef": {
                        "id": pr_source_branch  # Assuming pr_source_branch is the correct branch identifier
                    },
                    "toRef": {
                        "id": pr_destination_branch  # Assuming pr_destination_branch is the correct branch identifier
                    },
                    #"reviewers": [{"username": reviewer} for reviewer in reviewers]
                }
            else:
                pr_payload = {
                    "title": pr_title,
                    "fromRef": {
                        "id": pr_source_branch  # Assuming pr_source_branch is the correct branch identifier
                    },
                    "toRef": {
                        "id": pr_destination_branch  # Assuming pr_destination_branch is the correct branch identifier
                    },
                    "description": f"Original Author: {pr_author_name}\n\nReviewers: {', '.join(reviewers)}",
                    # "reviewers": [{"displayName": reviewer} for reviewer in reviewers]
                }
            # headers = {
            #     "Content-Type": "application/json"
            # }

            pr_create_response = requests.post(tn_bitbucket_server_pr_api_url, json=pr_payload, auth=tn_auth)
            if pr_create_response.status_code == 201:
                logging.info(f"Pull request '{pr_title}' created in TN's Bitbucket Server.")
            else:
                logging.error(f"Failed to create pull request '{pr_title}' in TN's Bitbucket Server. Error: {pr_create_response.text} \n")
    else:
        logging.error(f"Failed to fetch pull requests from Gartner's Bitbucket Server. Error: {pr_response.text} \n")

    
for bitbucket_server_project_key in bitbucket_server_project_keys:
    logging.info(f"Execution started for Project key: {bitbucket_server_project_key}")
    # Gartner's Bitbucket Server API endpoint for projects
    gt_bitbucket_server_projects_api_url = f"https://{gt_bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"

    next_page_start = 0
    while True:
        params = {"start": next_page_start}
        response_server = requests.get(gt_bitbucket_server_projects_api_url, auth=gt_auth, params=params)
        
        if response_server.status_code == 200:
            repo_list = response_server.json()["values"]
            logging.info(f"Successfully fetched repository list from Gartner's Bitbucket Server")

            for repo_data in repo_list:
                bitbucket_server_repo_slug = repo_data["slug"]
                
                if bitbucket_server_repo_slug in skip_repo:
                    logging.info(f"Execution skipped for Repository name: {bitbucket_server_repo_slug} of {bitbucket_server_project_key} project")
                else:
                    logging.info(f"Execution started for Repository name: {bitbucket_server_repo_slug} of {bitbucket_server_project_key} project")

                    # Gartner's Bitbucket Server API endpoints
                    gt_bitbucket_server_api_url = f"https://{gt_bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos/{bitbucket_server_repo_slug}"
                    gt_bitbucket_server_branch_api_url =f"{gt_bitbucket_server_api_url}/branches"
                    gt_bitbucket_server_pr_api_url = f"{gt_bitbucket_server_api_url}/pull-requests"
                    
                    # TN's Bitbucket Server API endpoints
                    tn_bitbucket_server_api_url = f"https://{tn_bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"
                    tn_bitbucket_server_api_url_repo = f"{tn_bitbucket_server_api_url}/{bitbucket_server_repo_slug}"
                    tn_bitbucket_server_pr_api_url = f"{tn_bitbucket_server_api_url_repo}/pull-requests"

                    # Gartner's Bitbucket Server Repository URL
                    gt_server_repo_clone_url = f'https://{gt_bitbucket_server_username}:{gt_bitbucket_server_http_token}@{gt_bitbucket_server}/scm/{bitbucket_server_project_key}/{bitbucket_server_repo_slug}.git'

                    # TN's Bitbucket Server Repository URL
                    tn_server_repo_clone_url = f'https://{tn_bitbucket_server_username}:{tn_bitbucket_server_http_token}@{tn_bitbucket_server}/scm/{bitbucket_server_project_key}/{bitbucket_server_repo_slug}.git'

                    # Fetch repository information from TN's Bitbucket Server
                    response = requests.get(tn_bitbucket_server_api_url_repo, auth=tn_auth)
                    if response.status_code == 200:
                        logging.info(f"{bitbucket_server_repo_slug} repository exists in TN's Bitbucket Server proceeding to next repository.\n")
                        #exit(1)
                        continue
                    
                    # Fetch repository information from Gartner's Bitbucket Server
                    response = requests.get(gt_bitbucket_server_api_url, auth=gt_auth)
                    if response.status_code != 200:
                        logging.error(f"Failed to fetch {bitbucket_server_repo_slug} repository information from Gartner's Bitbucket Server. Error: {response.text} \n")
                        #exit(1)
                        break
                    else:
                        logging.info(f"Fetched {bitbucket_server_repo_slug} repository information from Gartner's Bitbucket Server.")

                    repo_data = response.json()

                    # Fetch repository information from Gartner's Bitbucket Server
                    responseb = requests.get(gt_bitbucket_server_branch_api_url, auth=gt_auth)
                    if responseb.status_code != 200:
                        logging.error(f"Failed to fetch branch information of {bitbucket_server_repo_slug} repository from Gartner's Bitbucket Server. Error: {responseb.text} \n")
                        #exit(1)
                        break
                    else:
                        logging.info(f"Fetched branch information of {bitbucket_server_repo_slug} repository from Gartner's Bitbucket Server.")

                    branch_data = responseb.json()

                    for branch in branch_data["values"]:
                        if branch.get("isDefault"):
                            default_branch_name = branch["displayId"]
                            logging.info(f"'{default_branch_name}' is main branch for {bitbucket_server_repo_slug} repository on Gartner's Bitbucket Server.")
                            break

                    if repo_data.get("description"):

                        # Prepare payload
                        payload = {
                            "scm": repo_data["scmId"],
                            "is_private": repo_data["public"],
                            "fork_policy": repo_data['forkable'],
                            "name": repo_data["name"],
                            "project": {
                                "key": repo_data["project"]["key"]
                            },
                            "defaultBranch": default_branch_name,
                            "description": repo_data["description"],
                        }
                    else:
                        # Prepare payload
                        payload = {
                            "scm": repo_data["scmId"],
                            "is_private": repo_data["public"],
                            "fork_policy": repo_data['forkable'],
                            "name": repo_data["name"],
                            "project": {
                                "key": repo_data["project"]["key"]
                            },
                            "defaultBranch": default_branch_name,
                            #"description": repo_data["description"],
                        }

                    # Create or update repository in TN's Bitbucket Server
                    create_response = requests.post(tn_bitbucket_server_api_url, json=payload, auth=tn_auth)
                    get_response = requests.get(tn_bitbucket_server_api_url_repo, json=payload, auth=tn_auth)
                    
                    if create_response.status_code != 201 and get_response.status_code != 200:
                        logging.error(f"Failed to create {bitbucket_server_repo_slug} repository in TN's Bitbucket Server. Error: {create_response.text} {get_response.text} \n")
                        #exit(1)
                        break
                    else:
                        response_tn = requests.put(tn_bitbucket_server_api_url_repo, json=payload, auth=tn_auth)

                        if response_tn.status_code != 200:
                            logging.error(f"Failed to create {bitbucket_server_repo_slug} repository in TN's Bitbucket Server. Error: {response_tn.text} \n")
    
                        logging.info(f"Configuring {bitbucket_server_repo_slug} repository on TN's Bitbucket Server.")
                        # Fetch the Gartner's Bitbucket Server repository
                        logging.info(f"Cloning {bitbucket_server_repo_slug} repository from Gartner's Bitbucket Server.")
                        fetch_cmd = f"git clone --bare {gt_server_repo_clone_url}"
                        fetch_process = subprocess.Popen(fetch_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        fetch_process.wait()
                        if fetch_process.returncode != 0:
                            logging.error(f"Failed to clone {bitbucket_server_repo_slug} repository from Gartner's Bitbucket Server.")
                            logging.error(fetch_process.stderr.read().decode())
                            #exit(1)
                            break
                        else:
                            logging.info(f"Successfully cloned {bitbucket_server_repo_slug} repository from Gartner's Bitbucket Server.")
                        
                        # Change directory to .git folder
                        new_dir = f"./{bitbucket_server_repo_slug}.git"
                        os.chdir(new_dir)

                        # Push the fetched repository to the TN's Bitbucket Server repository
                        logging.info(f"Pushing {bitbucket_server_repo_slug} repository to TN's Bitbucket Server")
                        push_cmd = f"git push --mirror {tn_server_repo_clone_url}"
                        push_process = subprocess.Popen(push_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        push_process.wait()
                        if push_process.returncode == 0:
                            logging.info("Gartner's Bitbucket Server repository synced with TN's Bitbucket Server repository.")
                            
                            # Change directory back to original path
                            os.chdir("..")
                            # Using function to delete .git folder
                            remove_gitfolder(new_dir)
                        else:
                            logging.error("Failed to push/sync Gartner's Bitbucket Server repository with TN's Bitbucket Server repository.")
                            logging.error(push_process.stderr.read().decode())
                            
                            # Change directory back to original path
                            os.chdir("..")
                            # Using function to delete .git folder
                            remove_gitfolder(new_dir)
                            #exit(1)
                            break
                            
                        # Fetch and sync pull requests from Gartner's Bitbucket Server to TN's Bitbucket Server
                        #pull_requests(gt_bitbucket_server_pr_api_url, gt_auth, tn_bitbucket_server_pr_api_url, tn_auth)

                logging.info(f"Will wait for {sleep_time} seconds before proceeding to next step")
                time.sleep(sleep_time)
                logging.info("Proceeding to next step")

            if "isLastPage" in response_server.json() and response_server.json()["isLastPage"]:
                break  # Break the loop if it's the last page
            
            next_page_start = response_server.json()["nextPageStart"]
        else:
            logging.error(f"Failed to fetch repository list from Gartner's Bitbucket Server. Error: {response_server.text} \n")
            # exit(1)
            break
logging.info ("Execution Complete.\n")