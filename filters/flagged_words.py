# Built from native speakers, with inspiration from
# https://github.com/zacanger/profane-words
# and
# https://github.com/thisandagain/washyourmouthoutwithsoap/blob/develop/data/build.json
# and
# https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit as st

st.set_page_config(layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    flagged_words_url = st.secrets.connections.flagged_words["spreadsheet"]
except Exception as e:
    flagged_words_url = ""
    st.info(repr(e))


def flagged_words(worksheet_name: str, column_header_name: str):
    if not flagged_words_url or not worksheet_name or not column_header_name:
        return []

    df_flagged_words = conn.read(
        spreadsheet=flagged_words_url, worksheet=worksheet_name)
    return df_flagged_words[column_header_name].tolist()


def english_flagged_words():
    return flagged_words(worksheet_name="English", column_header_name="English flagged words")


def chinese_flagged_words():
    return flagged_words(worksheet_name="Chinese", column_header_name="Chinese flagged words")


def arabic_flagged_words():
    return flagged_words(worksheet_name="Arabic", column_header_name="Arabic flagged words")


def bengali_flagged_words():
    return flagged_words(worksheet_name="Bengali", column_header_name="Bengali flagged words")


def ca_flagged_words():
    return flagged_words(worksheet_name="ca", column_header_name="ca flagged words")


def spanish_flagged_words():
    return flagged_words(worksheet_name="Spanish", column_header_name="Spanish flagged words")


def french_flagged_words():
    return flagged_words(worksheet_name="French", column_header_name="French flagged words")


def hindi_flagged_words():
    return flagged_words(worksheet_name="Hindi", column_header_name="Hindi flagged words")


def bahasa_flagged_words():
    return flagged_words(worksheet_name="Bahasa", column_header_name="Bahasa Indonasian flagged words")


def portuguese_flagged_words():
    return flagged_words(worksheet_name="Portuguese", column_header_name="Portuguese flagged words")


def thai_flagged_words():
    return flagged_words(worksheet_name="Thai", column_header_name="Thai flagged words")


def Vietnamese_flagged_words():
    return flagged_words(worksheet_name="Vietnamese", column_header_name="Vietnamese flagged words")


def Urdu_flagged_words():
    return flagged_words(worksheet_name="Urdu", column_header_name="Urdu flagged words")


flagged_words = {
    "en": english_flagged_words(),
    "zh": english_flagged_words() + chinese_flagged_words(),
    "ar": english_flagged_words() + arabic_flagged_words(),
    "bn": english_flagged_words() + bengali_flagged_words(),
    "ca": english_flagged_words() + ca_flagged_words(),
    "es": english_flagged_words() + spanish_flagged_words(),
    "eu": english_flagged_words() + [],
    "fr": english_flagged_words() + french_flagged_words(),
    "hi": english_flagged_words() + hindi_flagged_words(),
    "id": english_flagged_words() + bahasa_flagged_words(),
    "pt": english_flagged_words() + portuguese_flagged_words(),
    "ur": english_flagged_words() + Urdu_flagged_words(),
    "vi": english_flagged_words() + Vietnamese_flagged_words(),
    "th": english_flagged_words() + chinese_flagged_words() + thai_flagged_words(),
    "ms": english_flagged_words() + chinese_flagged_words() + [],
    "my": english_flagged_words() + chinese_flagged_words() + [],
    "tl": english_flagged_words() + chinese_flagged_words() + [],
    "lo": english_flagged_words() + chinese_flagged_words() + [],
    "km": english_flagged_words() + chinese_flagged_words() + [],
    "ta": english_flagged_words() + chinese_flagged_words() + [],
}
