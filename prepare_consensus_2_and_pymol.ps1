# Get current directory as a STRING
$start_dir = (Get-Location).Path

Write-Host "Starting consensus and PyMol scripts manipulations from directory: $start_dir"

$base_dir=$start_dir


#################################################################
# Write-Output "Starting consensus building and pymol scripts preparation"

$pymol_scripts = Join-Path $base_dir "PYMOL_SCRIPTS"
Write-Host "Changing directory to:"
Write-Host "   $pymol_scripts"
cd $pymol_scripts

Write-Host  "Starting pm_main.py script with the 2nd consensus method"

python .\pm_main.py  --interactive --consensus-method=2
# If you want to skip user input, (configure everything in yaml of by default)
# python .\pm_main.py

cd  $base_dir

Write-Host  "Returned to base dir:"
Write-Host  "  $base_dir"

