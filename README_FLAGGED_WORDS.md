# Flagged_Words Setup for SEA-LION Quality Signal EDA Visualisation tool

This guide explains how to set up the master copy for individual flagged words for their corresponding sheets. After the admins have approved the flagged words, they can add it to the Google sheet for the respective languages. Google Sheets is used for its accessibility and ease of setup.

### 1. Linking the google sheet to the database
- Under `.streamlit/secret.toml`

### 2. Connecting individual language id to their respective google sheet 
- Establish a connection to the Google Sheets API using the following code under the file directory `filters/flagged_words.py`:

```bash
conn = st.connection("authdb", type=GSheetsConnection)

def english_flagged_words():
    df_english_flagged_words = conn.read(worksheet='English')
    return df_english_flagged_words['English flagged words'].tolist()
flagged_words = {
    "en": english_flagged_words(),
}
```
Replace `English` with the respective language worksheet name and adjust the column name `English flagged words` accordingly.

### 3. Update and Visualize Data
After adding or removing flagged words, regenerate the signal data by running:

    python data_prep/get_data_for_visualization.py
    
The script will create updated statistics files in the data/generated_signals folder for visualization.



