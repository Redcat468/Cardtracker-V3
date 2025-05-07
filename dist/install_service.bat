@echo off
setlocal enabledelayedexpansion

set SERVICE_NAME=CardTracker
set EXE_PATH=%~dp0cardtracker.exe
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
    echo Téléchargez-le depuis https://nssm.cc et placez-le ici:
    echo %~dp0
    pause
    exit /b 1
)

REM Vérifier l'existence du service
echo Vérification des services existants...
"%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo Suppression de l'ancien service...
    "%NSSM_PATH%" stop %SERVICE_NAME% confirm
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm
    
    REM Attendre la suppression complète
    :check_removal
    "%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
    if %errorlevel% equ 0 (
        timeout /t 1 >nul
        goto check_removal
    )
)

REM Installer le nouveau service
echo Création du nouveau service...
"%NSSM_PATH%" install %SERVICE_NAME% "%EXE_PATH%"
if %errorlevel% neq 0 (
    echo ERREUR: Échec de l'installation du service
    pause
    exit /b 1
)

REM Configurer le service
echo Configuration du service...
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory %~dp0
"%NSSM_PATH%" set %SERVICE_NAME% Description "Service de suivi de cartes"

REM Vérifier l'installation
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Le service n'a pas été créé correctement
    pause
    exit /b 1
)

REM Démarrer le service
echo Démarrage du service...
"%NSSM_PATH%" start %SERVICE_NAME%

timeout /t 2 >nul

REM Vérifier le statut
"%NSSM_PATH%" status %SERVICE_NAME%
if %errorlevel% neq 0 (
    echo ERREUR: Le service ne répond pas
    pause
    exit /b 1
)

echo Opération réussie! Vérification finale:
sc query %SERVICE_NAME% | findstr "STATE"
pause