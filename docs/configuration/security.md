# Security Guidelines

## API Key Security

### Environment Variables

```bash
# ✅ DO: Use environment variables
OPENWEATHER_API_KEY=your_actual_api_key_here

# ❌ DON'T: Hardcode in source files
api_key = "3a113d811b8150d09780f9bf941c9b93"  # NEVER DO THIS!
```

### Git Security

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Check if .env was ever committed
git log --all --full-history -- .env
```

### Best Practices

- Store API keys in `.env` file only
- Rotate API keys regularly
- Monitor API usage in dashboard
- Implement rate limiting
- Mask keys in logs (show only first 8 chars)

## Incident Response

### If API Key is Compromised
1. Regenerate API key in OpenWeatherMap dashboard
2. Update `.env` file with new key
3. Review git history
4. Monitor API usage for 24-48 hours

### If API Key is Accidentally Committed
1. Regenerate the API key immediately
2. Remove from git history using git filter-branch
3. Force push to remote repository

## Database Security

- Database file stored in `data/` directory (not committed to git)
- All inputs validated before storage
- JSON backups in secure local directory
- No personal/sensitive information stored

## API Usage

### OpenWeatherMap Limits
- Rate limiting: 60 calls/minute, 1,000 calls/day
- Monitor usage: [OpenWeatherMap Statistics](https://openweathermap.org/api/statistics)

## Security Checklist

- [ ] No API keys in source code
- [ ] `.env` file in `.gitignore`
- [ ] API keys masked in logs
- [ ] Rate limiting implemented
- [ ] HTTPS used for all API calls
- [ ] Input validation for user data
- [ ] Database file not committed to git

---

**For additional documentation, see the `docs/` directory.**
