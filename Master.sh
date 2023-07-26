#!/bin/bash
set -euxo pipefail
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

#Function to copy plugins.zip frm S3 to EC2
function copyplugins() {
  cd /
  mkdir -p /home/jenkins/plugins
  mkdir -p /home/jenkins/tools
  sudo yum install unzip -y
  sudo yum install amazon-efs-utils
  mkdir -p /gartner/app/jenkins/tools/
  cd /home/jenkins/plugins
  if [ ! -f "plugins.zip" ]; then
    aws s3 cp s3://tools-and-plugins/plugins.zip /home/jenkins/plugins
    unzip plugins.zip
  fi
  cd /home/jenkins/tools
  if [ ! -f "tools.zip" ]; then
    aws s3 cp s3://tools-and-plugins/tools.zip /home/jenkins/tools
    unzip tools.zip
  fi
}

#Function to install Plugins in Jenkins Master
function pluginsinstall() {
  jenkins_home="/var/lib/jenkins"
  initialpassword=$(cat /var/lib/jenkins/secrets/initialAdminPassword)
  serverip=$(hostname -i)
  JENKINS_URL="http://admin:$initialpassword@$serverip:8080"
  
  cd /home/jenkins/plugins
  sleep 60
  wget http://"$serverip":8080/jnlpJars/jenkins-cli.jar
  chmod 777 -R /home
  home_plugins_dir="/home/jenkins/plugins/"
  jenkins_plugins_dir="/var/lib/jenkins/plugins"
  jenkins_cli_jar="/home/jenkins/plugins/jenkins-cli.jar"

  # Compare and install plugins in Jenkins Master
  for plugin_file in "$home_plugins_dir"/*.hpi; do
    plugin_ext=$(basename "$plugin_file")
    plugin="$(basename "$plugin_ext" | cut -d '.' -f 1)"
    echo $plugin
    if [ ! -f "$jenkins_plugins_dir/$plugin.jpi" ]; then
        echo "Installing $plugin..."
        java -jar jenkins-cli.jar -s "http://admin:$initialpassword@$serverip:8080" install-plugin file://"$home_plugins_dir"/"$plugin_ext"
    else
       echo "Plugin $plugin is already Installed..."
    fi
  done
  #sudo systemctl restart jenkins
}

#Function to Install Tools in Jenkins Master 
function toolsinstall() {

# Replace "/path/to/source/directory" with the directory containing your ZIP and GZIP files
source_directory="/home/jenkins/tools/"

custom_dir="/gartner/app/jenkins/tools/"
tools=("jdk-17.0.8" "jdk-19.0.2" "jdk-20.0.2" "node-v18.16.0-linux-arm64")

# Change to the source directory to ensure the correct paths in the ZIP and GZIP files
cd "$source_directory"

# Function to check if a directory exists
check_dir_exists() {
  if [ -d "$1" ]; then
    echo "Directory '$1' exists."
    echo "Skipping installation of '$1'."
  else
    echo "Directory '$1' does not exist."
    # Loop through all .gz files and extract them to the custom location
    for gz_file in "$2"*.gz; do
      if [ -f "$gz_file" ]; then
        echo "Installing '$gz_file'"
        tar -xzvf "$gz_file" -C "$custom_dir"
      fi
    done
    for zip_file in "$2"*.zip; do
      if [ -f "$zip_file" ]; then
        echo "Installing '$zip_file'"
        unzip "$zip_file" -d "$custom_dir"
      fi
    done
  fi
}

# Check if the custom directory exists
#check_dir_exists "$custom_dir"

# Check if the paths formed by tools exist
for tool in "${tools[@]}"; do
  tool_path="$custom_dir$tool"
  check_dir_exists "$tool_path" "$tool"
done
}

##Jcasc configiguration
function update_jenkins_with_jcasc() {
  JENKINS_HOME="/var/lib/jenkins"
  cas_global_config="$JENKINS_HOME/io.jenkins.plugins.casc.CasCGlobalConfig.xml"
  jcasc_config_file="$JENKINS_HOME/jenkins.yaml"

  if [ ! -f "$jcasc_config_file" ]; then
    echo "File is not present in $JENKINS_HOME copying from s3"
    aws s3 cp s3://tools-and-plugins/jenkins.yaml $JENKINS_HOME
    cd $JENKINS_HOME
    chown jenkins:jenkins jenkins.yaml
  else
    echo "File is present in $JENKINS_HOME"
  fi

  if [ ! -f "$cas_global_config" ]; then
    echo "CasC global xml file is not present in $JENKINS_HOME creating file"
    # Create and update CasC global xml file
cat <<EoF > "$cas_global_config"
<?xml version='1.1' encoding='UTF-8'?>
<io.jenkins.plugins.casc.CasCGlobalConfig plugin=configuration-as-code@1670.v564dc8b_982d0>
  <configurationPath>$jcasc_config_file</configurationPath>
</io.jenkins.plugins.casc.CasCGlobalConfig>
EoF
  else
    echo "CasC global xml file is present in $JENKINS_HOME"
  fi

  chown jenkins:jenkins $cas_global_config
  #sudo systemctl restart jenkins
}

function exclude_jenkins_package_from_yum_updates(){
  printf "\n\n*** Executing function: $FUNCNAME ***\n\n"
  
  cat <<EoF > /etc/yum.repos.d/jenkins.repo
[jenkins]
name=Jenkins
baseurl=http://pkg.jenkins.io/redhat
gpgcheck=1
# Exclude jenkins from yum updates
exclude=jenkins
EoF
}

function update_firewalld(){
  local firewalldConf='/etc/firewalld/firewalld.conf'
  printf "\n\n*** Executing function: $FUNCNAME ***\n\n"
  printf "\n\n***\n*** Updating local firewall rules\n***\n\n"

  # Disable zone drifting
  if $(grep 'AllowZoneDrifting=yes' $firewalldConf  &>/dev/null); then
    sed -i 's/^AllowZoneDrifting=yes/AllowZoneDrifting=no/' $firewalldConf
  fi

  firewall-offline-cmd --zone=public --set-target=DROP \
  && firewall-offline-cmd --add-port=22/tcp --add-port=8080/tcp \
  && systemctl restart firewalld
}

function update_jenkins_sysconfig(){
  printf "\n\n*** Executing function: $FUNCNAME ***\n\n"
  local JENKINS_HOME="var/lib/jenkins"

  cat <<EoF > /etc/sysconfig/jenkins
JENKINS_HOME=$JENKINS_HOME
JENKINS_JAVA_CMD=""
JENKINS_USER="jenkins"
JENKINS_PORT="8080"
JENKINS_LISTEN_ADDRESS=""
JENKINS_HTTPS_PORT=""
JENKINS_HTTPS_KEYSTORE=""
JENKINS_HTTPS_KEYSTORE_PASSWORD=""
JENKINS_HTTPS_LISTEN_ADDRESS=""
JENKINS_DEBUG_LEVEL="5"
JENKINS_ENABLE_ACCESS_LOG="no"
JENKINS_HANDLER_MAX="300"
JENKINS_HANDLER_IDLE="50"
JENKINS_ARGS="--sessionTimeout=350 --sessionEviction=14400"
EoF
}

function update_thread_max(){
  printf "\n\n*** Executing function: $FUNCNAME ***\n\n"

  cat <<EoF > /etc/security/limits.d/30-jenkins.conf
jenkins soft core unlimited
jenkins hard core unlimited
jenkins soft fsize unlimited
jenkins hard fsize unlimited
jenkins soft nofile 18192
jenkins hard nofile 232768
jenkins soft nproc 61308
jenkins hard nproc 61308
EoF
}

# function get_dsl_jobs(){
#   printf "\n\n*** Executing function: $FUNCNAME ***\n\n"
#   local dsl_jobs="$jenkins_master_fldr/$dsl_job_archive"
#   curl -s $dsl_jobs | tar -zxv -C $jenkins_home \
#   && chown -Rv jenkins:jenkins "$jenkins_home/init.groovy.d" || exit 1
# }

# Calling all the required functions
copyplugins
pluginsinstall
toolsinstall
update_jenkins_with_jcasc
exclude_jenkins_package_from_yum_updates
#update_firewalld
update_jenkins_sysconfig
update_thread_max

sudo systemctl try-restart jenkins