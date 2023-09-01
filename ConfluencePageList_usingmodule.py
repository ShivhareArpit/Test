from atlassian import Confluence
import os
import csv

conf_url = 'https://test-con.atlassian.net'
conf_user = 'arpit.shivhare@newvision-software.com'
conf_pass = "ATATT3xFfGF0i0MzDCctW3Gm2ZKb7kUSGnO7B5LsscIKrQZ33S5Kj4lUNqD9GPMvdmeM6DaMfrPdoVn8SyY8E9VkGbZNmD4Al2QDCbvpayaMrTx6Ww66BclHpLS9zUWDvQijWNmGrhmAvFJi6kalfOhp_FSK9wJgo5tiYdiuFPvHEmWulP-GSKI=ECBDAB12"

# conf_url = "https://siteforkt.atlassian.net"
# conf_user = "randomemail@guysmail.com"
# conf_pass = "ATATT3xFfGF0xvDaHav7W648ZKOawxycsF4HwBkvgjX0svwEn2TEnor9pPpSZstGumOlR-PkvkdXpklNVGwEYOMcal2aIGQziZ0dfLQLA5yGdLPZ71NFh-EGIjIe-dFtEahn-BZEt7Q6L7AauPlgmZrIN1uU-izYP_3I3w03IDELSgYnjPMD47c=D1444803"

space_key = 'SPACE'

all_title = []
all_id = []

# Connect to Confluence
conf = Confluence(url=conf_url, username=conf_user, password=conf_pass)

for i in range(1, 101):  # Loop from 1 to 100
    
    # Get all pages from Space
    # content_type can be 'page' or 'blogpost'. Defaults to 'page'
    # expand is a comma separated list of properties to expand on the content.
    # max limit is 100. For more you have to loop over start values.
    # confluence.get_all_pages_from_space(space, start=0, limit=100, status=None, expand=None, content_type='page')

    pages = conf.get_all_pages_from_space(space_key, start=(i - 1) * 50, limit=50, status=None, expand=None, content_type='page')

    for page in pages:
        id_value = page['id']
        title_value = page['title']

        all_title.append(title_value)
        all_id.append(id_value)

# Export the all_repo list to a CSV file
csv_filename = f"{space_key}_project_list.csv"
cdir = os.getcwd()
with open(csv_filename, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Page ID", "Page Title"])  # Write header
    for proj_i, proj_t in zip(all_id, all_title):
        csv_writer.writerow([proj_i, proj_t])

print(f"Page list of {space_key} has been exported to {cdir}/{csv_filename}")