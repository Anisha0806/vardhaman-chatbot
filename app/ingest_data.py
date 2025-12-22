import chromadb
import pandas as pd
import json
import os

# 1. Force Absolute Paths
# This ensures the DB is created exactly in the 'app/vardhaman_db' folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vardhaman_db")
JSON_PATH = os.path.join(BASE_DIR, "..", "data", "doctors.json")
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "chatbot_training_data.csv")

# 2. Setup Database
client = chromadb.PersistentClient(path=DB_PATH)
# Delete old collection if it exists to start fresh
try:
    client.delete_collection(name="hospital_data")
except:
    pass
collection = client.create_collection(name="hospital_data")

# 3. Process CSV Training Data
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    for i, row in df.iterrows():
        collection.add(
            documents=[str(row['phrase'])],
            metadatas=[{"intent": row['intent'], "type": "faq"}],
            ids=[f"csv_{i}"]
        )
    print(f"✅ Loaded {len(df)} CSV phrases.")
else:
    print(f"❌ CSV NOT FOUND at: {CSV_PATH}")

# 4. Process Doctor JSON Data
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        doctors = json.load(f)
    
    for i, doc in enumerate(doctors):
        # Using .get() prevents the 'KeyError' crash
        name = doc.get('name', 'N/A')
        spec = doc.get('specialization', 'General')
        opd = doc.get('opd', 'Consult Reception')
        time = doc.get('timing', 'Contact Hospital')
        symptoms = ", ".join(doc.get('symptoms', []))
        
        combined_info = f"Doctor: {name}. Dept: {spec}. Location: {opd}. Timing: {time}. Symptoms: {symptoms}"
        
        collection.add(
            documents=[combined_info],
            metadatas={"room": opd, "doctor": name, "type": "doctor_info"},
            ids=[f"doc_{i}"]
        )
    print(f"✅ Loaded {len(doctors)} Doctors from JSON.")
else:
    print(f"❌ JSON NOT FOUND at: {JSON_PATH}")

# 5. Final Verification
total_count = collection.count()
print(f"\n--- Final Status ---")
print(f"Database Entries: {total_count}")
if total_count > 0:
    print(f"SUCCESS: 'vardhaman_db' is now populated at {DB_PATH}")
else:
    print(f"FAILED: Database is still empty.")