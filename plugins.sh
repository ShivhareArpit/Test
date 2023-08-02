#!/bin/bash
sudo yum install perl -y

JENKINS_VERSION="2.401.3"
PLUGIN_DOWNLOAD_DIR="/var/lib/jenkins/plugins/"
serverip=$(hostname -i)
initialpassword=$(cat /var/lib/jenkins/secrets/initialAdminPassword)
#jenkins_url="http://admin:$initialpassword@$serverip:8080"
serverip=$(hostname -i)

plugin_names=("amazon-ecs:1.48" "bitbucket:223.vd12f2bca5430" "jfrog:1.4.0" "sonar:2.15")

wget https://github.com/jenkinsci/plugin-installation-manager-tool/releases/download/2.12.13/jenkins-plugin-manager-2.12.13.jar

chmod +x jenkins-plugin-manager-2.12.13.jar

# Function to check if the plugin is installed
function is_plugin_installed() {
    local plugin="$1"
    local is_installed=$(curl -sSL -u admin:$initialpassword "http://$serverip:8080/pluginManager/api/xml?depth=1&xpath=/*/*/shortName|/*/*/version&wrapper=plugins" \
    | perl -pe 's/.*?<shortName>([\w-]+).*?<version>([^<]+)()(<\/\w+>)+/\1 \2\n/g'|sed 's/ /:/' | grep -w "$plugin")
    if [ -n "$is_installed" ]; then
        echo "Plugin $plugin is already installed."
        return 0  # Plugin is installed
    else
        echo "Plugin $plugin is not installed."
        return 1  # Plugin is not installed
    fi
} 

for plugin_name in ${plugin_names[@]}; do
    echo $plugin_name
    # Check if the plugin is installed
    if is_plugin_installed "$plugin_name"; then
        echo "Skipping plugin installation. The plugin is already installed."
    else
        echo "Plugin not found. Running the installation command..."
        sudo java -jar jenkins-plugin-manager-2.12.13.jar --jenkins-version $JENKINS_VERSION  \
        --plugin-download-directory $PLUGIN_DOWNLOAD_DIR --plugins "$plugin_name"
    fi
done