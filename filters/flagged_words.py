# Built from native speakers, with inspiration from
# https://github.com/zacanger/profane-words
# and
# https://github.com/thisandagain/washyourmouthoutwithsoap/blob/develop/data/build.json
# and
# https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words
from streamlit_gsheets import GSheetsConnection
import streamlit as st

st.set_page_config(layout="wide")
conn = st.connection("authdb", type=GSheetsConnection)

def english_flagged_words():
    df_english_flagged_words = conn.read(worksheet='English')
    return df_english_flagged_words['English flagged words'].tolist()

def chinese_flagged_words():
    df_chinese_flagged_words = conn.read(worksheet='Chinese')
    return df_chinese_flagged_words['Chinese flagged words'].tolist()

def arabic_flagged_words():
    df_arabic_flagged_words = conn.read(worksheet='Arabic')
    return df_arabic_flagged_words['Arabic flagged words'].tolist()

def bengali_flagged_words():
    df_bengali_flagged_words = conn.read(worksheet='Bengali')
    return df_bengali_flagged_words['Bengali flagged words'].tolist()

def ca_flagged_words():
    df_arabic_flagged_words = conn.read(worksheet='ca')
    return df_arabic_flagged_words['ca flagged words'].tolist()

def spanish_flagged_words():
    df_spanish_flagged_words = conn.read(worksheet='Spanish')
    return df_spanish_flagged_words['Spanish flagged words'].tolist()

def french_flagged_words():
    df_french_flagged_words = conn.read(worksheet='French')
    return df_french_flagged_words['French flagged words'].tolist()

def hindi_flagged_words():
    df_hindi_flagged_words = conn.read(worksheet='Hindi')
    return df_hindi_flagged_words['Hindi flagged words'].tolist()

def bahasa_flagged_words():
    df_bahasa_flagged_words = conn.read(worksheet='Bahasa')
    return df_bahasa_flagged_words['Bahasa Indonasian flagged words'].tolist()

def portuguese_flagged_words():
    df_portuguese_flagged_words = conn.read(worksheet='Portuguese')
    return df_portuguese_flagged_words['Portuguese flagged words'].tolist()

def thai_flagged_words():
    df_thai_flagged_words = conn.read(worksheet='Thai')
    return df_thai_flagged_words['Thai flagged words'].tolist()

def Vietnamese_flagged_words():
    df_vietnamese_flagged_words = conn.read(worksheet='Vietnamese')
    return df_vietnamese_flagged_words['Vietnamese flagged words'].tolist()

def Urdu_flagged_words():
    df_urdu_flagged_words = conn.read(worksheet='Urdu')
    return df_urdu_flagged_words['Urdu flagged words'].tolist()

flagged_words = {
    "en": english_flagged_words(),
    "zh": english_flagged_words() + chinese_flagged_words(),
    "ar": english_flagged_words() + arabic_flagged_words(),
    "bn": english_flagged_words() + bengali_flagged_words(),
    "ca" : english_flagged_words() + ca_flagged_words(),
    "es": english_flagged_words() + spanish_flagged_words(),
    "eu": english_flagged_words()+ [],
    "fr": english_flagged_words() + french_flagged_words(),
    "hi": english_flagged_words() + hindi_flagged_words(),
    "id": english_flagged_words() + bahasa_flagged_words(),
    "pt": english_flagged_words() + portuguese_flagged_words(),
    "ur": english_flagged_words() + Urdu_flagged_words(),
    "vi": english_flagged_words() + Vietnamese_flagged_words(),
    "th":english_flagged_words() + chinese_flagged_words() + thai_flagged_words(),
    "ms": english_flagged_words() + chinese_flagged_words() + [],
    "my": english_flagged_words() + chinese_flagged_words() + [],
    "tl": english_flagged_words() + chinese_flagged_words() + [],
    "lo": english_flagged_words() + chinese_flagged_words() + [],
    "km": english_flagged_words() + chinese_flagged_words() + [],
    "ta": english_flagged_words() + chinese_flagged_words() + [],
}
