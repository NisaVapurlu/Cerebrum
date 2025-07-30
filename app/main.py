import firebase_admin
import datetime, traceback, os
from fastapi import FastAPI, Request, Query, Cookie, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, auth, firestore
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import numpy as np

if not firebase_admin._apps:
    cred = credentials.Certificate("cerebrumal-firebase-adminsdk-fbsvc-82c52971a9.json")
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

UPLOAD_DIR = ""
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

@app.api_route("/scan-mri", methods=["GET", "POST"], response_class=HTMLResponse)
async def scan(request: Request, session_token: str = Cookie(None), file: UploadFile = File(None)):
    if request.method == "GET":
        return templates.TemplateResponse("scan-page.html", {"request": request})

    elif request.method == "POST":
        if not file:
            return JSONResponse({"error": "No file uploaded"}, status_code=400)

        print("Filename:", file.filename)

        # Kök dizine göre statik klasörün altına kaydetmek istiyorsan:
        base_dir = os.path.dirname(__file__)  # current file's directory
        upload_dir = os.path.join(base_dir, "static", "upload")
        os.makedirs(upload_dir, exist_ok=True)  # klasör yoksa oluştur

        file_location = os.path.join(upload_dir, file.filename)

        # Dosya içeriğini oku (sadece 1 kez!)
        contents = await file.read()

        with open(file_location, "wb") as f:
            f.write(contents)

        base_dir = os.path.dirname(__file__)
        model_path = os.path.join(base_dir, "model.h5")

        model = load_model(model_path)

        class_names = ['glioma_tumor', 'meningioma_tumor', 'no_tumor', 'pituitary_tumor']

        img = Image.open(file_location).convert('RGB')

        img_resized = img.resize((224, 224))

        img_array = image.img_to_array(img_resized)
        img_array = img_array / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        pred_probs = model.predict(img_array)
        pred_index = np.argmax(pred_probs)
        pred_label = class_names[pred_index]
        confidence = pred_probs[0][pred_index]
        print("Prediction Rate:", confidence, "Prediction Label:", pred_label)

        return JSONResponse({"message": f"Image saved to {file_location}"})
    

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
    except Exception as e:
        print("Exception in /doctor-area:")
        traceback.print_exc()
        return RedirectResponse(url="/")

@app.get("/doctor-info")
async def doctor_info(request: Request, session_token: str = Cookie(None)):
    if not session_token:
        print("No available session found.")
        return RedirectResponse(url="/")
    doc_ref = db.collection("doctor").document(session_token)
    patients = db.collection("patient").stream()
    counter = 0
    for patient in patients:
        patient_data = patient.to_dict()
        if patient_data["doctor"] == session_token:
            counter += 1
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
        "created_on": created_on.strftime("%d/%m/%Y"),
        "patient_count": counter
    }

    return {"message": "Fetched doctor response", "data": response}

@app.get("/result/{result_id}")
async def result_info(request: Request, result_id: str, session_token: str = Cookie(None)):
    if not session_token:
        print("No available session found.")
        return RedirectResponse(url="/")
    
    result_ref = db.collection("results").document(result_id)
    res = result_ref.get()

    if not res.exists:
        return JSONResponse({"error": "Doctor not found"}, status_code=404)

    result_data = res.to_dict()
    print(result_data)
    # Take the patient
    pat_ref = db.collection("patient").document(result_data["patient_id"])
    pat = pat_ref.get()
    patient_data = pat.to_dict()

    scanned_on = result_data.get("scanned_on")
    # If created_on is DatetimeWithNanoseconds, convert it to datetime
    if isinstance(scanned_on, DatetimeWithNanoseconds):
        scanned_on = datetime.datetime.fromtimestamp(scanned_on.timestamp())

    response = {
        "title": result_data.get("name"),
        "patient_name":  patient_data.get("name") +" "+patient_data.get("surname"),
        "tumor_type": result_data.get("tumor_type"),
        "pred_rate": result_data.get("pred_rate"),
        "description": result_data.get("description"),
        "scanned_on": scanned_on.strftime("%d/%m/%Y %H:%M:%S")
    }

    return {"message": "Fetched doctor response", "data": response}

@app.get("/patient-profile/{patient_id}", response_class=HTMLResponse)
async def patient_profile(request: Request, patient_id: str, session_token: str = Cookie(None)):
    if not session_token:
        return RedirectResponse(url="/")
    patient_ref = db.collection("patient").document(patient_id)
    patient = patient_ref.get()
    if not patient.exists:
        return JSONResponse({"error": "Patient not found"}, status_code=404)
    patient_data = patient.to_dict()
    patient_data["gender"] = "Male" if patient_data["gender"] else "Female"
    all_results = db.collection("results").stream()
    results = []
    for result_doc in all_results:
        result_data = result_doc.to_dict()
        if result_data["patient_id"] != patient_id:
            continue
        scanned_on = result_data.get("scanned_on")
        if isinstance(scanned_on, DatetimeWithNanoseconds):
            scanned_on = datetime.datetime.fromtimestamp(scanned_on.timestamp())

        results.append({
            "id": result_doc.id,
            "name": result_data["name"],
            "tumor_type": result_data["tumor_type"],
            "scanned_on": scanned_on.strftime("%d/%m/%Y %H:%M:%S") if scanned_on else None
        })

    results.sort(key=lambda r: r["scanned_on"], reverse=True)
    for i in range(0, len(results)):
        results[i]["order"] = i + 1
    print(results)

    return templates.TemplateResponse("patient-profile.html", {"request": request, "patient": patient_data, "results": results})
