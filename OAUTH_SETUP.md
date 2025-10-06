# OAuth Setup Guide for AWS Quiz Website

## Overview
The application now supports OAuth authentication with Google, GitHub, and Microsoft providers, making it easy for users to sign in with their existing accounts.

## Development vs Production Setup

### Current Development Configuration
The OAuth providers are configured with placeholder credentials that work for development testing but need to be replaced for production use.

### Setting Up OAuth Providers for Production

#### 1. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure OAuth consent screen
6. Add authorized redirect URI: `https://yourdomain.com/auth/google/callback`
7. Copy the Client ID and Client Secret
8. Update `OAUTH_CREDENTIALS['google']` in `app.py`

#### 2. GitHub OAuth Setup
1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Set Authorization callback URL: `https://yourdomain.com/auth/github/callback`
4. Copy the Client ID and Client Secret
5. Update `OAUTH_CREDENTIALS['github']` in `app.py`

#### 3. Microsoft OAuth Setup
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to Azure Active Directory → App registrations
3. Click "New registration"
4. Set redirect URI: `https://yourdomain.com/auth/microsoft/callback`
5. Copy the Application (client) ID and create a client secret
6. Update `OAUTH_CREDENTIALS['microsoft']` in `app.py`

## Environment Variables (Recommended)
For production, store OAuth credentials as environment variables:

```python
# In app.py, replace hardcoded credentials with:
OAUTH_CREDENTIALS = {
    'google': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        # ... rest of config
    },
    # Similar for other providers
}
```

## Features Implemented

### User Experience
- **Seamless Registration**: New users can sign up instantly with OAuth
- **Account Linking**: Existing email accounts are automatically linked with OAuth
- **Profile Pictures**: OAuth providers can provide profile pictures
- **No Password Required**: OAuth users don't need to set passwords

### Security Features
- **Secure Token Handling**: OAuth tokens are processed securely
- **Provider Validation**: Only supported providers are allowed
- **Email Verification**: OAuth providers handle email verification
- **Rate Limiting**: OAuth routes are protected against abuse

### Database Schema
New columns added to users table:
- `oauth_provider`: The OAuth provider (google, github, microsoft)
- `oauth_id`: The unique ID from the OAuth provider
- `profile_picture_url`: URL to user's profile picture
- `password_hash`: Made optional for OAuth users

## OAuth Flow
1. User clicks OAuth button (Google/GitHub/Microsoft)
2. Redirected to provider's authorization server
3. User authorizes the application
4. Provider redirects back with authorization code
5. Application exchanges code for access token
6. Application gets user info from provider's API
7. User is created/updated in database
8. User is logged in automatically

## Error Handling
- Invalid providers are rejected
- Failed OAuth attempts redirect to login with error message
- Missing user information is handled gracefully
- Database errors are caught and logged

## Testing OAuth (Development)
1. OAuth buttons are visible on login/register pages
2. Clicking them shows configuration error (expected with placeholder credentials)
3. UI styling is responsive and matches app theme
4. Error messages display properly

## Production Checklist
- [ ] Set up OAuth applications with each provider
- [ ] Configure proper redirect URIs
- [ ] Store credentials as environment variables
- [ ] Test OAuth flow on production domain
- [ ] Configure HTTPS for secure OAuth
- [ ] Set up proper error monitoring
- [ ] Test account linking scenarios
- [ ] Verify profile picture handling

## Security Considerations
- Always use HTTPS in production
- Validate OAuth state parameters
- Implement proper session management
- Monitor for OAuth abuse attempts
- Keep OAuth library dependencies updated
- Review OAuth scopes regularly

## Support Contact
For OAuth setup assistance or issues, contact your development team.