import streamlit as st
import pandas as pd
import subprocess
import os
import sys
from pathlib import Path
import json

sys.path.append(str(Path(sys.path[0]).parent.absolute().parent.absolute()))

import config

st.set_page_config(layout="wide")

if "generated_data_file" not in st.session_state:
    st.session_state.generated_data_file = None

if "df" not in st.session_state:
    st.session_state.df = None


with st.sidebar:
    st.header("Generate and Preview Data_File")

    with st.expander("Generate Files"):
        st.write("Choose Data File to preview and visualize")
        data_options = config.DATASETS_IN_DATA_DIR
        selected_data_file = st.selectbox("Select a data file", data_options)

        num_visualize = st.number_input(
            "Number of data in file to be generated (7186)", 
            min_value=1, max_value=7186, value=config.NUM_DATA_SAMPLES
        )

        config.NUM_DATA_SAMPLES = num_visualize

        if "generated_file" not in st.session_state:
            st.session_state.generated_file = None

        new_filename = st.text_input("Enter new filename:", value="File_name")

        if st.button("Generate Data File"):
            with st.spinner("Processing..."):
                try:
                    # Run the script to generate data
                    result = subprocess.run(
                        ["python", "data_prep/get_data_for_visualization.py",str(num_visualize),new_filename],
                        check=True,
                        capture_output=True,
                        text=True,
                    )

                    st.success("Data file generated successfully!")
                    st.rerun()
    
                except subprocess.CalledProcessError as e:
                    st.error("Failed to generate data file.")
                    st.text(e.stderr)

    with st.expander("Choose a file to preview"):
    #     if isinstance(config.FILES_IN_GENERATED_SIGNALS_DIR, str):
    #         generated_files_dir = config.FILES_IN_GENERATED_SIGNALS_DIR
    #         generated_file_options = os.listdir(generated_files_dir)
    #     elif isinstance(config.FILES_IN_GENERATED_SIGNALS_DIR, list):
    #         generated_files_dir = None
    #         generated_file_options = config.FILES_IN_GENERATED_SIGNALS_DIR
    #     else:
    #         st.error("Invalid FILES_IN_GENERATED_SIGNALS_DIR format in config.")

        generated_file_options = []

        if os.path.exists(config.GENERATED_SIGNALS_DIR):
            for dirpath, dirnames, filenames in os.walk(config.GENERATED_SIGNALS_DIR):
                for filename in filenames:
                    if filename.endswith('.json'):
                        generated_file_options.append(filename)  # Only store filename
        else:
            st.error(f"Directory '{config.GENERATED_SIGNALS_DIR}' does not exist.")

        if not generated_file_options:
            generated_file_options = ["No JSON files found"]

        if "generated_file" in st.session_state and st.session_state.generated_file in generated_file_options:
            selected_generated_data_file = st.session_state.generated_file
        else:
            selected_generated_data_file = st.selectbox("Select a generated data file", generated_file_options)

        if selected_generated_data_file and selected_generated_data_file != "No JSON files found":
            full_file_path = os.path.join(config.GENERATED_SIGNALS_DIR, selected_generated_data_file)
            st.session_state.generated_data_file = full_file_path
        else:
            st.session_state.generated_data_file = None
                
        num_preview = st.number_input(
            "Number of rows to preview", min_value=1, max_value=num_visualize, key="num_preview"
        )

st.header("Preview Data")


if st.button("Preview"):
    if not st.session_state.generated_data_file:
        st.error("No file selected. Please select a file first.")
    elif not os.path.exists(st.session_state.generated_data_file):
        st.error(f"File not found: {st.session_state.generated_data_file}")
    else:
        try:
            if 'json_data' not in st.session_state:
                with open(st.session_state.generated_data_file, "r", encoding="utf-8") as json_file:
                    st.session_state.json_data = json.load(json_file)

            data = st.session_state.json_data

            if isinstance(data, list):  
                st.session_state.df = pd.DataFrame(data)
                if "words" in st.session_state.df.columns:
                    st.session_state.df = st.session_state.df.drop(columns=["words"])
                if "character_repetition_ratio" in st.session_state.df.columns:
                    if st.session_state.df["character_repetition_ratio"].apply(lambda x: isinstance(x, dict)).all():
                        st.session_state.df["character_repetition_ratio"] = st.session_state.df["character_repetition_ratio"].apply(lambda x: x.get("2") if isinstance(x, dict) else None)
                if "token_repetition_ratio" in st.session_state.df.columns:
                    if st.session_state.df["token_repetition_ratio"].apply(lambda x: isinstance(x, dict)).all():
                        st.session_state.df["token_repetition_ratio"] = st.session_state.df["token_repetition_ratio"].apply(lambda x: x.get("3") if isinstance(x, dict) else None)
                st.dataframe(st.session_state.df.head(num_preview))
            else:
                st.error("Invalid JSON format: Expected a list of dictionaries.")

        except json.JSONDecodeError:
            st.error("Error reading JSON file: Invalid JSON format.")
        except Exception as e:
            st.error(f"Error loading JSON: {e}")
