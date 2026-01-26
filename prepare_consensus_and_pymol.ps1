# Get current directory as a STRING
$start_dir = (Get-Location).Path

Write-Host "Starting consensus and PyMol scripts manipulations from directory: $start_dir"

$base_dir=$start_dir

# Define directories
$predictions_input = Join-Path $base_dir "UI_SELENIUM\input"
$predictions_output = Join-Path $base_dir "UI_SELENIUM\output"
$pm_input           = Join-Path $base_dir "PYMOL_SCRIPTS\PM_INPUT"

# was in the earlier versions:
# robocopy $predictions_output $pm_input /E /XD *OLD* *temp* /R:0 /W:0
#

#################################################################
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

