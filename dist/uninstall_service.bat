@echo off
setlocal enabledelayedexpansion

set SERVICE_NAME=CardTracker
set NSSM_PATH=%~dp0nssm.exe

REM Vérifier les droits administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Erreur: Exécutez ce script en tant qu'Administrateur!
    pause
    exit /b 1
)

REM Vérifier la présence de nssm.exe
if not exist "%NSSM_PATH%" (
    echo Erreur: nssm.exe introuvable dans ce dossier!
    echo Placez nssm.exe ici: %~dp0
    pause
    exit /b 1
)

REM Vérifier l'existence du service
echo Vérification du service %SERVICE_NAME%...
"%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
if %errorlevel% neq 0 (
    echo Le service %SERVICE_NAME% n'existe pas.
    pause
    exit /b 1
)

REM Arrêt du service
echo Arrêt du service...
"%NSSM_PATH%" stop %SERVICE_NAME% confirm

REM Suppression du service
echo Suppression du service...
"%NSSM_PATH%" remove %SERVICE_NAME% confirm

REM Vérification finale avec boucle
:verification
echo Vérification de la suppression...
timeout /t 1 >nul
"%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo Le service existe toujours, nouvelle tentative...
    goto verification
)

REM Contrôle via SC
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo ERREUR: La suppression a échoué!
    pause
    exit /b 1
)

echo Service supprimé avec succès!
sc query %SERVICE_NAME% 2>&1 | findstr "nom spécifié" && echo Confirmation: Service introuvable dans le gestionnaire de services

pause