#!/bin/bash

#gunicorn -w 4 -k uvicorn.workers.UvicornWorker asgi:app
# streamlit run visualization.py
streamlit run visualization.py --server.maxMessageSize=200 --server.runOnSave=true

