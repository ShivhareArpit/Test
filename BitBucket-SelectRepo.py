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

# Bitbucket Server (self-hosted) details
bitbucket_server="<BITBUCKET-SERVER-URL-WITHOUT-HTTP>"
bitbucket_server_username = "<BITBUCKET-SERVER-USER>"
bitbucket_server_http_token = "<HTTP-TOKEN>"

# Bitbucket Cloud details
bitbucket_cloud_username = "<BITBUCKET-CLOUD-USER>"
bitbucket_cloud_app_password = "<APP_PASSWORD>"
bitbucket_cloud_workspace = "<WORKSPACE-NAME-BITBUCKET-CLOUD>"

# Sleep time in seconds
sleep_time = 30

# Specify the Bitbucket Server project key
bitbucket_server_project_keys = ["P2", "P3", "P1"]

# Specify the Bitbucket Server repository names
bitbucket_server_repo_slugs = [["p2repo1", "p2repo2"], ["p3repo1"], ["p1repo1"]]

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
            # Bitbucket Server API endpoints
            bitbucket_server_api_url = f"https://{bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos/{bitbucket_server_repo_slug}"
            bitbucket_server_pr_api_url = f"{bitbucket_server_api_url}/pull-requests"

            # Bitbucket Cloud API endpoints
            bitbucket_cloud_api_url = f"https://api.bitbucket.org/2.0/repositories/{bitbucket_cloud_workspace}/{bitbucket_server_repo_slug}"
            bitbucket_cloud_pr_api_url = f"{bitbucket_cloud_api_url}/pullrequests"

            #Bitbucket Server Repository URL
            server_repo_clone_url = f'https://{bitbucket_server_username}:{bitbucket_server_http_token}@{bitbucket_server}/scm/{bitbucket_server_project_key}/{bitbucket_server_repo_slug}.git'
            #Bitbucket Cloud Repository URL
            bitbucket_cloud_url = f"https://{bitbucket_cloud_username}:{bitbucket_cloud_app_password}@bitbucket.org/{bitbucket_cloud_workspace}/{bitbucket_server_repo_slug}"

            # Fetch repository information from Bitbucket Server
            response = requests.get(bitbucket_server_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token))
            if response.status_code != 200:
                logging.error(f"Failed to fetch {bitbucket_server_repo_slug} repository information from Bitbucket Server. Error: {response.text} \n")
                #exit(1)
                break
            else:
                logging.info(f"Fetched {bitbucket_server_repo_slug} repository information from Bitbucket Server.")

            repo_data = response.json()
            
            # Create or update repository in Bitbucket Cloud
            headers = {
                "Content-Type": "application/json"
            }
            auth = (bitbucket_cloud_username, bitbucket_cloud_app_password)

            # Prepare payload
            payload = {
                "scm": repo_data["scmId"],
                "is_private": not repo_data["public"],
                "fork_policy": "no_public_forks",
                "name": repo_data["name"],
                #"description": repo_data["description"],
            }

            # Create or update repository in Bitbucket Cloud
            response = requests.put(bitbucket_cloud_api_url, headers=headers, auth=auth, json=payload)

            if response.status_code != 200:
                logging.error(f"Failed to create/update {bitbucket_server_repo_slug} repository in Bitbucket Cloud. Error: {response.text} \n")
                #exit(1)
                break
            else:
                logging.info(f"Configuring {bitbucket_server_repo_slug} repository on Bitbucket Cloud.")
                # Fetch the Bitbucket Server repository
                logging.info(f"Cloning {bitbucket_server_repo_slug} repository from Bitbucket server.")
                fetch_cmd = f"git clone --mirror {server_repo_clone_url}"
                fetch_process = subprocess.Popen(fetch_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                fetch_process.wait()
                if fetch_process.returncode != 0:
                    logging.error(f"Failed to clone {bitbucket_server_repo_slug} repository from Bitbucket Server.")
                    logging.error(fetch_process.stderr.read().decode())
                    #exit(1)
                    break
                else:
                    logging.info(f"Successfully cloned {bitbucket_server_repo_slug} repository from Bitbucket Server.")
                
                # Change directory to .git folder
                new_dir = f"./{bitbucket_server_repo_slug}.git"
                os.chdir(new_dir)

                # Push the fetched repository to the Bitbucket Cloud repository
                logging.info(f"Pushing {bitbucket_server_repo_slug} repository to Bitbucket Cloud")
                push_cmd = f"git push --mirror {bitbucket_cloud_url}.git"
                push_process = subprocess.Popen(push_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                push_process.wait()
                if push_process.returncode == 0:
                    logging.info("Bitbucket Server repository synced with Bitbucket Cloud repository.")
                    
                    # Change directory back to original path
                    os.chdir("..")
                    # Using function to delete .git folder
                    remove_gitfolder(new_dir)
                else:
                    logging.error("Failed to push/sync Bitbucket Server repository with Bitbucket Cloud repository.")
                    logging.error(push_process.stderr.read().decode())
                    
                    # Change directory back to original path
                    os.chdir("..")
                    # Using function to delete .git folder
                    remove_gitfolder(new_dir)
                    #exit(1)
                    break

                # Fetch and sync pull requests from Bitbucket Server to Bitbucket Cloud
                pr_response = requests.get(bitbucket_server_pr_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token))
                if pr_response.status_code == 200:
                    logging.info("Fetched pull requests data from Bitbucket Server.")
                    pr_data = pr_response.json()
                    for pr in pr_data["values"]:
                        pr_title = pr["title"]
                        pr_source_branch = pr["fromRef"]["displayId"]
                        pr_destination_branch = pr["toRef"]["displayId"]

                        if "description" in pr:
                            pr_description = pr["description"]
                            # Create the pull request in Bitbucket Cloud
                            pr_payload = {
                                "title": pr_title,
                                "description": pr_description,  # Add description if not empty
                                "source": {
                                    "branch": {
                                        "name": pr_source_branch
                                    }
                                },
                                "destination": {
                                    "branch": {
                                        "name": pr_destination_branch
                                    }
                                }
                            }
                        else:
                            # Create the pull request in Bitbucket Cloud
                            pr_payload = {
                                "title": pr_title,
                                "source": {
                                    "branch": {
                                        "name": pr_source_branch
                                    }
                                },
                                "destination": {
                                    "branch": {
                                        "name": pr_destination_branch
                                    }
                                }
                            }
                        
                        pr_create_response = requests.post(bitbucket_cloud_pr_api_url, headers=headers, auth=auth, json=pr_payload)
                        if pr_create_response.status_code == 201:
                            logging.info(f"Pull request '{pr_title}' created in Bitbucket Cloud.")
                        else:
                            logging.error(f"Failed to create pull request '{pr_title}' in Bitbucket Cloud. Error: {pr_create_response.text} \n")
                else:
                    logging.error(f"Failed to fetch pull requests from Bitbucket Server. Error: {pr_response.text} \n")
            logging.info(f"Will wait for {sleep_time} seconds before proceeding to next step")
            time.sleep(sleep_time)
            logging.info("Proceeding to next step")
logging.info ("Execution Complete.\n")