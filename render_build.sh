#!/usr/bin/env bash
set -e

# 1) ثبّت المكتبات
pip install -r requirements.txt

# 2) احذف قاعدة البيانات القديمة إن وُجدت
rm -f qc_app.db

# 3) أنشئ الجداول وعبّي بيانات أولية
python -c "from qc_app import app, setup_database; setup_database(app)"
