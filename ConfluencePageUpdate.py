from atlassian import Confluence
import csv

conf_site = 'https://test-con.atlassian.net'
conf_user = 'arpit.shivhare@newvision-software.com'
conf_pass = "ATATT3xFfGF0i0MzDCctW3Gm2ZKb7kUSGnO7B5LsscIKrQZ33S5Kj4lUNqD9GPMvdmeM6DaMfrPdoVn8SyY8E9VkGbZNmD4Al2QDCbvpayaMrTx6Ww66BclHpLS9zUWDvQijWNmGrhmAvFJi6kalfOhp_FSK9wJgo5tiYdiuFPvHEmWulP-GSKI=ECBDAB12"

# conf_url = "https://siteforkt.atlassian.net"
# conf_user = "randomemail@guysmail.com"
# conf_pass = "ATATT3xFfGF0xvDaHav7W648ZKOawxycsF4HwBkvgjX0svwEn2TEnor9pPpSZstGumOlR-PkvkdXpklNVGwEYOMcal2aIGQziZ0dfLQLA5yGdLPZ71NFh-EGIjIe-dFtEahn-BZEt7Q6L7AauPlgmZrIN1uU-izYP_3I3w03IDELSgYnjPMD47c=D1444803"

# Find and replace strings
original_string = "gartner.com"
new_string = "talentneuron.com"

csvfile = 'D:\Talent Neuron\Confluence/SPACE_project_list.csv'
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
