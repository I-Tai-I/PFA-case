# PFA-case
My solution for a case in the hiring process of the PFA Softwaredeveloper role


Run locally in virtual environment:
´´´ bash
set GOOGLE_API_KEY=YOUR_KEY_HERE
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn routes:app --reload
´´´

Access the swagger documentation at "http://127.0.0.1:8000/docs".