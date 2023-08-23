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
gt_bitbucket_server= "3.145.159.218:7990"
gt_bitbucket_server_username = "Arpit"
gt_bitbucket_server_http_token = "NDc1MjU3NDU1OTAxOs9QKi+kM0WZ9eCsYf8GUTIwdgHg"

# TN's Bitbucket Server (self-hosted) details
tn_bitbucket_server= "3.15.196.235:7990"
tn_bitbucket_server_username = "Arpit"
tn_bitbucket_server_http_token = "MDI3NzcwNzM2OTMyOnwwP915wLHfcy2XVntKYmwXJ3UB"

# Sleep time in seconds
sleep_time = 1

# Specify the Gartner's Bitbucket Server project key
bitbucket_server_project_keys = [ "P4", "P3", "P2", "P1"]

# Specify the Gartner's Bitbucket Server repository names
bitbucket_server_repo_slugs = [["p4repo1", "p4repo2", "p4repo3", "p4repo4"], ["p3repo1", "ec2", "wordpress"], ["p2repo1", "p2repo2", "wordpress"], ["p1repo1", "p1repo2", "ec2", "wordpress"]]

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
    
key_of_repos = dict(zip(bitbucket_server_project_keys, bitbucket_server_repo_slugs))

for bitbucket_server_project_key in bitbucket_server_project_keys:
    logging.info(f"Project key: {bitbucket_server_project_key}")
    if bitbucket_server_project_key in key_of_repos:
        selected_repos = key_of_repos[bitbucket_server_project_key]
        #logging.info("Selected repositories:", selected_repos)
        for bitbucket_server_repo_slug in selected_repos:
            logging.info(f"Execution started for Repo name: {bitbucket_server_repo_slug}")
            
            # Gartner's Bitbucket Server API endpoints
            gt_bitbucket_server_api_url = f"http://{gt_bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos/{bitbucket_server_repo_slug}"
            gt_bitbucket_server_branch_api_url =f"{gt_bitbucket_server_api_url}/branches"
            gt_bitbucket_server_pr_api_url = f"{gt_bitbucket_server_api_url}/pull-requests"

            # TN's Bitbucket Server API endpoints
            tn_bitbucket_server_api_url = f"http://{tn_bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"
            tn_bitbucket_server_api_url_repo = f"{tn_bitbucket_server_api_url}/{bitbucket_server_repo_slug}"
            tn_bitbucket_server_pr_api_url = f"{tn_bitbucket_server_api_url_repo}/pull-requests"


            # Gartner's Bitbucket Server Repository URL
            gt_server_repo_clone_url = f'http://{gt_bitbucket_server_username}:{gt_bitbucket_server_http_token}@{gt_bitbucket_server}/scm/{bitbucket_server_project_key}/{bitbucket_server_repo_slug}.git'

            # TN's Bitbucket Server Repository URL
            tn_server_repo_clone_url = f'http://{tn_bitbucket_server_username}:{tn_bitbucket_server_http_token}@{tn_bitbucket_server}/scm/{bitbucket_server_project_key}/{bitbucket_server_repo_slug}.git'
                        
            # Fetch repository information from Gartner's Bitbucket Server
            response = requests.get(gt_bitbucket_server_api_url, auth=(gt_bitbucket_server_username, gt_bitbucket_server_http_token))
            if response.status_code != 200:
                logging.error(f"Failed to fetch {bitbucket_server_repo_slug} repository information from Gartner's Bitbucket Server. Error: {response.text} \n")
                #exit(1)
                break
            else:
                logging.info(f"Fetched {bitbucket_server_repo_slug} repository information from Gartner's Bitbucket Server.")

            repo_data = response.json()

            # Fetch repository information from Gartner's Bitbucket Server
            responseb = requests.get(gt_bitbucket_server_branch_api_url, auth=(gt_bitbucket_server_username, gt_bitbucket_server_http_token))
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
                    logging.info(f"Main branch is {default_branch_name} for {bitbucket_server_repo_slug} repository on Gartner's Bitbucket Server.")
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
            create_response = requests.post(tn_bitbucket_server_api_url, json=payload, auth=(tn_bitbucket_server_username, tn_bitbucket_server_http_token))
            get_response = requests.get(tn_bitbucket_server_api_url_repo, json=payload, auth=(tn_bitbucket_server_username, tn_bitbucket_server_http_token))
            
            if create_response.status_code != 201 and get_response.status_code != 200:
                logging.error(f"Failed to create {bitbucket_server_repo_slug} repository in TN's Bitbucket Server. Error: {create_response.text} {get_response.text} \n")
                #exit(1)
                break
            else:
                response_tn = requests.put(tn_bitbucket_server_api_url_repo, json=payload, auth=(tn_bitbucket_server_username, tn_bitbucket_server_http_token))

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
            logging.info(f"Will wait for {sleep_time} seconds before proceeding to next step")
            time.sleep(sleep_time)
            logging.info("Proceeding to next step")
logging.info ("Execution Complete.\n")