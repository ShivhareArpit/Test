from atlassian import Confluence
import os
import csv

conf_url =  '<CONFLUENCE-SITE-URL'  # Ex: 'https://test-con.atlassian.net'
conf_user = '<EMAIL-OF-USER'
conf_pass = "<API-TOKEN>"           # URL to generate API token: https://id.atlassian.com/manage-profile/security/api-tokens

space_key = '<SPACE-KEY>'

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