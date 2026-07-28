# Fix Phase B — Auth, schema, smoke

## Done
- Hardened `pyronites_auth.py`: multi-shape response parsing, JWT claim fallback, clear 503 when Pyronites unset, login requires access_token
- Safer `repositories/base.py` list/one parsing
- `docs/PYRONITES_SCHEMA.md` table field list
- `scripts/smoke_phase_b.py` offline checks
- `.env.example` updated for Pyronites-first (no required Supabase)

## Run smoke
```bash
cd backend
pip install -r requirements.txt
python scripts/smoke_phase_b.py
```

## Auth contract
- Signup: validates email + strong password; may return `needs_confirmation=true` if provider omits token
- Login: always requires `access_token` or returns 401
- Protected routes: `Authorization: Bearer <token>`
- Token resolve order: Pyronites auth API → JWT claims (`sub`/`email`)
