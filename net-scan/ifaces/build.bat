@Echo off

cd /d %~dp0

IF EXIST build ( rmdir build /s /q )
IF EXIST dist ( rmdir dist /s /q )
IF EXIST ifaces.spec ( del ifaces.spec )

pyinstaller --onefile --name ifaces ifaces.py
