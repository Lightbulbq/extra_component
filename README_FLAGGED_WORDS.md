# Flagged_Words Setup for SEA-LION Quality Signal EDA Visualisation tool

This guide explains how to set up the master copy for flagged words and their corresponding individual sheets. These steps ensure each linguist can access only their designated content. Google Sheets is used for its accessibility and ease of setup.

### 1. Create a Master Copy in Google Sheets
The master copy should include all flagged words across different languages.

### 2. Lock the master copy 
- Right-click the sheet and select Protect sheet.
- Set permissions to allow only admins to edit the sheet. Others will only have view access.

<img width="257" alt="Screenshot 2024-12-02 at 4 39 14 PM" src="https://github.com/user-attachments/assets/579645d5-a7b9-40b6-b48a-dd97c05f870b">
<img width="457" alt="Screenshot 2024-12-02 at 4 41 41 PM" src="https://github.com/user-attachments/assets/0876fed6-5ae2-492b-8f3c-81bdf319eeea">

### 3. Creating individual sheets for the respective languages based on the languages inside the master copy
<img width="915" alt="Screenshot 2024-12-02 at 4 51 28 PM" src="https://github.com/user-attachments/assets/c411dcbb-e4ce-4882-ab83-cf027682161c">

- Create separate sheets for each language listed in the master copy.
- Use this formula in the first cell of the language sheet to copy words while removing punctuation:

```bash
=SUBSTITUTE(SUBSTITUTE('Filter_words(Master_copy)'!A2, ".", ""), ",", "")
```

Replace `A2` with the cell reference of the first word in the flagged words column. Drag down to populate the entire list for that language.

### 4. Lock Individual Language Sheets (Optional)
- Protect each sheet by restricting access to the designated linguist.
This ensures each linguist can only view and edit their assigned language sheet.

### 5. Connecting individual language id to their respective google sheet 
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

### 6. Update and Visualize Data
After adding or removing flagged words, regenerate the signal data by running:

    python data_prep/get_data_for_visualization.py
    
The script will create updated statistics files in the data/generated_signals folder for visualization.



