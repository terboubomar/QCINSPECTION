# wsgi.py
from qc_app import app

# اختياري: مسار بسيط للصحة لو ما كان موجود
@app.get("/health")
def health():
    return "ok"
