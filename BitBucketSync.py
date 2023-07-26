"""
Before running this Python program:
- Update the values in variables from line 22 to 32 as per your requirements.
- Ensure that the following modules are installed: requests, subprocess, and os.
  To install requests: pip install requests
  To install subprocess: pip install subprocess
  To install os: pip install os

To generate a Bitbucket Cloud App Password for a user, refer to:
https://support.atlassian.com/bitbucket-cloud/docs/create-an-app-password/

To delete a Bitbucket server repository folder:
- We are using the subprocess module and PowerShell command.
- Ensure that PowerShell is installed. If not, comment out code block from line 143 to 151.
- Alternatively, you can manually try to remove the folder or use the 'rm -rf <path>' command in the shell.
"""
import requests
import subprocess
import os

# Bitbucket Server (self-hosted) repository details
bitbucket_server_url = "<BITBUCKER-SERVER-URL-WITH-PORT>"
bitbucket_server_project_key = "<BITBUCKER-SERVER-PROJECT-KEY>"
bitbucket_server_repo_slug = "<BITBUCKER-SERVER-REPOSITORY-NAME>"
bitbucket_server_username = "<BITBUCKER-SERVER-USERNAME>"
bitbucket_server_password = "<BITBUCKER-SERVER-PASSWORD>"

# Bitbucket Cloud repository details
bitbucket_cloud_username = "<BITBUCKET-CLOUD-USERNAME>"
bitbucket_cloud_password = "<BITBUCKET-CLOUD-APP-PASSWORD>"
bitbucket_cloud_workspace = "<BITBUCKET-CLOUD-WORKSPACE-NAME>"

# Name of repository for Bitbucket server & cloud repository is same

# Bitbucket Server API endpoints
bitbucket_server_api_url = f"{bitbucket_server_url}/rest/api/1.0/projects/{bitbucket_server_project_key}/repos/{bitbucket_server_repo_slug}"
bitbucket_server_pr_api_url = f"{bitbucket_server_api_url}/pull-requests"

# Bitbucket Cloud API endpoints
bitbucket_cloud_api_url = f"https://api.bitbucket.org/2.0/repositories/{bitbucket_cloud_workspace}/{bitbucket_server_repo_slug}"
bitbucket_cloud_pr_api_url = f"{bitbucket_cloud_api_url}/pullrequests"

#Bitbuccket Cloud Repository URL
bitbucket_cloud_url = f"https://{bitbucket_cloud_username}:{bitbucket_cloud_password}@bitbucket.org/{bitbucket_cloud_workspace}/{bitbucket_server_repo_slug}"

# Fetch repository information from Bitbucket Server
response = requests.get(bitbucket_server_api_url, auth=(bitbucket_server_username, bitbucket_server_password))
if response.status_code != 200:
    print(f"Failed to fetch repository information from Bitbucket Server. Error: {response.text}")
    exit(1)

repo_data = response.json()

# Extract the repository URL from the server response
server_repo_clone_url = repo_data["links"]["clone"][0]["href"]

# Create or update repository in Bitbucket Cloud
headers = {
    "Content-Type": "application/json"
}
auth = (bitbucket_cloud_username, bitbucket_cloud_password)

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
    print(f"Failed to create/update repository in Bitbucket Cloud. Error: {response.text}")
    exit(1)
else:
    print("Synchronization completed successfully.")
    # Fetch the Bitbucket Server repository
    fetch_cmd = f"git clone --mirror {server_repo_clone_url}"
    fetch_process = subprocess.Popen(fetch_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    fetch_process.wait()
    if fetch_process.returncode != 0:
        print("Failed to fetch Bitbucket Server repository.")
        print(fetch_process.stderr.read().decode())
        exit(1)

    # Change directory to repository folder
    new_dir = f"./{bitbucket_server_repo_slug}.git"
    os.chdir(new_dir)
    os.getcwd()

    # Push the fetched repository to the Bitbucket Cloud repository
    push_cmd = f"git push --mirror {bitbucket_cloud_url}.git"
    push_process = subprocess.Popen(push_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    push_process.wait()
    if push_process.returncode == 0:
        print("Bitbucket Server repository synced with Bitbucket Cloud repository.")
    else:
        print("Failed to sync Bitbucket Server repository.")
        print(push_process.stderr.read().decode())
        exit(1)

    # Fetch and sync pull requests from Bitbucket Server to Bitbucket Cloud
    pr_response = requests.get(bitbucket_server_pr_api_url, auth=(bitbucket_server_username, bitbucket_server_password))
    if pr_response.status_code == 200:
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
                print(f"Failed to create pull request '{pr_title}' in Bitbucket Cloud. Error: {pr_create_response.text}")
    else:
        print(f"Failed to fetch pull requests from Bitbucket Server. Error: {pr_response.text}")

    # Change directory back to original path
    os.chdir("..")
    os.getcwd()
  
    # Delete Bitbucket server repository folder using subprocess module
    # Define the PowerShell command
    powershell_command = f'Remove-Item -Path "{new_dir}" -Force -Recurse'
    # Run the PowerShell command and capture the output
    output = subprocess.check_output(['powershell', '-Command', powershell_command], shell=True)
    # Decode the output as a string (optional)
    output = output.decode('utf-8')
    # Print the output
    print(output)