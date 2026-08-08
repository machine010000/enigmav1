# Upwork Setup Guide

This guide covers setting up Upwork integration for production use.

## Prerequisites

- Active Upwork freelancer account
- Upwork API credentials (client_id, client_secret)
- Production callback URL

## Getting Upwork API Credentials

### 1. Apply for API Access

1. Go to https://www.upwork.com/developer/keys/apply
2. Log in with your Upwork freelancer account
3. Select "OAuth 2.0" as the key type
4. Fill in the application form:
   - Application Name: "Enigma AI Assistant"
   - Description: "AI-powered freelance job application assistant"
   - Website: Your production domain
   - Callback URL: `https://your-domain.com/upwork/callback`
5. Submit the application
6. Wait for approval (may take 1-2 business days)

### 2. Configure Environment Variables

Once approved, configure the following in your `.env` file:

```env
UPWORK_CLIENT_ID=<your-client-id>
UPWORK_CLIENT_SECRET=<your-client-secret>
UPWORK_REDIRECT_URI=https://your-domain.com/upwork/callback
```

## OAuth Flow

### Step 1: Initiate OAuth

Call the OAuth initiation endpoint:

```bash
GET /upwork/auth
```

Response:
```json
{
  "authorization_url": "https://www.upwork.com/ab/account-security/oauth2/authorize?...",
  "state": "random-state-string"
}
```

### Step 2: User Authorization

1. Redirect user to `authorization_url`
2. User logs into Upwork
3. User approves access
4. Upwork redirects to callback URL

### Step 3: Handle Callback

Upwork redirects to your callback URL with:
- `code`: Authorization code
- `state`: State parameter (for CSRF protection)

The system exchanges the code for an access token.

## Account Information

After authentication, the system retrieves:

- Account ID
- Username
- Account status (active, suspended, restricted)
- Available Connects
- Total Connects
- Daily/monthly application limits

## Connects Management

### Connects Cost

Each job application requires a certain number of Connects:
- Standard jobs: 1-6 Connects
- Premium jobs: May require more Connects

### Connects Protection

The system checks Connects before submission:
1. Retrieve job application cost
2. Check available Connects
3. If insufficient, block submission
4. Display cost to user for approval

### Connects Tracking

The system tracks:
- Connects spent per application
- Total Connects spent
- Remaining Connects
- Connects refill date

## Rate Limiting

Upwork API has rate limits:
- 100 requests per minute
- 10,000 requests per day

The system implements:
- Exponential backoff on 429 errors
- Request queuing
- Rate limit monitoring

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 429 Rate Limit | Too many requests | Wait and retry |
| 403 Forbidden | Insufficient permissions | Check API scope |
| 500 Server Error | Upwork service issue | Retry later |

### Error Recovery

The system automatically:
- Retries retriable errors (429, 500)
- Refreshes expired tokens
- Logs all errors for debugging
- Notifies user of non-retriable errors

## Testing OAuth Flow

### Development Testing

Use Upwork's sandbox environment for testing:
- Set `UPWORK_REDIRECT_URI` to localhost
- Test the complete OAuth flow
- Verify token storage and refresh

### Production Testing

1. Use production credentials
2. Test with real Upwork account
3. Verify account information retrieval
4. Test job discovery
5. Test application submission (with approval)

## Security Considerations

- Never commit Upwork credentials to Git
- Store credentials in environment variables
- Use HTTPS for all OAuth requests
- Implement state parameter for CSRF protection
- Refresh tokens securely
- Never log OAuth tokens
- Rotate credentials regularly

## Troubleshooting

### OAuth Fails

1. Verify callback URL matches Upwork settings
2. Check client_id and client_secret
3. Ensure HTTPS is used
4. Verify state parameter matches

### Token Expired

1. System should auto-refresh
2. Check refresh token is stored
3. Verify refresh token is valid

### Rate Limited

1. Wait before retrying
2. Reduce request frequency
3. Implement caching where possible

### Account Restricted

1. Check Upwork account status
2. Resolve any account issues
3. Contact Upwork support if needed

## Monitoring

Monitor:
- OAuth success/failure rate
- Token refresh frequency
- API rate limit usage
- Connects balance
- Application submission success rate
