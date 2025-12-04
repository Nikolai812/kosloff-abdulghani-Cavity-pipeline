Write-Output "Starting pacupp script for JMOL"

wsl -d Ubuntu --exec /bin/bash -c "./run_pacupp.bash"

Write-Output "Pacupp completed. Starting selenium demo"
python .\UI_SELENIUM\selenium_test.py
Write-Output ".ps1 completed"


