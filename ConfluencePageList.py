import requests
import os
import csv

conf_url = 'https://test-con.atlassian.net'
conf_user = 'arpit.shivhare@newvision-software.com'
conf_pass = "ATATT3xFfGF0i0MzDCctW3Gm2ZKb7kUSGnO7B5LsscIKrQZ33S5Kj4lUNqD9GPMvdmeM6DaMfrPdoVn8SyY8E9VkGbZNmD4Al2QDCbvpayaMrTx6Ww66BclHpLS9zUWDvQijWNmGrhmAvFJi6kalfOhp_FSK9wJgo5tiYdiuFPvHEmWulP-GSKI=ECBDAB12"

# conf_url = "https://siteforkt.atlassian.net"
# conf_user = "randomemail@guysmail.com"
# conf_pass = "ATATT3xFfGF0xvDaHav7W648ZKOawxycsF4HwBkvgjX0svwEn2TEnor9pPpSZstGumOlR-PkvkdXpklNVGwEYOMcal2aIGQziZ0dfLQLA5yGdLPZ71NFh-EGIjIe-dFtEahn-BZEt7Q6L7AauPlgmZrIN1uU-izYP_3I3w03IDELSgYnjPMD47c=D1444803"

space_key = "SPACE"

all_title = []
all_id = []
i = 1

auth = (conf_user, conf_pass)

def get_page_content(page_id, headers):
    url = f"{conf_url}/wiki/rest/api/content/{page_id}"
    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        page_details = response.json()
        return page_details
    else:
        print(f"Error fetching page {page_id}: {response.status_code}")
        return None

def main():
    headers = {
        "Content-Type": "application/json"
    }
    global i
    start = 0  # Starting index for pagination
    limit = 25  # Number of results per page
    
    while True:
        url = f"{conf_url}/wiki/rest/api/space/{space_key}/content?type=page&start={start}&limit={limit}"
        response = requests.get(url, headers=headers, auth=auth)
        
        if response.status_code == 200:
            pages = response.json().get("page", {}).get("results", [])
            
            if not pages:
                break  # No more pages to retrieve
            
            for page in pages:
                page_id = page["id"]
                page_title = page["title"]
                #print("Page ID:", page_id)
                #print("Page Title:", page_title)
                print(f"On page no. {i}")
                all_title.append(page_title)
                all_id.append(page_id)
                page_details = get_page_content(page_id, headers)
                if page_details:
                    children = page_details.get("children", [])
                    if children:
                        print("Child Pages:")
                        for child in children:
                            child_title = child["title"]
                            print("  -", child_title)
                #print("---")
                i = i + 1
            
            start += limit  # Move to the next page of results
        else:
            print("Error:", response.status_code)
            break

if __name__ == "__main__":
    main()

# Export the all_repo list to a CSV file
csv_filename = f"{space_key}_project_list.csv"
cdir = os.getcwd()
with open(csv_filename, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Page ID", "Page Title"])  # Write header
    for proj_i, proj_t in zip(all_id, all_title):
        csv_writer.writerow([proj_i, proj_t])

print(f"Page list of {space_key} has been exported to {cdir}/{csv_filename}")