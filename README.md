# 🌾 AI Agriculture Assistant

A mobile-first agriculture platform that helps farmers detect plant diseases, receive treatment recommendations, get fertilizer suggestions, weather alerts, and market prices.

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Flutter (Android/iOS) |
| **Backend** | Python FastAPI |
| **AI/ML** | TensorFlow, Keras, MobileNetV2 |
| **Database** | PostgreSQL |
| **Auth** | JWT (JSON Web Tokens) |
| **Weather** | OpenWeatherMap API |
| **Containerization** | Docker & Docker Compose |

## 📁 Project Structure

```
AGENTAI/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── routes/          # API Endpoints
│   │   ├── models/          # SQLAlchemy Models
│   │   ├── schemas/         # Pydantic Schemas
│   │   ├── services/        # Business Logic
│   │   ├── database/        # DB Configuration
│   │   └── main.py          # App Entry Point
│   ├── Dockerfile
│   └── requirements.txt
├── ai-model/                # ML Model Training & Inference
│   ├── train.py
│   ├── predict.py
│   ├── disease_info.json
│   ├── dataset/             # PlantVillage Dataset (download separately)
│   └── saved_model/         # Trained model output
├── frontend/                # Flutter Mobile App
│   ├── lib/
│   │   ├── screens/
│   │   ├── services/
│   │   ├── models/
│   │   └── main.dart
│   └── pubspec.yaml
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🏁 Getting Started

### Prerequisites

- Python 3.10+
- Flutter SDK 3.x
- Docker & Docker Compose
- An OpenWeatherMap API Key (free tier)

### 1. Clone & Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values (API keys, secrets)
```

### 2. Start the Database

```bash
docker-compose up -d db
```

### 3. Run the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs will be available at: `http://localhost:8000/docs`

### 4. Train the AI Model (Optional)

```bash
cd ai-model
pip install -r requirements.txt
# Download the PlantVillage dataset into ai-model/dataset/
python train.py
```

### 5. Run the Flutter App

```bash
cd frontend
flutter pub get
flutter run
```

## 📡 API Endpoints (MVP)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new farmer |
| `POST` | `/auth/login` | Login and get JWT token |
| `GET` | `/auth/profile` | Get current farmer profile |
| `PUT` | `/auth/profile` | Update farmer profile |
| `POST` | `/predict` | Upload leaf image for disease detection |
| `GET` | `/predict/history` | Get prediction history |
| `GET` | `/recommendation/{disease}` | Get treatment recommendations |
| `GET` | `/weather?city={city}` | Get weather data and alerts |

## 📄 License

This project is for educational purposes.
