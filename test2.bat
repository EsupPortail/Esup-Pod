@echo off
for /f "delims=" %%a in (.env.dev) do call set %%a

