#!/usr/bin/env bash
# Install dependencies
pip install -r requirements.txt

# Run database setup
python -c "from qc_app import app, setup_database; setup_database(app)"
