import os
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from spin_engine import get_profile, update_profile, submit_measure
from excel_handler import generate_excel_template, parse_excel_file

app = FastAPI(title="SPIN Maatregel Aanvrager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

@app.get("/api/profile")
def api_get_profile():
    return get_profile()

@app.post("/api/profile")
def api_save_profile(data: dict):
    updated = update_profile(data)
    return {"status": "success", "profile": updated}

@app.post("/api/create-single")
def api_create_single(data: dict):
    is_draft = data.get("isDraft", True)
    if isinstance(is_draft, str):
        is_draft = is_draft.lower() not in ["false", "0", "nee", "definitief"]

    res = submit_measure(data, is_draft=is_draft)
    return res

@app.get("/api/download-template")
def api_download_template():
    profile = get_profile()
    temp_dir = tempfile.mkdtemp()
    filepath = os.path.join(temp_dir, "SPIN_Sjabloon_Aanvragen.xlsx")
    generate_excel_template(filepath, profile=profile)
    return FileResponse(filepath, filename="SPIN_Sjabloon_Aanvragen.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/import-excel")
async def api_import_excel(file: UploadFile = File(...), is_draft: bool = Form(True)):
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    measures = parse_excel_file(temp_file_path)
    
    results = []
    for idx, m in enumerate(measures, 1):
        # Determine draft per row or global toggle
        row_draft = m.get("isDraft")
        if row_draft is not None:
            if isinstance(row_draft, str):
                draft_flag = row_draft.lower() not in ["false", "0", "nee", "definitief"]
            else:
                draft_flag = bool(row_draft)
        else:
            draft_flag = is_draft

        res = submit_measure(m, is_draft=draft_flag)
        results.append({
            "row": idx + 2,
            "success": res.get("success"),
            "message": res.get("message"),
            "road": m.get("location.fromRoadNumber"),
            "start": m.get("start"),
            "end": m.get("end")
        })

    return {"total": len(measures), "results": results}

# Mount static files for UI
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 6000))
    print(f"Starting SPIN Aanvrager server on http://localhost:{port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)
