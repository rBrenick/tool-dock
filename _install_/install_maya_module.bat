
:: dcc_toolbox is determined by the current folder name
for %%I in (.) do set dcc_toolbox=%%~nxI
SET CLEAN_dcc_toolbox=%dcc_toolbox:-=_%

:: Check if modules folder exists
if not exist %UserProfile%\Documents\maya\modules mkdir %UserProfile%\Documents\maya\modules

:: Delete .mod file if it already exists
if exist %UserProfile%\Documents\maya\modules\%dcc_toolbox%.mod del %UserProfile%\Documents\maya\modules\%dcc_toolbox%.mod

:: Create file with contents in users maya/modules folder
(echo|set /p=+ %dcc_toolbox% 1.0 %CD%\_install_ & echo; & echo icons: ..\%CLEAN_dcc_toolbox%\icons)>%UserProfile%\Documents\maya\modules\%dcc_toolbox%.mod

:: end print
echo .mod file created at %UserProfile%\Documents\maya\modules\%dcc_toolbox%.mod


