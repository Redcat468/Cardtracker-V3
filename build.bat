@echo off
chcp 65001 > nul
echo Création de l'exécutable...

pyinstaller --onefile --name "cardtracker" ^
--icon "static\images\logo.ico" ^
--add-data "templates;templates" ^
--add-data "static;static" ^
--add-data "database.py;." ^
--add-data "models.py;." ^
--add-data "routes.py;." ^
--hidden-import "flask_sqlalchemy" ^
--hidden-import "flask_login" ^
--hidden-import "sqlalchemy.ext.declarative" ^
--hidden-import "database" ^
--noconsole ^
--clean ^
app.py

echo Build terminé. Exécutable dans 'dist\'
pause