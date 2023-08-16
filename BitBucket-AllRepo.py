import requests
import subprocess
import platform
import time
import os

# Bitbucket Server (self-hosted) details
bitbucket_server="<BITBUCKET-SERVER-URL-WITHOUT-HTTP>"
bitbucket_server_username = "<BITBUCKET-SERVER-USER>"
bitbucket_server_http_token = "<HTTP-TOKEN>"

# Bitbucket Cloud details
bitbucket_cloud_username = "<BITBUCKET-CLOUD-USER>"
bitbucket_cloud_app_password = "<APP-PASSWORD>"
bitbucket_cloud_workspace = "<WORKSPACE-NAME-BITBUCKET-CLOUD>"

# Sleep time in seconds
sleep_time = 30

# Specify the Bitbucket Server project key
bitbucket_server_project_keys = ["P1", "P2", "P3"]

skip_repo = ["ec2", "wordpress"]

# Function to delete .git folder
def remove_gitfolder(new_dir):
    try:
        system_platform = platform.system()
        if system_platform == "Windows":
            cmd = f'rmdir /s /q "{new_dir}"'
        else:
            cmd = f'rm -rf "{new_dir}"'
        
        subprocess.run(cmd, shell=True, check=True)
        print(f"Removed '{new_dir}' directory and its contents successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while removing '{new_dir}': {e}")
    
for bitbucket_server_project_key in bitbucket_server_project_keys:
    print(f"\nExecution started for Project key: {bitbucket_server_project_key}")
    # Bitbucket Server API endpoint for projects
    bitbucket_server_projects_api_url = f"http://{bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos"

    next_page_start = 0
    while True:
        params = {"start": next_page_start}
        response_server = requests.get(bitbucket_server_projects_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token), params=params)
        
        if response_server.status_code == 200:
            repo_list = response_server.json()["values"]
            print(f"Successfully fetched repository list from Bitbucket Server")

            for repo_data in repo_list:
                bitbucket_server_repo_slug = repo_data["slug"]
                
                if bitbucket_server_repo_slug in skip_repo:
                    print(f"\nExecution skipped for Repository name: {bitbucket_server_repo_slug} of {bitbucket_server_project_key} project")
                else:

                    print(f"\nExecution started for Repository name: {bitbucket_server_repo_slug} of {bitbucket_server_project_key} project")
                    
                    # Bitbucket Server API endpoints
                    bitbucket_server_api_url = f"http://{bitbucket_server}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos/{bitbucket_server_repo_slug}"
                    bitbucket_server_pr_api_url = f"{bitbucket_server_api_url}/pull-requests"

                    # Bitbucket Cloud API endpoints
                    bitbucket_cloud_api_url = f"https://api.bitbucket.org/2.0/repositories/{bitbucket_cloud_workspace}/{bitbucket_server_repo_slug}"
                    bitbucket_cloud_pr_api_url = f"{bitbucket_cloud_api_url}/pullrequests"

                    #Bitbucket Server Repository URL
                    server_repo_clone_url = f'http://{bitbucket_server_username}:{bitbucket_server_http_token}@{bitbucket_server}/scm/{bitbucket_server_project_key}/{bitbucket_server_repo_slug}.git'
                    #Bitbucket Cloud Repository URL
                    bitbucket_cloud_url = f"https://{bitbucket_cloud_username}:{bitbucket_cloud_app_password}@bitbucket.org/{bitbucket_cloud_workspace}/{bitbucket_server_repo_slug}"

                    # Fetch repository information from Bitbucket Server
                    response = requests.get(bitbucket_server_projects_api_url + f"/{bitbucket_server_repo_slug}", auth=(bitbucket_server_username, bitbucket_server_http_token))
                    if response.status_code != 200:
                        print(f"Failed to fetch {bitbucket_server_repo_slug} repository information from Bitbucket Server. \nError: {response.text}")
                        exit(1)
                    else:
                        print(f"Fetched {bitbucket_server_repo_slug} repository information from Bitbucket Server.")

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
                        print(f"Failed to create/update {bitbucket_server_repo_slug} repository in Bitbucket Cloud. \nError: {response.text}")
                        exit(1)
                    else:
                        print(f"Configuring {bitbucket_server_repo_slug} repository on Bitbucket Cloud.")
                        # Fetch the Bitbucket Server repository
                        print(f"Cloning {bitbucket_server_repo_slug} repository from Bitbucket server.")
                        fetch_cmd = f"git clone --mirror {server_repo_clone_url}"
                        fetch_process = subprocess.Popen(fetch_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        fetch_process.wait()
                        if fetch_process.returncode != 0:
                            print(f"Failed to clone {bitbucket_server_repo_slug} repository from Bitbucket Server.")
                            print(fetch_process.stderr.read().decode())
                            exit(1)
                        else:
                            print(f"Successfully cloned {bitbucket_server_repo_slug} repository from Bitbucket Server.")
                        
                        # Change directory to .git folder
                        new_dir = f"./{bitbucket_server_repo_slug}.git"
                        os.chdir(new_dir)

                        # Push the fetched repository to the Bitbucket Cloud repository
                        print(f"Pushing {bitbucket_server_repo_slug} repository to Bitbucket Cloud")
                        push_cmd = f"git push --mirror {bitbucket_cloud_url}.git"
                        push_process = subprocess.Popen(push_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        push_process.wait()
                        if push_process.returncode == 0:
                            print("Bitbucket Server repository synced with Bitbucket Cloud repository.")
                            
                            # Change directory back to original path
                            os.chdir("..")
                            # Using function to delete .git folder
                            remove_gitfolder(new_dir)
                        else:
                            print("Failed to push/sync Bitbucket Server repository with Bitbucket Cloud repository.")
                            print(push_process.stderr.read().decode())
                            
                            # Change directory back to original path
                            os.chdir("..")
                            # Using function to delete .git folder
                            remove_gitfolder(new_dir)
                            exit(1)

                        # Fetch and sync pull requests from Bitbucket Server to Bitbucket Cloud
                        pr_response = requests.get(bitbucket_server_pr_api_url, auth=(bitbucket_server_username, bitbucket_server_http_token))
                        if pr_response.status_code == 200:
                            print("Fetched pull requests data from Bitbucket Server.")
                            pr_data = pr_response.json()
                            for pr in pr_data["values"]:
                                pr_title = pr["title"]
                                pr_description = pr["description"]
                                pr_source_branch = pr["fromRef"]["displayId"]
                                pr_destination_branch = pr["toRef"]["displayId"]

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
                                    print(f"Pull request '{pr_title}' created in Bitbucket Cloud.")
                                else:
                                    print(f"Failed to create pull request '{pr_title}' in Bitbucket Cloud. \nError: {pr_create_response.text}")
                        else:
                            print(f"Failed to fetch pull requests from Bitbucket Server. \nError: {pr_response.text}")
            
                print(f"Will wait for {sleep_time} seconds before proceeding to next step")
                time.sleep(sleep_time)
                print("Proceeding to next step")

            if "isLastPage" in response_server.json() and response_server.json()["isLastPage"]:
                break  # Break the loop if it's the last page
            
            next_page_start = response_server.json()["nextPageStart"]
        else:
            print(f"Failed to fetch repository list from Bitbucket Server.\nError: {response_server.text}")
            exit(1)
print ("Execution Complete")
