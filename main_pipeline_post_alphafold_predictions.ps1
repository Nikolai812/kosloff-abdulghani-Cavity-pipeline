# Base directory where the script is allowed to run
# $base_dir = "C:\Users\user\source\repos\uh-cast-p-fold"

# Get current directory as a STRING
$start_dir = (Get-Location).Path

Write-Host "Starting PostAlphaFold cavity predictions from directory: $start_dir"

# Verify the script is run from the expected directory
# if ($start_dir -ne $base_dir) {
#     Write-Warning "Exiting: this script must be run from: $base_dir"
#     Write-Error "Current directory is: $start_dir"
#     exit 1
# }

$base_dir = $start_dir

Write-Output "Starting pacupp script for JMOL"
wsl -d Ubuntu --exec /bin/bash -c "./run_pacupp.bash"

Write-Output "Pacupp over JMOL completed. Starting python 4 predictions processing"
python .\UI_SELENIUM\main.py
Write-Output "4 cavity predictions completed"


# Define directories
Write-Output ""
Write-Output ""
Write-Output "Moving to consensus and PyMol preparation"
$predictions_input = Join-Path $base_dir "UI_SELENIUM\input"
$predictions_output = Join-Path $base_dir "UI_SELENIUM\output"
$pm_input           = Join-Path $base_dir "PYMOL_SCRIPTS\PM_INPUT"

Write-Output "Defined predictions input dir $predictions_input"
Write-Output "Defined predictions output dir $predictions_output"
Write-Output "Defined pymol preparations input dir $pm_input"

Write-Host "Copying from:"
Write-Host "  $predictions_output"
Write-Host "To:"
Write-Host "  $pm_input"

robocopy $predictions_output $pm_input /E /XD *OLD* *temp* /R:0 /W:0


# Get all .pdb files in the predictions input directory
Get-ChildItem -Path $predictions_input -Filter "*.pdb" -File | ForEach-Object {
    # Get the file name without extension
    $fileNameOnly = $_.BaseName

    # Create destination subdirectory under $pm_input
    $destDir = Join-Path $pm_input $fileNameOnly
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null

    # Copy the .pdb file into its corresponding subdirectory
    Copy-Item -Path $_.FullName -Destination $destDir -Force

    Write-Host "Copied $($_.Name) → $destDir"
}


#defining the 4 predictions output directory and

Write-Output "Copying 4 predictions output to pymol input dir"


# Write-Output "Starting consensus building and pymol scripts preparation"

$pymol_scripts = Join-Path $base_dir "PYMOL_SCRIPTS"
Write-Host "Changing directory to:"
Write-Host "   $pymol_scripts"
cd $pymol_scripts

Write-Host  "Starting pm_main.py script"

python .\pm_main.py

cd  $base_dir

Write-Host  "Returned to base dir:"
Write-Host  "  $base_dir"



