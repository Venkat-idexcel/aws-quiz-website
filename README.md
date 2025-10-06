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