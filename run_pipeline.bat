@echo off
cd /d "c:\Users\Surbhi\Documents\sentiment"
call sentiment_env\Scripts\activate.bat
python pipeline.py --topic "Artificial Intelligence" --limit 200
