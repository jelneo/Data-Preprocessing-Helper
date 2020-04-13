@echo off
cd /D "C:/Users/Jelena/Data-Preprocessing-Helper"
FOR /L %%i IN (1,1,10) DO (
  start /WAIT C:\ProgramData\Anaconda3\envs\py36\python.exe -m preprocessing.data_preprocessing_grd_texana
)