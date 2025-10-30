@echo off
REM Test launcher - should only create ONE log entry
cd /d "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
echo [%date% %time%] TEST: Launch attempt >> "Logs\launch.log"
start "" "C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\pythonw.exe" "RAG_Control_Panel.py"
exit
