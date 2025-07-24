import firebase_admin
import datetime
from fastapi import FastAPI, Request, Query, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, auth, firestore
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

cred = credentials.Certificate("cerebrumal-firebase-adminsdk-fbsvc-1ed7ecd1a2.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Or ["http://localhost:8000"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def sign_in(request: Request):
    return templates.TemplateResponse("sign-in.html", {"request": request})

@app.get("/patient-list", response_class=HTMLResponse)
async def patient_list(request: Request, session_token: str = Cookie(None)):
    if not session_token:
        print("No available session found.")
        return RedirectResponse(url="/")
    patient_ref_list= db.collection("patient").stream()
    patients = []
    counter = 0
    for patient_doc in patient_ref_list:
        patient_data = patient_doc.to_dict()  # dictionary of the document fields
        if patient_data["doctor"] != session_token:
            continue; 
        counter += 1
        patients.append({
            "id": patient_doc.id,
            "order": counter,
            "name": patient_data["name"],
            "surname": patient_data["surname"]
        })
    return templates.TemplateResponse("patient-list.html", {"request": request, "patients": patients})

@app.get("/scan-mri", response_class=HTMLResponse)
async def scan(request: Request, session_token: str = Cookie(None)):
    if not session_token:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse("scan-page.html", {"request": request})

@app.get("/patient-profile/{patient_id}", response_class=HTMLResponse)
async def patient_profile(request: Request, patient_id: str, session_token: str = Cookie(None)):
    if not session_token:
        return RedirectResponse(url="/")
    patient_ref = db.collection("patient").document(patient_id)
    patient = patient_ref.get()
    if not patient.exists:
        return JSONResponse({"error": "Patient not found"}, status_code=404)
    patient_data = patient.to_dict()
    print(type(patient_data["gender"]))
    patient_data["gender"] = "Male" if patient_data["gender"] else "Female"
    return templates.TemplateResponse("patient-profile.html", {"request": request, "patient": patient_data})

@app.get("/doctor-area")
async def doctor_area(token: str = Query(...)):
    try:
        decoded = auth.verify_id_token(token, clock_skew_seconds=60)
        uid = decoded["uid"]

        doc_ref = db.collection("doctor").document(uid)
        if not doc_ref.get().exists:
            return RedirectResponse(url="/")

        response = RedirectResponse(url="/scan-mri")

        response.set_cookie(
            key="session_token",
            value=uid,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=3600*24 # 1 day
        )
        return response
    except Exception:
        return RedirectResponse(url="/")

@app.get("/doctor-info")
async def doctor_info(request: Request, session_token: str = Cookie(None)):
    if not session_token:
        print("No available session found.")
        return RedirectResponse(url="/")
    doc_ref = db.collection("doctor").document(session_token)
    doc = doc_ref.get()

    if not doc.exists:
        return JSONResponse({"error": "Doctor not found"}, status_code=404)

    doctor_data = doc.to_dict()

    created_on = doctor_data.get("created_on")
    # If created_on is DatetimeWithNanoseconds, convert it to datetime
    if isinstance(created_on, DatetimeWithNanoseconds):
        created_on = datetime.datetime.fromtimestamp(created_on.timestamp())

    response = {
        "name": doctor_data.get("name"),
        "surname": doctor_data.get("surname"),
        "institution": doctor_data.get("institution"),
        "title": doctor_data.get("title"),
        "created_on": created_on.strftime("%d/%m/%Y")
    }

    return {"message": "Fetched doctor response", "data": response}
"""
@app.get("/doctor-area")
async def doctor_area(user_id: str = Depends(verify_token)):
    # ✅ Check if user is a doctor
    doc_ref = db.collection("doctor").document(user_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=403, detail="You are not authorized")

    # ✅ Set session cookie
    return {"message": "Doctor signed in." }

    @app.get("/scan-mri", response_class=HTMLResponse)

async def scan(request: Request, session_token: str = Cookie(None)):
    if not session_token:
        return RedirectResponse(url="/")
    
    # ✅ (Optional) Double-check the session_token is a valid doctor
    doc_ref = db.collection("doctor").document(session_token)
    if not doc_ref.get().exists:
        return RedirectResponse(url="/")

    return templates.TemplateResponse("scan-page.html", {"request": request})

"""
