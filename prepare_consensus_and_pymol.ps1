# Base directory where the script is allowed to run
$base_dir = "C:\Users\user\source\repos\uh-cast-p-fold"

# Get current directory as a STRING
$start_dir = (Get-Location).Path

Write-Host "Starting consensus and PyMol scripts manipulations from directory: $start_dir"

# Verify the script is run from the expected directory
if ($start_dir -ne $base_dir) {
    Write-Warning "Exiting: this script must be run from: $base_dir"
    Write-Error "Current directory is: $start_dir"
    exit 1
}

# Define directories
$predictions_output = Join-Path $base_dir "UI_SELENIUM\output"
$pm_input           = Join-Path $base_dir "PYMOL_SCRIPTS\PM_INPUT"

Write-Host "Copying from:"
Write-Host "  $predictions_output"
Write-Host "To:"
Write-Host "  $pm_input"

robocopy $predictions_output $pm_input /E /XD *OLD* *temp* /R:0 /W:0

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

