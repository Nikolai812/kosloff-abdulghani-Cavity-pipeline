#!/bin/bash

# Save the current working directory
logfile="ui_selenium.log"
echo "Started run_pacupp.bash script at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"
start_dir=$(pwd)
echo "Start directory: $start_dir" | tee -a "$logfile"
logfile="$(pwd)/ui_selenium.log"
echo "Logfile defined as $logfile" | tee -a "$logfile"

#CONFIGURATION: Pacupp script and output directories
pacupp_dir="/mnt/c/pipeline/JPipeline_PACUPP/Fill_Cavities_PACUPP"
pacupp_spreadsheet_lists_dir="$pacupp_dir/output-files/spreadsheet-ready-lining-lists"

# CONFIGURATION: PDB files input directory, pacupp python feed up directory
# (Normal place- inside the uh-cast-p-fold project.)
# pipeline_base="/mnt/c/Users/user/source/repos/uh-cast-p-fold"
pipeline_base=$start_dir
input_dir="$pipeline_base/UI_SELENIUM/input"
pacupp_python_feedup="$pipeline_base/UI_SELENIUM/pacupp_python_feedup"
# (input_dir="/mnt/c/Users/user/Ubuntu/INPUT_PDB")

echo "!!!!!!!!!!! DIRECTORY CONFIGURATION:" | tee -a "$logfile"
echo "pacupp_dir=$pacupp_dir" | tee -a "$logfile"
echo "pacupp_spreadsheet_lists_dir=$pacupp_spreadsheet_lists_dir" | tee -a "$logfile"
echo "pipeline_base=$pipeline_base" | tee -a "$logfile"
echo "input_dir=$input_dir" | tee -a "$logfile"
echo "pacupp_python_feedup=$pacupp_python_feedup" | tee -a "$logfile"
echo "!!!!!!!!!!!" | tee -a "$logfile"
echo "   " | tee -a "$logfile"
echo "   " | tee -a "$logfile"
echo "--------Beginning with previous results cleaning---------" | tee -a "$logfile"
echo "+++++++ Cleaning the pacupp_spreadsheet_lists_dir: $pacupp_spreadsheet_lists_dir" | tee -a "$logfile"
rm -f "$pacupp_spreadsheet_lists_dir"/*
echo "+++++++ Cleaning the pacupp_python_feedup: $pacupp_python_feedup" | tee -a "$logfile"
rm "$pacupp_python_feedup"/*

# List all .pdb files in the input directory
echo "Listing .pdb files in $input_dir:" | tee -a "$logfile"
ls "$input_dir"/*.pdb 2>/dev/null || echo "No .pdb files found in $input_dir at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"

# Gather all .pdb files into an array
pdb_input_files=("$input_dir"/*.pdb)

# Check if any .pdb files were found
if [ ${#pdb_input_files[@]} -eq 0 ]; then
    echo "No .pdb files found in $input_dir" | tee -a "$logfile"
    exit 1
fi

# Going tp pacupp directory
cd "$pacupp_dir" || { echo "Failed to go to $pacupp_dir at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"; exit 1; }
echo "we are inside: $(pwd) at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"



# Loop through each .pdb file
for current_pdb in "${pdb_input_files[@]}"; do
    echo "Processing $current_pdb at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"
    
    # Replace the second line in steps.spt with the new load command
    sed -i "2s|^.*|load $current_pdb;|" steps.spt

    # Echo the updated line for confirmation
    echo "Updated steps.spt: load $current_pdb;" | tee -a "$logfile"

    # Run the Java command in the background
    java -jar 1-Jmol.jar -g 1000x1000 steps.spt &

    # Store the PID of the Java process
    JAVA_PID=$!
    echo "java_pid=$JAVA_PID at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"

    # Wait for a specified delay (in seconds)
    DELAY=90  # Change this value to your desired delay
    sleep $DELAY

    # Kill the Java process
    kill $JAVA_PID
    echo "killing java process: $JAVA_PID at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"

    DELAY=2
done


# Exit the script 
echo "Copying pacupp spreadsheet lists from  $pacupp_spreadsheet_lists_dir to $pacupp_python_feedup (with force overwrite)" | tee -a "$logfile"
mkdir -p "$pacupp_python_feedup"
cp -f "$pacupp_spreadsheet_lists_dir"/*.txt "$pacupp_python_feedup"/



# Return to the original directory
cd "$start_dir" || { echo "Failed to return to $start_dir" | tee -a "$logfile"; exit 1; }
echo "Returned to directory: $(pwd)" | tee -a "$logfile"
echo "exiting run_pacupp.bash script at $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$logfile"

