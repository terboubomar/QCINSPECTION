# Restaurant Quality Control Application

## Overview
The Restaurant Quality Control Application is designed to ensure the best quality control standards for restaurants, leveraging advanced technologies such as FastAPI, SQLAlchemy, Redis, Celery, OpenCV, and TensorFlow.

## Features
- Real-time monitoring of food quality
- Automated inspections using image processing
- Scalable architecture with Docker and Celery for task management
- User-friendly API with FastAPI
- Database management with SQLAlchemy
- Caching and event-driven processing using Redis

## Installation Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/terboubomar/QCINSPECTION.git
   cd QCINSPECTION
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Guide
- Run the application:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
- Visit `http://localhost:8000/docs` for API documentation.
