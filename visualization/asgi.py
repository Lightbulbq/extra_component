# asgi.py

import subprocess

def app(scope):
    if scope['type'] == 'http':
        # Run the Streamlit app
        subprocess.run(["streamlit", "run", "streamlit_app.py", "--server.headless", "true"])
    return None