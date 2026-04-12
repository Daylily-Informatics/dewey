## Dewey Playwright Auth E2E

Run:

```bash
AWS_PROFILE=your-profile E2E_USER_PASSWORD=... pytest tests/e2e/test_auth_e2e.py -m e2e
```

Defaults:
- `E2E_USER_EMAIL=johnm+test@lsmc.com`
- `DEWEY_BASE_URL=https://localhost:18914`

These tests cover only the Dewey GUI login/logout browser flow.
