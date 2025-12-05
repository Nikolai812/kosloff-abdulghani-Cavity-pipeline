Write-Output "Starting pacupp script for JMOL"

wsl -d Ubuntu --exec /bin/bash -c "./run_pacupp.bash"

Write-Output "Pacupp over JMOL completed. Starting selenium demo"
python .\UI_SELENIUM\main.py
Write-Output ".ps1 completed"


