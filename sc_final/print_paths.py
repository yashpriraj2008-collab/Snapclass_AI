import os

print('cwd=', os.getcwd())

# Candidate secrets paths
candidates = [
    os.path.join(os.getcwd(), '.streamlit', 'secrets.toml'),
    os.path.join(os.path.dirname(os.getcwd()), '.streamlit', 'secrets.toml'),
    os.path.join(os.path.expanduser('~'), '.streamlit', 'secrets.toml'),
]

for p in candidates:
    print('candidate=', p, 'exists=', os.path.exists(p))

# Also print Streamlit default search locations
try:
    import streamlit as st
    import streamlit.runtime.secrets as sec
    # sec.Secrets will parse on demand; we just show derived config.
except Exception:
    pass

