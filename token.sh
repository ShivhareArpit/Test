#!/bin/bash

function update_jenkins_with_jcasc() {
  # Replace the following variables with your actual values
  serverip=$(hostname -i)
  jenkins_url="http://$serverip:8080"
  jenkins_user="admin"
  initialpassword=$(cat /var/lib/jenkins/secrets/initialAdminPassword)
  #jenkins_token="1116b92098de3d38da1092ecbc65b4ded4"
  jcasc_config_file="/var/lib/jenkins/casc/jenkins.yaml"
  token_name="newtoken"

# Run the curl command and store the JSON response in a variable
json_response=$(curl -s --cookie-jar /tmp/cookies -u $jenkins_user:$initialpassword $jenkins_url/crumbIssuer/api/json)

# Extract the crumb value using jq and store it in a variable
crumb=$(echo "$json_response" | jq -r '.crumb')

# Print the crumb value (optional, for verification)
echo "Crumb value: $crumb"

token=$(curl -X POST -H "Jenkins-Crumb: $crumb" --cookie /tmp/cookies $jenkins_url/me/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken?newTokenName=\$token_name -u $jenkins_user:$initialpassword)

jenkins_token=$(echo "$token" | jq -r '.data.tokenValue')

echo "Token Value: $jenkins_token"

  # Use curl to apply the JCASC configuration to Jenkins
  curl -X POST "$jenkins_url/configuration-as-code/apply" \
    --user "$jenkins_user:$jenkins_token" \
    --header "Content-Type: application/xml" \
    --data-binary "@$jcasc_config_file"
}

# Call the function to update Jenkins with JCASC configuration
update_jenkins_with_jcasc
