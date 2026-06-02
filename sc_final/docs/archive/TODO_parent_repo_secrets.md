# TODO

## Secrets & API key handling (Supabase/Razorpay)
- [ ] Add/remove required keys in `sc_final/.streamlit/secrets.toml`.
- [ ] Ensure app reads secrets keys via `src/database/client.py` (SUPABASE_URL + SUPABASE_ANON_KEY).
- [ ] Never commit real secrets to git (verify `.gitignore`).
- [ ] Rotate any exposed keys found in repo history (if applicable).
- [ ] Restart Streamlit after changing secrets.

