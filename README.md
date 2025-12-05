# Trading Dashboard
1
Ein modernes Web-basiertes Trading Dashboard, das die KITradingModel API nutzt und externe Marktdaten-APIs integriert.

## Features

- **KI-gestützte Analyse**: Integration mit KITradingModel für Trading-Empfehlungen und NHITS-Preisprognosen
- **Multi-Market Support**: Kryptowährungen, Forex und Aktien
- **Echtzeit-Daten**: Live-Marktdaten von CoinGecko, Binance und Alpha Vantage
- **News-Aggregation**: Markt-relevante Nachrichten mit Sentiment-Analyse
- **Modernes UI**: Vue 3 + TailwindCSS Dark-Mode Dashboard

## Architektur

```
TradingDashboard/
├── backend/                 # FastAPI Backend
│   ├── src/
│   │   ├── api/            # API Routes
│   │   ├── services/       # External API Services
│   │   ├── models/         # Pydantic Models
│   │   └── config/         # Configuration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   │   ├── views/         # Page Components
│   │   ├── components/    # UI Components
│   │   ├── services/      # API Client
│   │   └── stores/        # Pinia Stores
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Externe APIs

| API | Zweck | Auth |
|-----|-------|------|
| KITradingModel | KI-Analyse & Prognosen | Lokal (Port 3011) |
| CoinGecko | Krypto-Marktdaten | Keine (Free) |
| Binance | Echtzeit-Ticker & Orderbook | Optional API Key |
| Alpha Vantage | Aktien & Forex | Free Key (demo) |
| CryptoCompare | News | Keine (Free) |

## Installation

### Voraussetzungen

- Python 3.11+
- Node.js 20+
- KITradingModel läuft auf Port 3011

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env bearbeiten falls nötig
python run.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
# Alles starten
docker-compose up -d

# Nur Backend
docker-compose up -d backend

# Logs anzeigen
docker-compose logs -f
```

## Konfiguration

### Backend (.env)

```env
# KITradingModel
KITRADING_API_URL=http://localhost:3011/api/v1
KITRADING_TIMEOUT=120

# External APIs
ALPHA_VANTAGE_API_KEY=demo
BINANCE_API_KEY=          # Optional
NEWS_API_KEY=             # Optional

# Server
HOST=0.0.0.0
PORT=3010
```

## API Endpoints

### Dashboard
- `GET /api/v1/health` - System Health Check
- `GET /api/v1/dashboard` - Aggregierte Dashboard-Daten

### KITradingModel Integration
- `GET /api/v1/ki/symbols` - Verfügbare Symbole
- `GET /api/v1/ki/recommendation/{symbol}` - Trading-Empfehlung
- `POST /api/v1/ki/analyze` - Vollständige Analyse
- `GET /api/v1/ki/forecast/{symbol}` - NHITS Preisprognose
- `GET /api/v1/ki/strategies` - Trading-Strategien

### Crypto Markets
- `GET /api/v1/crypto/markets` - Top Kryptowährungen
- `GET /api/v1/crypto/{coin}/ohlc` - OHLC Candlestick-Daten
- `GET /api/v1/binance/ticker` - Binance Live-Ticker
- `GET /api/v1/binance/orderbook/{symbol}` - Orderbook

### Stocks & Forex
- `GET /api/v1/stocks/quote/{symbol}` - Aktien-Kurs
- `GET /api/v1/forex/rate` - Wechselkurse

### News
- `GET /api/v1/news/crypto` - Krypto-News
- `GET /api/v1/news/combined` - Alle Markt-News

## Frontend Views

| Route | Beschreibung |
|-------|--------------|
| `/` | Dashboard mit Watchlist, Quick Analysis, News |
| `/analysis` | KI-Analyse mit LLM-Option |
| `/forecast` | NHITS Preisprognosen mit Chart |
| `/markets` | Marktübersicht (Crypto, Binance, Forex, Stocks) |
| `/news` | News-Feed mit Sentiment-Analyse |
| `/settings` | System-Status und Konfiguration |

## Entwicklung

### Backend Development
```bash
cd backend
uvicorn src.main:app --reload --port 3010
```

### Frontend Development
```bash
cd frontend
npm run dev  # Port 5173 mit API Proxy
```

### Build für Production
```bash
cd frontend
npm run build  # Output in dist/
```

## Technologie-Stack

### Backend
- FastAPI 0.104+
- Python 3.11
- httpx (Async HTTP Client)
- Pydantic 2.x
- cachetools (In-Memory Cache)

### Frontend
- Vue 3.4 (Composition API)
- Vite 5
- TailwindCSS 3.4
- Pinia (State Management)
- Vue Router 4
- Axios

### Deployment
- Docker & Docker Compose
- Nginx (Frontend)
- Uvicorn (Backend)

## Lizenz

MIT
