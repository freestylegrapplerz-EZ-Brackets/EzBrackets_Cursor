EZ BRACKETS - SHARE PACKAGE

This folder contains the current EZ Brackets Streamlit app files.

Main app file:
- app.py

Required dependency file:
- requirements.txt

Project info:
- README.md

Sample CSV files:
- smoothcomp_sample.csv
- universal_sample.csv

Optional helper files:
- Launch_EZ_Brackets.bat
- EZ_Brackets_Profit_Plan.txt
- EZ_Brackets_Logo.png

How to run locally:

1. Install Python.
2. Open a terminal in this folder.
3. Install requirements:
   pip install -r requirements.txt
4. Run the app:
   streamlit run app.py

What the app does:

EZ Brackets helps tournament directors upload a Smoothcomp or CSV export, find single-athlete divisions, detect same-academy bracket conflicts, rank merge recommendations, apply safety/rule presets, and export director-ready action plans.

Important:

The main source of truth is app.py. If someone is enhancing the app, they should start there.
