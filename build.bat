@echo off
chcp 65001 > nul
echo Création de l'exécutable...

pyinstaller --onefile --name "cardtracker" ^
--icon "static\images\logo.ico" ^
--add-data "templates;templates" ^
--add-data "static;static" ^
--hidden-import "routes" ^
--hidden-import "models" ^
--hidden-import "sqlite3" ^
--hidden-import "flask_login" ^
--clean ^
--collect-all flask_sqlalchemy ^
app.py

echo Build terminé. Exécutable dans 'dist\'
pause