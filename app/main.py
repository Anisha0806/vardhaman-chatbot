from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

# --------------------------------------------------
# 1. FastAPI App
# --------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 2. Load doctors.json (SOURCE OF TRUTH)
# Folder structure:
# VARDHMAN/
# ├── app/main.py
# ├── data/doctors.json
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTORS_PATH = os.path.join(BASE_DIR, "..", "data", "doctors.json")

with open(DOCTORS_PATH, "r", encoding="utf-8") as f:
    DOCTORS = json.load(f)

# --------------------------------------------------
# 3. Detect User Language / Dialect
# --------------------------------------------------
def detect_language(text: str) -> str:
    text = text.lower()

    hindi_words = ["डॉक्टर", "दर्द", "बुखार", "घुटने", "कान", "नाक"]
    punjabi_words = ["ਡਾਕਟਰ", "ਦਰਦ", "ਘੁੱਟਨੇ", "ਕਾਨ", "ਨੱਕ"]

    if any(word in text for word in punjabi_words):
        return "pa"
    if any(word in text for word in hindi_words):
        return "hi"
    return "en"

# --------------------------------------------------
# 4. Normalize Query (Hinglish + Short Forms)
# --------------------------------------------------
def normalize(text: str) -> str:
    text = text.lower()

    synonyms = {
        "ent": "ear nose throat ent",
        "ortho": "orthopedics bone joint",
        "haddi": "bone",
        "kan": "ear",
        "kaan": "ear",
        "naak": "nose",
        "gala": "throat",
        "daant": "dental",
        "dant": "dental",
        "skin": "dermatology",
        "heart": "cardiology"
    }

    for key, value in synonyms.items():
        if key in text:
            text += " " + value

    return text

# --------------------------------------------------
# 5. Find Matching Doctors (NO RAG)
# --------------------------------------------------
def find_doctors(query: str):
    q = normalize(query)
    results = []

    for doc in DOCTORS:
        dept = doc.get("specialization", "").lower()
        symptoms = " ".join(doc.get("symptoms", [])).lower()

        # Department match
        if dept in q:
            results.append(doc)
            continue

        # Symptom keyword match
        for word in q.split():
            if word in symptoms:
                results.append(doc)
                break

    return results

# --------------------------------------------------
# 6. Format Response in Same Dialect
# --------------------------------------------------
def format_response(doc, lang):
    if lang == "hi":
        return (
            f"डॉक्टर का नाम: {doc['name']}\n"
            f"विभाग: {doc['specialization']}\n"
            f"ओपीडी: {doc['opd']}\n"
            f"समय: {doc['timing']}"
        )

    if lang == "pa":
        return (
            f"ਡਾਕਟਰ ਦਾ ਨਾਮ: {doc['name']}\n"
            f"ਵਿਭਾਗ: {doc['specialization']}\n"
            f"OPD: {doc['opd']}\n"
            f"ਸਮਾਂ: {doc['timing']}"
        )

    return (
        f"Doctor Name: {doc['name']}\n"
        f"Department: {doc['specialization']}\n"
        f"OPD: {doc['opd']}\n"
        f"Timing: {doc['timing']}"
    )

# --------------------------------------------------
# 7. Chat API
# --------------------------------------------------
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    lang = detect_language(request.message)
    doctors = find_doctors(request.message)

    if not doctors:
        fallback = {
            "en": "I couldn’t find a matching doctor. Please describe your symptoms.",
            "hi": "मुझे उपयुक्त डॉक्टर नहीं मिला। कृपया अपने लक्षण बताएं।",
            "pa": "ਮੈਨੂੰ ਢੁੱਕਵਾਂ ਡਾਕਟਰ ਨਹੀਂ ਮਿਲਿਆ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਲੱਛਣ ਦੱਸੋ।"
        }
        return {"response": fallback[lang]}

    response = format_response(doctors[0], lang)
    return {"response": response}

# --------------------------------------------------
# 8. Run Server
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

   # uvicorn.run(app, host="127.0.0.1", port=8000)
