::   Copyright 2013 by MATOBA Akihiro;  matobaa /at/ gmail.com
::
::   Licensed under the Apache License, Version 2.0 (the "License");
::   you may not use this file except in compliance with the License.
::   You may obtain a copy of the License at
::
::       http://www.apache.org/licenses/LICENSE-2.0
::
::   Unless required by applicable law or agreed to in writing, software
::   distributed under the License is distributed on an "AS IS" BASIS,
::   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
::   See the License for the specific language governing permissions and
::   limitations under the License.

:: this script is distributed at
::  http://subversion.assembla.com/svn/matobaa/trunk/svnhooks
::  http://trac.assembla.com/matobaa/wiki/SvnHooks

@echo off
setlocal
set REPOS=%1
set REV=%2
set USER=%3
set PROPNAME=%4
set ACTION=%5

:MKTMP
set OLDLOG=%RANDOM%
IF EXIST %OLDLOG% GOTO :MKTMP

:: enable below line to modify/delete oldlog
:: if x%PROPNAME%==xoldlog ( exit 0 )

if x%ACTION%==xM if x%PROPNAME%==xsvn:log (
(
echo ::: log was modified by %USER% on %DATE%T%TIME:~0,8% :::
echo ::: BEFORE:
svnlook log %REPOS% -r %REV%
svnlook propget --revprop %REPOS% -r %REV% oldlog 1>NUL 2>NUL && for /F "usebackq tokens=*" %%i in (`svnlook propget --revprop %REPOS% -r %REV% oldlog`) do (echo %%i)
) > %OLDLOG%
svnadmin setrevprop %REPOS% -r %REV% oldlog %OLDLOG% 
del %OLDLOG%

exit 0
)

echo "Changing revision properties other than svn:log is prohibited" >&2
exit 1
