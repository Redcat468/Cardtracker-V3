@echo off
chcp 65001 > nul
echo Création de l'exécutable...

pyinstaller --onefile --name "cardtracker" ^
--icon "static\images\logo.ico" ^
--add-data "templates;templates" ^
--add-data "static;static" ^
--add-data "instance;instance" ^
--add-data "models.py;." ^
--add-data "routes.py;." ^
--add-data "database.py;." ^
--hidden-import "flask_sqlalchemy" ^
--hidden-import "flask_login" ^
--hidden-import "sqlalchemy.ext.declarative" ^
--clean ^
app.py

echo Build terminé. Exécutable dans 'dist\'
pause