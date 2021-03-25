
:: tool_dock is determined by the current folder name
for %%I in (.) do set tool_dock=%%~nxI
SET CLEAN_tool_dock=%tool_dock:-=_%

:: Check if modules folder exists
if not exist %UserProfile%\Documents\maya\modules mkdir %UserProfile%\Documents\maya\modules

:: Delete .mod file if it already exists
if exist %UserProfile%\Documents\maya\modules\%tool_dock%.mod del %UserProfile%\Documents\maya\modules\%tool_dock%.mod

:: Create file with contents in users maya/modules folder
(echo|set /p=+ %tool_dock% 1.0 %CD%\_install_ & echo; & echo icons: ..\%CLEAN_tool_dock%\icons)>%UserProfile%\Documents\maya\modules\%tool_dock%.mod

:: end print
echo .mod file created at %UserProfile%\Documents\maya\modules\%tool_dock%.mod


