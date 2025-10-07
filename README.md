# AWS Quiz Platform - High Performance Edition

A scalable, high-performance web-based quiz application for AWS certifications, built with Flask and PostgreSQL, optimized for concurrent users and load balancing.

## 🚀 Performance Features

- ⚡ **Database Connection Pooling**: Handles 20 concurrent database connections
- 🏎️ **Redis Caching**: Caches frequently accessed data and user sessions
- 📊 **Load Balancing**: Gunicorn with Gevent workers for concurrent request handling
- 🛡️ **Rate Limiting**: Prevents abuse with intelligent request throttling
- 🎯 **Query Optimization**: Database indexes for fast data retrieval
- 🔄 **Session Management**: Redis-based sessions for scalability
- 📈 **Production Ready**: Configured for high-traffic deployment

## 🎯 Core Features

- 🔐 **User Authentication**: Sign up, sign in, password reset functionality
- 📚 **Multi-Quiz System**: AWS Cloud Practitioner, Data Engineer, Tableau (expandable)
- 📊 **Progress Tracking**: Comprehensive quiz history and performance analytics
- 🎨 **Modern UI**: Clean, responsive design with optimized loading
- 📱 **Mobile Optimized**: Works seamlessly on all devices
- 🔄 **Real-time Results**: Instant feedback and detailed explanations
- 👨‍💼 **Admin Dashboard**: User management and analytics

## 📋 System Requirements

### Production Environment
- **CPU**: 2+ cores (4+ recommended for high traffic)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 10GB+ SSD
- **Network**: High bandwidth for concurrent users

### Software Dependencies
- Python 3.8+
- PostgreSQL 12+ 
- Redis 6.0+
- Nginx (for production reverse proxy)

## 🛠️ Installation & Deployment

### Quick Development Setup

1. **Clone the project**:
   ```bash
   cd C:\Users\venkatasai.p\Documents\aws_quiz_website
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify database connection**:
   - Ensure PostgreSQL is running on port 5480
   - Database `cretificate_quiz_db` exists
   - User `psql_master` has access
   - Table `aws_questions` contains your AWS questions

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser**:
   Visit `http://localhost:5000`

## Usage

### First Time Setup

1. **Register**: Create a new account with your details
2. **Sign In**: Use your credentials to log in
3. **Take Quiz**: Select number of questions and start practicing
4. **View Results**: See detailed feedback and explanations
5. **Track Progress**: Monitor your improvement over time

### Production / Load Balancer Readiness

New additions for stability:

- `/healthz` – liveness probe (always 200 if process alive)
- `/readyz` – readiness probe (503 if DB unreachable)
- Structured logging to stdout (set `LOG_LEVEL`)
- `wsgi.py` entrypoint for Gunicorn/Waitress
- `flask create-indexes` command to add helpful DB indexes

#### Gunicorn (Linux)
```bash
export FLASK_CONFIG=production
gunicorn -w 4 -k gthread --threads 2 -b 0.0.0.0:8000 --timeout 90 --graceful-timeout 30 wsgi:app
```

#### Waitress (Windows)
```powershell
$env:FLASK_CONFIG='production'
python -c "from waitress import serve; from wsgi import app; serve(app, host='0.0.0.0', port=8000)"
```

#### Health Checks (AWS ALB / Nginx / Kubernetes)
- Path: `/readyz`
- Success codes: 200
- Interval: 30s (or 10s for faster failover)
- Unhealthy threshold: 3

Example Nginx upstream snippet:
```
location /healthz { return 200 'ok'; add_header Content-Type text/plain; }
location /readyz { proxy_pass http://app_backend/readyz; }
```

#### Environment Variables (.env)
See `.env.example` for tunables:
- DB_POOL_MIN / DB_POOL_MAX
- RATELIMIT_DEFAULT (e.g. `1000 per hour;200 per minute`)
- LOG_LEVEL

#### Index Optimization
Run once after deploying:
```bash
flask create-indexes
```

#### Zero-Downtime Rolling Update (Gunicorn)
1. Start new set of workers on a new port (e.g., 8001)
2. Update load balancer target group to include new port
3. Drain old workers and stop old process

#### Common Issues
| Symptom | Cause | Fix |
|---------|-------|-----|
| 503 on /readyz | DB unreachable | Verify security group / credentials |
| Slow first request | Cold pool init | Warm by curling `/readyz` on deploy |
| Connection refused after deploy | Old process died early | Use supervisor/systemd for process management |

### Quiz Options

- **10 Questions**: Quick practice session
- **20 Questions**: Standard practice (default)
- **30 Questions**: Extended practice
- **50 Questions**: Challenge mode
- **65 Questions**: Full exam simulation

### Features

- **Dashboard**: Overview of your statistics and progress
- **Quiz History**: See all past quiz attempts
- **Detailed Results**: Review each question with correct answers
- **Responsive Design**: Works on desktop, tablet, and mobile

## Database Schema

The application creates the following tables:

### `users`
- User account information
- Authentication details
- Profile data

### `quiz_sessions`
- Quiz attempt records
- Scores and timing
- Completion status

### `quiz_answers`
- Individual question responses
- Correct/incorrect tracking
- Answer history

## Configuration

### Database Settings

Update `DB_CONFIG` in `app.py` if your database settings differ:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5480,
    'database': 'cretificate_quiz_db',
    'user': 'psql_master',
    'password': 'your_password_here'
}
```

### Security

**Important**: Change the secret key in production:

```python
app.secret_key = 'your-production-secret-key'
```

## File Structure

```
aws_quiz_website/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── main.js       # JavaScript functionality
└── templates/
    ├── base.html         # Base template
    ├── auth/
    │   ├── login.html    # Sign in page
    │   ├── register.html # Registration page
    │   └── forgot_password.html
    ├── dashboard/
    │   ├── home.html     # Main dashboard
    │   └── history.html  # Quiz history
    ├── quiz/
    │   ├── start.html    # Quiz configuration
    │   ├── question.html # Question display
    │   └── results.html  # Quiz results
    └── errors/
        ├── 404.html      # Page not found
        └── 500.html      # Server error
```

## Color Scheme

The design uses a professional color palette inspired by CYNCS:

- **Primary Dark**: `#1a2332` (Navigation, headers)
- **Primary Blue**: `#2c3e50` (Cards, main content)
- **Accent Teal**: `#1abc9c` (Buttons, highlights)
- **Dark Background**: `#0f1419` (Page background)
- **Success Green**: `#27ae60` (Correct answers)
- **Warning Orange**: `#f39c12` (Moderate scores)
- **Danger Red**: `#e74c3c` (Incorrect answers)

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- Mobile browsers

## Security Features

- Password hashing with Werkzeug
- Session management
- SQL injection protection
- CSRF protection (built into Flask)
- Input validation and sanitization

## Performance

- Optimized database queries
- Efficient question randomization
- Minimal JavaScript for fast loading
- Responsive CSS for all devices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please respect AWS trademark and certification guidelines.

## Support

For issues or questions:

1. Check the console for error messages
2. Verify database connection
3. Ensure all dependencies are installed
4. Check PostgreSQL logs if database issues persist

## Future Enhancements

- [ ] Email notifications for password reset
- [ ] More detailed analytics
- [ ] Question categories and filtering
- [ ] Timed quiz mode
- [ ] Study mode with explanations
- [ ] Export quiz results to PDF
- [ ] Dark/light theme toggle
- [ ] Question bookmarking
- [ ] Practice weak areas

---

**Note**: Make sure your existing `aws_questions` table in PostgreSQL contains the AWS certification questions before running the application.
