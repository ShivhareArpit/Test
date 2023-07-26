#!/bin/bash
# Replace "/path/to/source/directory" with the directory containing your ZIP and GZIP files
source_directory="/pkg"

custom_dir="/gartner/app/jenkins/tools/"
tools=("jdk-17.0.8" "jdk-19.0.2" "jdk-20.0.2" "node-v18.16.0")

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


tar -xzvf "jdk-19.0.2_linux-x64_bin.tar.gz" -C "/gartner/app/jenkins/tools/"