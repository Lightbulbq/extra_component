import streamlit as st
import subprocess

st.title("Run Signal Generation Script")

# Create a button in Streamlit
if st.button("Run Signal Generation"):
    with st.spinner("Running the script..."):
        try:
            # Run the script using subprocess
            result = subprocess.run(
                ["python", "data_prep/get_data_for_visualization.py"],
                check=True,
                capture_output=True,
                text=True,
            )
            st.success("Script ran successfully!")
            st.text(result.stdout)  # Display the script's output
        except subprocess.CalledProcessError as e:
            st.error("Script execution failed.")
            st.text(e.stderr)  # Display the error message

