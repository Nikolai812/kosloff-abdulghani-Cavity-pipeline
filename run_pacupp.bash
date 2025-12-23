#!/bin/bash

# Save the current working directory
start_dir=$(pwd)
echo "Starting directory: $start_dir"

#CONFIGURATION: Pacupp script and output directories
pacupp_dir="/mnt/c/Users/user/Ubuntu/app/pacupp/Fill_Cavities_PACUPP"
pacupp_spreadsheet_lists_dir="$pacupp_dir/output-files/spreadsheet-ready-lining-lists"

# CONFIGURATION: PDB files input directory, pacupp python feed up directory
# (Normal place- inside the uh-cast-p-fold project.)
# pipeline_base="/mnt/c/Users/user/source/repos/uh-cast-p-fold"
pipeline_base=$start_dir
input_dir="$pipeline_base/UI_SELENIUM/input"
pacupp_python_feedup="$pipeline_base/UI_SELENIUM/pacupp_python_feedup"
# (input_dir="/mnt/c/Users/user/Ubuntu/INPUT_PDB")

echo "!!!!!!!!!!! DIRECTORY CONFIGURATION:"
echo "pacupp_dir=$pacupp_dir"
echo "pacupp_spreadsheet_lists_dir=$pacupp_spreadsheet_lists_dir"
echo "pipeline_base=$pipeline_base"
echo "input_dir=$input_dir"
echo "pacupp_python_feedup=$pacupp_python_feedup"
echo "!!!!!!!!!!!"
echo "   "

# List all .pdb files in the input directory
echo "Listing .pdb files in $input_dir:"
ls "$input_dir"/*.pdb 2>/dev/null || echo "No .pdb files found in $input_dir"

# Gather all .pdb files into an array
pdb_input_files=("$input_dir"/*.pdb)

# Check if any .pdb files were found
if [ ${#pdb_input_files[@]} -eq 0 ]; then
    echo "No .pdb files found in $input_dir"
    exit 1
fi

# Going tp pacupp directory
cd "$pacupp_dir" || { echo "Failed to go to $pacupp_dir"; exit 1; }
echo "we are inside: $(pwd)"



# Loop through each .pdb file
for current_pdb in "${pdb_input_files[@]}"; do
    echo "Processing $current_pdb"
    
    # Replace the second line in steps.spt with the new load command
    sed -i "2s|^.*|load $current_pdb;|" steps.spt

    # Echo the updated line for confirmation
    echo "Updated steps.spt: load $current_pdb;"

    # Run the Java command in the background
    java -jar 1-Jmol.jar -g 1000x1000 steps.spt &

    # Store the PID of the Java process
    JAVA_PID=$!
    echo "java_pid=$JAVA_PID"

    # Wait for a specified delay (in seconds)
    DELAY=90  # Change this value to your desired delay
    sleep $DELAY

    # Kill the Java process
    kill $JAVA_PID
    echo "killing java process: $JAVA_PID"

    DELAY=2
done


# Exit the script 
echo "Copying pacupp spreadsheet lists from  $pacupp_spreadsheet_lists_dir to $pacupp_python_feedup (with force overwrite)"
mkdir -p "$pacupp_python_feedup"
cp -f "$pacupp_spreadsheet_lists_dir"/*.txt "$pacupp_python_feedup"/



# Return to the original directory
cd "$start_dir" || { echo "Failed to return to $start_dir"; exit 1; }
echo "Returned to directory: $(pwd)"
echo "exiting run_pacupp.bash script"

