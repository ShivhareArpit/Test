from atlassian import Confluence
import csv

conf_site = '<CONFLUENCE-SITE-URL'                          # Ex: 'https://test-con.atlassian.net'
conf_user = '<EMAIL-OF-USER'
conf_pass = "<API-TOKEN>"                                   # URL to generate API token: https://id.atlassian.com/manage-profile/security/api-tokens

# Find and replace strings
original_string = "<STRING-TO-FIND-FOR-REPLACEMENT>"        # Ex: "gartner.com"
new_string = "<STRING-TO-REPLACE>"                          # Ex: "talentneuron.com"

csvfile = '<PATH-OF-CSV-WHICH-CONTAINS-PAGE-ID-AND-TITLE>'  # Ex: 'D:\Talent_Neuron\Confluence/SPACE_project_list.csv'
# Connect to Confluence
conf = Confluence(url=conf_site, username=conf_user, password=conf_pass)

# Read page details from CSV file
with open(csvfile, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # Skip header row
    for row in csvreader:
        page_id = row[0]  # Assuming the first column is page ID
        page_title = row[1]  # Assuming the second column is page title

        # Retrieve page content
        page = conf.get_page_by_id(page_id, expand='body.storage')
        page_content = page['body']['storage']['value']
        page_body = page_content.replace(original_string, new_string)

        # Update page content
        conf.update_existing_page(page_id, page_title, page_body)
        print(f"Updated page ID {page_id} - {page_title}")

print("All pages updated successfully.")
