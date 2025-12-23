Write-Output "This is just a test for selenium web driver."

$start_dir = (Get-Location).Path

Write-Host "Starting selenium demo from directory: $start_dir"

python .\UI_SELENIUM\selenium_test.py
Write-Output "Testing selenium .ps1 completed"


