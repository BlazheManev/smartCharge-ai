# 🔗 SmartCharge ML & DVC Pipeline & LSTM 

This directory contains the full machine learning pipeline for SmartCharge AI. The pipeline includes automatic data fetching, preprocessing, validation, drift testing, model training, export, and deployment — all managed via DVC and automated with GitHub Actions.

---

## 🚀 Features

* ✈️ Automated data ingestion every 30 minutes
* 📊 Data validation using Great Expectations
* 🧠 Model training & evaluation with MLflow tracking
* 🧪 Trains 40+ models using LSTM (1 per EV station)
* 📲 Metadata export to MongoDB
* 🌐 HTML report uploads (drift, expectations)
* ✨ Two GitHub Actions workflows for scheduling pipelines

---

## 🧱 Stack

* **DVC** (Data Version Control)
* **Python 3.12** + **Poetry** for dependency management
* **MLflow** for model tracking
* **Great Expectations** for data validation
* **MongoDB** as metadata store
* **GitHub Actions** for automation
* 🧠 **LSTM** models used for time series prediction

---

## 🔄 Pipeline Overview

```yaml
stages:
  fetch_ev:             # Download EV availability data
  preprocess_ev:        # Clean and structure data
  validate_ev_data:     # Run Great Expectations validation
  test_ev_data:         # Drift detection report generation
  train_ev:             # Train 40+ LSTM models (one per station)
  export_and_deploy_ml_json: # Export model metadata and upload to MongoDB
  upload_reports:       # Upload drift/validation HTML to MongoDB
```

---

## 🗂️ Structure

```
.
├── workflows/                        # GitHub Actions pipelines
│   ├── fetch_ev_data.yml             # Every 30 minutes
│   └── train_ev_model.yml            # Every 6 hours
├── data/                             # DVC tracked data folder
├── gx/                               # Great Expectations setup
│   └── run_checkpoint.py
├── reports/                          # Drift and validation reports
├── public/                           # Exported JSON metadata
├── src/
│   ├── data/
│   │   ├── fetch_ev_data.py
│   │   ├── preprocess_ev_data.py
│   │   ├── test_ev_data.py
│   │   └── upload_html_to_mongo.py
│   └── model/
│       ├── train_ev.py
│       ├── export_mlflow_models.py
│       └── upload_model_json_to_mongo.py
```

---

## 🤖 GitHub Actions Workflows

### ⚡ Fast EV Data Pipeline (`fetch_ev_data.yml`)

Runs every **30 minutes**:

```yaml
dvc repro fetch_ev preprocess_ev validate_ev_data test_ev_data upload_reports
```

### 🧠 Full Model Training Pipeline (`train_ev_model.yml`)

Runs every **6 hours (09:00, 15:00, 21:00, 03:00 UTC)**:

```yaml
dvc repro --single-item train_ev
dvc repro --single-item export_and_deploy_ml_json
```

Each job includes:

* `dvc pull` to fetch latest inputs
* `dvc push` after updates
* Git commit + push with lock/status changes

---

## 📦 MLflow Model Metadata

* Extracted with: `export_mlflow_models.py`
* Outputs JSON to: `public/ml_models.json`
* Uploaded to MongoDB: `upload_model_json_to_mongo.py`

---

## 🧾 HTML Report Uploads

* Great Expectations data docs and drift reports are uploaded to Mongo:

```bash
upload_html_to_mongo.py
```

Used by backend `/reports/view/:id` and frontend admin panel.

---

## 🧪 Environment Setup

To run the pipeline successfully, ensure:

* ✅ DVC remote is configured:

```bash
dvc remote modify origin --local access_key_id YOUR_KEY
dvc remote modify origin --local secret_access_key YOUR_SECRET
```

* ✅ Add the following environment variables:

```env
MONGO_URI=mongodb+srv://...
TOMTOM_API_KEY=your_api_key
```

These can be passed via `.env` or set in GitHub Actions/Docker.

---

## 🌐 Deployment & Usage

Use `Dockerfile` to build and run this ML pipeline containerized:

```bash
docker build -t smartcharge-ml .
docker run -e MONGO_URI=... -e DAGSHUB_ACCESS_KEY_ID=... -e DAGSHUB_SECRET_ACCESS_KEY=... -e TOMTOM_API_KEY=... smartcharge-ml
```

Or run locally:

```bash
poetry install
poetry run dvc repro
```

---

## 👨‍💻 Author

Blazhe Manev

---