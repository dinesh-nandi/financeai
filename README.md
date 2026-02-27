# FinanceAI - Django Backend

AI-Powered Finance Education & Investment Intelligence Platform - Django Backend

## Features

- **User Authentication** - JWT-based auth, Web3 wallet (MetaMask), and **QR login** via WalletConnect
- **Learning Module** - Topics, quizzes, and progress tracking
- **Stock Prediction** - AI-powered predictions with confidence scores
- **News Intelligence** - Sentiment analysis and market correlation
- **Portfolio Analyzer** - Holdings tracking with analytics
- **AI Strategy Advisor** - Chat-based financial advice

## Project Structure

```
finance_ai/
├── finance_ai/          # Main Django project
│   ├── settings.py      # Django settings
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI config
│
├── users/               # User authentication & profiles
├── learning/            # Learning topics & quizzes
├── prediction/          # Stock predictions
├── news/                # News & sentiment analysis
├── portfolio/           # Portfolio management
├── advisor/             # AI chat advisor
│
├── templates/           # HTML templates
├── static/              # CSS & JS files
├── manage.py            # Django management
└── requirements.txt     # Python dependencies
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd finance_ai
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your settings
```

**QR login (WalletConnect):** To enable "Sign in with QR code" (scan with your phone wallet), add a free project ID from [WalletConnect Cloud](https://cloud.walletconnect.com/) to `.env`:

```
WALLETCONNECT_PROJECT_ID=your_project_id_here
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Load Initial Data (Optional)

```bash
python manage.py shell
```

Then run:
```python
from prediction.models import Stock

# Create sample stocks
stocks = [
    {'symbol': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology', 'current_price': 182.50},
    {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Technology', 'current_price': 215.30},
    {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology', 'current_price': 141.20},
    {'symbol': 'MSFT', 'name': 'Microsoft Corp.', 'sector': 'Technology', 'current_price': 312.45},
    {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer', 'current_price': 145.80},
    {'symbol': 'INFY', 'name': 'Infosys Ltd.', 'sector': 'Technology', 'current_price': 19.85},
]

for s in stocks:
    Stock.objects.get_or_create(symbol=s['symbol'], defaults=s)

exit()
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Access the application at: http://127.0.0.1:8000/

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `GET /api/auth/profile/` - Get user profile
- `POST /api/auth/logout/` - User logout

### Dashboard
- `GET /api/dashboard/summary/` - Dashboard summary data

### Learning
- `GET /api/learning/topics/` - List learning topics
- `GET /api/learning/topics/<id>/` - Topic details
- `POST /api/learning/submit-quiz/` - Submit quiz answers
- `GET /api/learning/progress/` - User progress
- `GET /api/learning/stats/` - Learning statistics

### Prediction
- `GET /api/prediction/stocks/` - List available stocks
- `GET /api/prediction/stocks/<symbol>/` - Stock details
- `POST /api/prediction/make/` - Make a prediction
- `GET /api/prediction/history/` - Prediction history
- `GET /api/prediction/stats/` - Prediction statistics

### News
- `GET /api/news/latest/` - Latest news
- `GET /api/news/sentiment-summary/` - Sentiment summary
- `GET /api/news/sentiment-trend/` - Sentiment trend
- `GET /api/news/correlation/` - News-market correlation

### Portfolio
- `GET /api/portfolio/list/` - List portfolio holdings
- `POST /api/portfolio/add/` - Add stock to portfolio
- `DELETE /api/portfolio/remove/<id>/` - Remove stock
- `GET /api/portfolio/summary/` - Portfolio summary
- `GET /api/portfolio/analytics/` - Portfolio analytics
- `GET /api/portfolio/allocation/` - Allocation data
- `GET /api/portfolio/performance/` - Performance history

### Advisor
- `POST /api/advisor/chat/` - Send chat message
- `GET /api/advisor/history/` - Chat history
- `GET /api/advisor/suggested-prompts/` - Suggested prompts
- `GET /api/advisor/recommendations/` - AI recommendations
- `GET /api/advisor/stats/` - Advisor statistics

## Frontend Pages

- `/` - Landing page
- `/login/` - Login page
- `/register/` - Registration page
- `/dashboard/` - Main dashboard
- `/learning/` - Learning module
- `/prediction/` - Stock prediction
- `/news/` - News intelligence
- `/portfolio/` - Portfolio analyzer
- `/advisor/` - AI strategy advisor

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
```

### Admin Panel

Access the admin panel at: http://127.0.0.1:8000/admin/

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure proper `ALLOWED_HOSTS`
3. Use PostgreSQL database
4. Set up proper static file serving
5. Use HTTPS
6. Configure proper logging

## License

MIT License
