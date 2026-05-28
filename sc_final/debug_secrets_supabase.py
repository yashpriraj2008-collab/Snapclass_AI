import os
import streamlit as st

# This script is meant to be run via: streamlit run app.py
# It will not change UI; it only helps us inspect secrets and cwd.

def main():
    cwd = os.getcwd()
    secrets_path = None
    # Streamlit doesn't expose the actual path directly; we infer common locations.
    # We'll print candidate paths that could be used.
    candidates = [
        os.path.join(cwd, ".streamlit", "secrets.toml"),
        os.path.join(os.path.dirname(cwd), ".streamlit", "secrets.toml"),
        os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml"),
    ]
    for p in candidates:
        if os.path.exists(p):
            secrets_path = p
            break

    secrets_detected = "yes"
    secret_keys = []
    try:
        # st.secrets access triggers parsing
        secret_keys = list(st.secrets.keys())
    except Exception:
        secrets_detected = "no"
        secret_keys = []

    # Only show allowed supabase keys
    allowed = {"SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_ANON_KEY"}
    loaded_allowed = [k for k in secret_keys if k in allowed]

    # Supabase status helper if available
    supabase_connected = "no"
    try:
        from src.database.client import is_db_connected
        supabase_connected = "yes" if is_db_connected() else "no"
    except Exception:
        supabase_connected = "no"

    print("=== DEBUG SECRETS/SUPABASE ===")
    print("current_working_directory=", cwd)
    print("secrets_detected=", secrets_detected)
    print("current_secrets_toml_absolute_path=", secrets_path)
    print("loaded_secret_keys_allowed=", loaded_allowed)
    print("supabase_connected=", supabase_connected)


if __name__ == "__main__":
    main()

