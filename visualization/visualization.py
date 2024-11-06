import streamlit as st

import os

from io import StringIO
import base64
import json
import pandas as pd
import math

pd.options.mode.chained_assignment = None

import numpy as np

import matplotlib.pyplot as plt

import sys
from pathlib import Path

# Append the path of the parent directory to the python path
# to find the files filtering.py and languages_id.py in the parent directory
sys.path.append(str(Path(sys.path[0]).parent.absolute().parent.absolute()))

from filters.filtering import LoadParameters, ModifyingDocuments, Filtering
from filters.languages_id import langs_id
import config

class Visualization_for_lang:
    def __init__(
        self,
        path_data,
        lang,
        num_docs,
        num_docs_for_words,
        max_len_text_display,
        lang_dataset_id,
        path_fasttext_model,
        path_sentencepiece_model,
        path_kenlm_model,
    ):
        self.path_data = path_data
        self.lang = lang
        self.num_docs = num_docs
        self.num_docs_for_words = num_docs_for_words
        self.max_len_text_display = max_len_text_display
        self.lang_dataset_id = lang_dataset_id
        self.param = LoadParameters.load_parameters(lang_dataset_id)
        self.stopwords = LoadParameters.load_stopwords(lang_dataset_id)
        self.flagged_words = LoadParameters.load_flagged_words(lang_dataset_id)
        self.model_lang_id = LoadParameters.load_model_lang_id(lang_dataset_id, path_fasttext_model)
        self.sentencepiece_model = LoadParameters.load_sentencepiece_model(lang_dataset_id, path_sentencepiece_model)
        self.sentencepiece_model_tok = self.sentencepiece_model if self.param["tokenization"] else None
        self.kenlm_model = LoadParameters.load_kenlm_model(lang_dataset_id, path_kenlm_model)

    def set_title(self):
        st.title(f"Filtering visualization for {self.lang}")

    def open_data(self):
        try:
            if 'json_data' not in st.session_state:
                with open(self.path_data) as json_file:
                    st.session_state.json_data = json.load(json_file) 
            data = st.session_state.json_data

        except json.JSONDecodeError as e:
            raise ValueError(
                "Error decoding JSON: The document is empty or not a valid JSON file.") from e

        self.num_docs = min(self.num_docs, len(data))
        self.num_docs_for_words = min(self.num_docs_for_words, len(data))
        self.num_docs_for_sents = min(self.num_docs, len(data))

        if "words" in data[0]:
            words = [doc["words"] for doc in data[: self.num_docs_for_words]]
            words = [word for doc in words for word in doc]
            self.words = pd.DataFrame(words)
        else:
            self.words = None

        docs = data[: self.num_docs]
        for doc in docs:
            if not (self.words is None):
                del doc["words"]
                # del doc["sentences"]
            if len(doc["text"]) > self.max_len_text_display:
                doc["text"] = (
                    doc["text"][: self.max_len_text_display]
                    + " [...] [THIS LONG TEXT HAS BEEN TRUNCATED FOR DISPLAY REASONS]"
                )

        self.docs_checkpoint = pd.DataFrame(docs)

        if "annotation" not in self.docs_checkpoint.columns:
            # when signal file is loaded for the first time, it may not contain the annotation column. If so, then add it
            self.docs_checkpoint["annotation"] = None

        if "annotation_data" in st.session_state.keys():
            # if saved annotation state is in the session, apply it to the loaded dataframe
            annotation_df = st.session_state["annotation_data"]
            self.docs_checkpoint["annotation"] = annotation_df["annotation"]    
            
        self.docs = self.docs_checkpoint

    @staticmethod
    def highlight_non_rows(row):
        style = ['']
        # Determine background color based on annotation value
        if row['annotation'] == "retain":
            style = ['background-color: rgba(57, 91, 59, 0.6)']  # Green for retain
        elif row['annotation'] == "discard":
            style = ['background-color: rgba(110, 14, 14, 0.4)']  # Red for discard
            
        return style * len(row) # Apply the style to all columns
    

    @staticmethod
    def print_discarded_by_cond(cond):
        st.caption(f"{(len(cond) - np.sum(1*cond)) / len(cond) *100:.2f}% of the total is discarded with this filter.")

    @staticmethod
    def plot_hist(dataframe, key, num_bins=50):
        checkbox = st.checkbox("Diplay distribution",value=True, key=f"display_distribution_{key[0]}")
        if checkbox:
            fig, ax = plt.subplots()
            val = dataframe[key[0]].values
            if np.median(val) != 0:
                val = val[abs(val - np.median(val)) < 9 *np.median(np.absolute(val - np.median(val)))]
            ax.hist(val, bins=num_bins, density=True)
            ax.set_title(" ".join(key[0].split("_")))
            ax.axvline(x=key[1], color="r", linestyle="dashed")
            st.pyplot(fig)

    @staticmethod
    def display_dataset(dataframe, cond, description, type_of_examples, data_editor_id=None, data_id=None, on_annotation_change_fn=None):
        displayed_examples = dataframe.loc[cond]
        st.subheader(
            f"{description}: {len(displayed_examples)} {type_of_examples} ({len(displayed_examples) / len(dataframe.index) * 100:.2f}%)"
        )
        st.markdown("Click on a column to sort by it, place the cursor on the text to display it.")

        # we use a variable to set the method for displaying the dataframe's columns
        hide_columns = config.USE_HIDE_SELECTED_COLS_METHOD
        if hide_columns:
            # hide selected columns and show the rest
            columns_to_hide = config.SELECTED_COLS
            # Drop columns if they exist
            displayed_examples_edited = displayed_examples.drop(
                columns=[col for col in columns_to_hide if col in displayed_examples.columns]
            )
        else:
            # show only selected columns
            columns_to_show = config.SELECTED_COLS
            # Display only the specified columns if they exist in the dataframe
            displayed_examples_edited = (displayed_examples[columns_to_show]
                if all(col in displayed_examples.columns for col in columns_to_show)
                else displayed_examples
            )
        
        if data_id is not None:
            st.session_state[data_id] = displayed_examples_edited
            
        # Applying highlight to row based on annotation value
        df_styled = displayed_examples_edited.style.apply(Visualization_for_lang.highlight_non_rows, axis=1)

        # only disabled columns will display styling
        edited_df = st.data_editor(df_styled, hide_index=False,use_container_width=True, column_config={
            "number_tokens": st.column_config.NumberColumn(disabled=True),
            "character_repetition_ratio": st.column_config.NumberColumn(disabled=True),
            "token_repetition_ratio": st.column_config.NumberColumn(disabled=True),
            "special_characters_ratio":st.column_config.NumberColumn(disabled=True),
            "flagged_words_ratio": st.column_config.NumberColumn(disabled=True),
            "lang_id_score": st.column_config.NumberColumn(disabled=True),
            "perplexity_score": st.column_config.NumberColumn(disabled=True),
            "text":st.column_config.TextColumn(disabled=True),
            "annotation": st.column_config.SelectboxColumn(
                options=['retain','discard'],  # Provide annotation options
            )
        }, key=data_editor_id,
        on_change=on_annotation_change_fn, args=[data_editor_id, data_id])


    def data_editor_on_change(self, data_editor_id, data_id):
        # Get the edited rows from the data editor
        editor_state = st.session_state[data_editor_id]
        
        for data_editor_index, updates in editor_state["edited_rows"].items():
            for edited_key, edited_value in updates.items():
                # Get the original dataframe index of the row
                original_index = st.session_state[data_id].index[data_editor_index]
                # Update the annotation value in the original dataframe
                self.docs.loc[self.docs.index == original_index, edited_key] = edited_value

        # save the annotation state in the session
        st.session_state["annotation_data"] = self.docs[["annotation"]]
        
        
    def filtering_of_docs(self):
        def set_sliders():
            columns = list(self.docs)
            keys = []
            conds = {}

            def get_cond(key, cutoff, max_cutoff, max_pp=None):
                if max_cutoff:
                    if max_pp:
                        return self.docs[key] <= min(max_pp, cutoff)
                    else:
                        return self.docs[key] <= cutoff
                return self.docs[key] >= cutoff

            if "number_tokens" in columns:
                with st.sidebar.expander("Number of tokens"):
                    cutoff_def = (
                        "If the number of tokens of a document is lower than this number, the document is removed."
                    )
                    max_nb_words = int(np.max(self.docs["number_tokens"])) + 1

                    # Text input for minimum number of tokens
                    min_tokens_input = st.text_input("Enter minimum number of tokens", "0")
                    try:
                        min_tokens_value = int(min_tokens_input)
                    except ValueError:
                        min_tokens_value = 0

                    # Slider for minimum number of tokens
                    cutoff_min_number_words = st.slider(cutoff_def, 0, min(max_nb_words, 500), min_tokens_value)
                    new_key = ("number_tokens", cutoff_min_number_words, False)
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond_1 = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond_1)

                    cutoff_def = (
                        "If the number of tokens of a document is higher than this number, the document is removed."
                    )

                    # Text input for maximum number of tokens
                    max_tokens_input = st.text_input(
                        "Enter maximum number of tokens", str(max_nb_words))
                    try:
                        max_tokens_value = int(max_tokens_input)
                    except ValueError:
                        max_tokens_value = max_nb_words

                    # Slider for maximum number of tokens
                    cutoff_max_number_words = st.slider(cutoff_def, 0, max_nb_words, max_tokens_value)
                    new_key = ("number_tokens", cutoff_max_number_words, True)
                    keys.append(new_key)
                    cond_2 = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond_2)

                    conds["number_tokens"] = [cond_1, cond_2]

            if "character_repetition_ratio" in columns:
                with st.sidebar.expander("Character repetition ratio"):
                    val_repetitions_lengths = list(self.docs["character_repetition_ratio"].iloc[0].keys())
                    default_index = val_repetitions_lengths.index("10") if "10" in val_repetitions_lengths else 0
                    label_selectbox = (
                        "Length of repetitions in characters (that will influence the character repetition ratio)."
                    )
                    repetitions_length = st.selectbox(
                        label=label_selectbox,
                        options=val_repetitions_lengths,
                        index=default_index,
                    )
                    st.caption(
                        "Choosing a higher or lower number does not mean that the filtering "
                        "is stronger or weaker. Be careful, choosing a low number (below 5 for languages like English) "
                        "tends to associate a high character repetition ratio to very long documents (like book chapters), but with "
                        "few or no repetitions, simply because their length gives them more diversity, and we do "
                        "not want to discard such documents. It is generally better to increase this number, so that false "
                        "positives are very short documents (which we want to delete anyway) rather than long ones. However, "
                        "a low number can be useful for Chinese, where a character can designate a whole word."
                    )
                    self.docs["character_repetition_ratio"] = self.docs_checkpoint["character_repetition_ratio"]
                    for i in range(len(self.docs["character_repetition_ratio"])):
                        self.docs.loc[i, "character_repetition_ratio"] = self.docs.loc[i, "character_repetition_ratio"][
                            repetitions_length
                        ]

                    cutoff_def = "If the character repetition ratio of a document is higher than this number, the document is removed."

                    # Text input for character repetition ratio
                    char_repetition_input = st.text_input("Enter character repetition ratio", "1.0")
                    try:
                        char_repetition_value = float(char_repetition_input)
                    except ValueError:
                        char_repetition_value = 1.0

                    # Slider for character repetition ratio
                    cutoff_character_repetition_ratio = st.slider(cutoff_def, 0.0, 1.0, char_repetition_value, step=0.01)
                    new_key = (
                        "character_repetition_ratio",
                        cutoff_character_repetition_ratio,
                        True,
                        repetitions_length,
                    )
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["character_repetition_ratio"] = [cond]

            if "token_repetition_ratio" in columns:
                with st.sidebar.expander("Token repetition ratio"):
                    val_repetitions_lengths = list(self.docs["token_repetition_ratio"].iloc[0].keys())
                    default_index = val_repetitions_lengths.index("5") if "5" in val_repetitions_lengths else 0
                    label_selectbox = (
                        "Length of repetitions in tokens (that will influence the token repetition ratio)."
                    )
                    repetitions_length = st.selectbox(
                        label=label_selectbox,
                        options=val_repetitions_lengths,
                        index=default_index,
                    )
                    st.caption(
                        "Choosing a higher or lower number does not mean that the filtering "
                        "is stronger or weaker. Be careful, choosing a low number (like 3) could "
                        "tend to associate a high token repetition ratio to very long documents (like book chapters), but with "
                        "few or no repetitions, simply because their length gives them more diversity, and we do "
                        "not want to discard such documents. It is generally better to increase a bit this number, so that false "
                        "positives are very short documents (which we want to delete anyway) rather than long ones."
                    )
                    self.docs["token_repetition_ratio"] = self.docs_checkpoint["token_repetition_ratio"]
                    for i in range(len(self.docs["token_repetition_ratio"])):
                        self.docs.loc[i, "token_repetition_ratio"] = self.docs.loc[i, "token_repetition_ratio"][
                            repetitions_length
                        ]

                    cutoff_def = "If the token repetition ratio of a document is higher than this number, the document is removed."

                    # Text input for token repetition ratio
                    token_repetition_input = st.text_input("Enter token repetition ratio", "1.0")
                    try:
                        token_repetition_value = float(token_repetition_input)
                    except ValueError:
                        token_repetition_value = 1.0

                    # Slider for token repetition ratio
                    cutoff_word_repetition_ratio = st.slider(cutoff_def, 0.0, 1.0, token_repetition_value, step=0.01)
                    new_key = (
                        "token_repetition_ratio",
                        cutoff_word_repetition_ratio,
                        True,
                        repetitions_length,
                    )
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["token_repetition_ratio"] = [cond]

            if "special_characters_ratio" in columns:
                with st.sidebar.expander("Special characters ratio"):
                    cutoff_def = "If the special characters ratio of a document is higher than this number, the document is removed."

                    # Text input for special characters ratio
                    special_characters_input = st.text_input("Enter special characters ratio", "1.0")
                    try:
                        special_characters_value = float(special_characters_input)
                    except ValueError:
                        special_characters_value = 1.0

                    # Slider for special characters ratio
                    cutoff_special_characters_ratio = st.slider(cutoff_def, 0.0, 1.0, special_characters_value, step=0.01)
                    new_key = (
                        "special_characters_ratio",
                        cutoff_special_characters_ratio,
                        True,
                    )
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["special_characters_ratio"] = [cond]

            if "flagged_words_ratio" in columns:
                # variable to control means of input of flagged words
                upload_file = config.UPLOAD_FLAGGED_WORDS_FILE
                with st.sidebar.expander("Flagged words ratio"):
                    if upload_file:
                        # code that uses file upload, but does not work... could be due to remote server settings (TODO - check it out)
                        flagged_words_file = st.file_uploader(
                            "Upload your own list of flagged words (one per line). If there is none, the default one is used."
                        )
                        if flagged_words_file:
                            new_flagged_words = StringIO(flagged_words_file.getvalue().decode("utf-8")).read()
                            new_flagged_words = set(new_flagged_words.split("\n"))
                            self.docs["flagged_words_ratio"] = self.docs_checkpoint["flagged_words_ratio"]
                            for i in range(len(self.docs["flagged_words_ratio"])):
                                self.docs["flagged_words_ratio"].iloc[i] = Filtering.compute_flagged_words_ratio(
                                    self.docs["text"].iloc[i],
                                    self.sentencepiece_model_tok,
                                    self.param["strip_characters"],
                                    self.param["cond_words_augmentation"],
                                    self.param["words_augmentation_group_sizes"],
                                    self.param["words_augmentation_join_char"],
                                    new_flagged_words,
                                )
                    else:
                        # code that uses text input instead of file upload
                        flagged_words_file = st.text_input("Enter flagged words, separated by a comma (,), eg: hello,world.")
                        if flagged_words_file:
                            new_flagged_words = flagged_words_file
                            new_flagged_words = set(new_flagged_words.split(","))
                            self.docs["flagged_words_ratio"] = self.docs_checkpoint["flagged_words_ratio"]
                            for i in range(len(self.docs["flagged_words_ratio"])):
                                self.docs.loc[i, "flagged_words_ratio"] = Filtering.compute_flagged_words_ratio(
                                    self.docs.loc[i, "text"],
                                    self.sentencepiece_model_tok,
                                    self.param["strip_characters"],
                                    self.param["cond_words_augmentation"],
                                    self.param["words_augmentation_group_sizes"],
                                    self.param["words_augmentation_join_char"],
                                    new_flagged_words,
                                )

                    cutoff_def = (
                        "If the flagged words ratio of a document is higher than this number, the document is removed."
                    )
                    max_fwr = np.max(self.docs["flagged_words_ratio"])
                    max_fwr = float(np.ceil(max_fwr * 1000) / 1000)
                    max_fwr = 1.0 if math.isclose(max_fwr, 0.0, abs_tol=1e-9) else (max_fwr + 0.001)

                    # Text input for flagged words ratio
                    flagged_words_ratio_input = st.text_input("Enter flagged words ratio", str(max_fwr))
                    try:
                        flagged_words_ratio_value = float(flagged_words_ratio_input)
                    except ValueError:
                        flagged_words_ratio_value = max_fwr

                    # Slider for flagged words ratio
                    cutoff_flagged_words_ratio = st.slider(
                        label=cutoff_def,
                        min_value=0.000,
                        max_value=max_fwr,
                        value=flagged_words_ratio_value,
                        step=0.001,
                        format="%f",
                    )
                    new_key = ("flagged_words_ratio",cutoff_flagged_words_ratio, True)
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["flagged_words_ratio"] = [cond]

            if "stopwords_ratio" in columns:
                with st.sidebar.expander("Stop words ratio"):
                    stopwords_file = st.file_uploader(
                        "Upload your own list of stop words (one per line). If there is none, the default one is used."
                    )
                    if stopwords_file:
                        new_stopwords = StringIO(stopwords_file.getvalue().decode("utf-8")).read()
                        new_stopwords = set(new_stopwords.split("\n"))
                        self.docs["stopwords_ratio"] = self.docs_checkpoint["stopwords_ratio"]
                        for i in range(len(self.docs["stopwords_ratio"])):
                            self.docs.loc[i, "stopwords_ratio"] = Filtering.compute_stopwords_ratio(
                                self.docs.loc[i, "text"],
                                self.sentencepiece_model_tok,
                                self.param["strip_characters"],
                                self.param["cond_words_augmentation"],
                                self.param["words_augmentation_group_sizes"],
                                self.param["words_augmentation_join_char"],
                                new_stopwords,
                            )
                    else:
                        # code that uses text input instead of file upload
                        stopwords_input = st.text_input(
                            "Enter stop words, separated by a comma (,), eg: the,and,of."
                        )
                        if stopwords_input:
                            new_stopwords = set(stopwords_input.split(","))
                            self.docs["stopwords_ratio"] = self.docs_checkpoint["stopwords_ratio"]
                            for i in range(len(self.docs["stopwords_ratio"])):
                                self.docs.loc[i, "stopwords_ratio"] = Filtering.compute_stopwords_ratio(
                                    self.docs.loc[i, "text"],
                                    self.sentencepiece_model_tok,
                                    self.param["strip_characters"],
                                    self.param["cond_words_augmentation"],
                                    self.param["words_augmentation_group_sizes"],
                                    self.param["words_augmentation_join_char"],
                                    new_stopwords,
                                )

                    cutoff_def = (
                        "If the stop words ratio of a document is lower than this number, the document is removed."
                    )

                    # Text input for stop words ratio
                    stopwords_ratio_input = st.text_input("Enter stop words ratio", "0.0")
                    try:
                        stopwords_ratio_value = float(stopwords_ratio_input)
                    except ValueError:
                        stopwords_ratio_value = 0.0

                    # Slider for stop words ratio
                    cutoff_stopwords_ratio = st.slider(cutoff_def, 0.0, 1.0, stopwords_ratio_value, step=0.01)
                    new_key = ("stopwords_ratio",cutoff_stopwords_ratio, False)
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["stopwords_ratio"] = [cond]

            if "lang_id_score" in columns:
                with st.sidebar.expander("Language ID confidence score"):
                    cutoff_def = "If the confidence score for the language identification prediction of a document is lower than this number, the document is removed."

                    # Text input for language ID confidence score
                    lang_id_score_input = st.text_input("Enter language ID confidence score", "0.0")
                    try:
                        lang_id_score_value = float(lang_id_score_input)
                    except ValueError:
                        lang_id_score_value = 0.0

                    # Slider for language ID confidence score
                    cutoff_lang_id_score = st.slider(cutoff_def, 0.0, 1.0, lang_id_score_value, step=0.01)
                    new_key = ("lang_id_score", cutoff_lang_id_score, False)
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2])
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["lang_id_score"] = [cond]

            if "perplexity_score" in columns:
                with st.sidebar.expander("Perplexity score"):
                    cutoff_def = (
                        "If the perplexity score of a document is higher than this number, the document is removed."
                    )
                    if config.USE_MAX_PERPLEXITY:
                        max_pp = int(np.max(self.docs["perplexity_score"])) + 1
                    else:
                        max_pp = config.USER_DEF_MAX_PERPLEXITY

                    # Text input for perplexity score
                    perplexity_score_input = st.text_input("Enter perplexity score", str(max_pp))
                    try:
                        perplexity_score_value = int(perplexity_score_input)
                    except ValueError:
                        perplexity_score_value = max_pp

                    # Slider for perplexity score
                    cutoff_perplexity_score = st.slider(cutoff_def, 0, max_pp, perplexity_score_value)
                    new_key = ("perplexity_score",cutoff_perplexity_score, True)
                    keys.append(new_key)
                    Visualization_for_lang.plot_hist(self.docs, new_key)
                    cond = get_cond(new_key[0], new_key[1], new_key[2], max_pp=max_pp)
                    Visualization_for_lang.print_discarded_by_cond(cond)
                    conds["perplexity_score"] = [cond]

            return keys, conds

        with st.expander(f"Filtering on documents, for {self.num_docs} {self.lang} documents"):
            st.header(f"Filtering on documents, for {self.num_docs} {self.lang} documents")

            if "labels" in list(self.docs):
                chosen_label = st.selectbox(
                    label="Consider only documents that include the following label",
                    options=[
                        "All",
                        "NA: Narrative",
                        "IN: Informational Description",
                        "OP: Opinion",
                        "ID: Interactive Discussion",
                        "HI: How-to/Instruction",
                        "IP: Informational Persuasion",
                        "LY: Lyrical",
                        "SP: Spoken",
                    ],
                )
                chosen_label = chosen_label.split(":")[0]
                if chosen_label != "All":
                    cond_label = list(self.docs["labels"].apply(lambda x: True if chosen_label in x else False))
                    self.docs = self.docs[cond_label]

            if self.docs.empty:
                st.markdown("No document to display, please try to select a different label.")
                self.keys = []
                self.parameters = []

            else:
                st.sidebar.subheader("Parameters of the filtering on documents")
                self.keys, conds = set_sliders()
                self.parameters = self.keys * 1

                all_conds = [subcond for cond in list(conds.values()) for subcond in cond]
                all_conds = np.all(all_conds, axis=0)

                Visualization_for_lang.display_dataset(self.docs, np.invert(all_conds), "Discarded documents", "docs", data_editor_id="discarded_docs", data_id="discarded_docs_data", on_annotation_change_fn=self.data_editor_on_change)

                # st.subheader("Display discarded documents by filter")
                display_discarded_documents_by_filter = st.checkbox("Display discarded documents by filter")

                if display_discarded_documents_by_filter:
                    columns = list(self.docs)

                    if "number_tokens" in columns:
                        cond_filter = np.invert(np.all(conds["number_tokens"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the number of words",
                            "docs",
                        )

                    if "character_repetition_ratio" in columns:
                        cond_filter = np.invert(np.all(conds["character_repetition_ratio"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the character repetition ratio",
                            "docs",
                        )

                    if "token_repetition_ratio" in columns:
                        cond_filter = np.invert(np.all(conds["token_repetition_ratio"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the token repetition ratio",
                            "docs",
                        )

                    if "special_characters_ratio" in columns:
                        cond_filter = np.invert(np.all(conds["special_characters_ratio"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the special characters ratio",
                            "docs",
                        )

                    if "stopwords_ratio" in columns:
                        cond_filter = np.invert(np.all(conds["stopwords_ratio"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the stop words ratio",
                            "docs",
                        )

                    if "flagged_words_ratio" in columns:
                        cond_filter = np.invert(np.all(conds["flagged_words_ratio"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the flagged words ratio",
                            "docs",
                        )

                    if "lang_id_score" in columns:
                        cond_filter = np.invert(np.all(conds["lang_id_score"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the language identification confidence score",
                            "docs",
                        )

                    if "perplexity_score" in columns:
                        cond_filter = np.invert(np.all(conds["perplexity_score"], axis=0))
                        Visualization_for_lang.display_dataset(
                            self.docs,
                            cond_filter,
                            "Discarded documents for the filter on the perplexity score",
                            "docs",
                        )
                
                Visualization_for_lang.display_dataset(self.docs, all_conds, "Retained documents", "docs", data_editor_id="retained_docs", data_id="retained_docs_data", on_annotation_change_fn=self.data_editor_on_change)

            st.header("Download data")

            with open(self.path_data) as json_file:
                btn = st.download_button(
                    label="Download data as json",
                    data=json_file,
                    file_name="data.json",
                )

    def filtering_of_words(self):
        if not (self.words is None):
            columns = list(self.words)

            st.sidebar.subheader("Parameter of the filtering on words")

            conds_words = {}

            if "len_word" in columns:
                with st.sidebar.expander("Length of words"):
                    cutoff_def = "If the length of a word is higher than this number, the word is removed."
                    max_len_word = min(int(np.max(self.words["len_word"])) + 1, 200)
                    cutoff_word = st.slider(cutoff_def, 0, max_len_word, max_len_word)
                    new_key = ("len_word", cutoff_word, True)
                    self.parameters.append(new_key)
                    Visualization_for_lang.plot_hist(self.words, new_key)
                    cond_len_words = self.words["len_word"] <= cutoff_word
                    Visualization_for_lang.print_discarded_by_cond(cond_len_words)
                    conds_words["len_word"] = cond_len_words

            if "incorrect_substrings" in columns:
                with st.sidebar.expander("Words with incorrect substrings"):
                    incorrect_substrings = st.checkbox("Remove words with incorrect substrings.")
                    self.parameters.append(("incorrect_substrings", incorrect_substrings))

                    checkbox = st.checkbox(
                        "Diplay distribution",
                        value=True,
                        key="display_distribution_incorrect_substrings",
                    )
                    if checkbox:
                        incor_sub = np.array(self.words["incorrect_substrings"]) * 1
                        with_incor_sub = np.sum(incor_sub)
                        without_incor_sub = len(incor_sub) - with_incor_sub
                        st.markdown(f"Number of words with incorrect substrings: {with_incor_sub}")
                        st.markdown(f"Number of words without incorrect substrings: {without_incor_sub}")

                    if incorrect_substrings:
                        cond_incorrect_substrings = np.invert(self.words["incorrect_substrings"])
                    else:
                        cond_incorrect_substrings = np.array(
                            [True for i in range(len(self.words["incorrect_substrings"]))]
                        )
                    Visualization_for_lang.print_discarded_by_cond(cond_incorrect_substrings)
                    conds_words["incorrect_substrings"] = cond_incorrect_substrings

            all_conds_words = np.all(list(conds_words.values()), axis=0)

            with st.expander(f"Filtering on words, for {self.num_docs_for_words} {self.lang} documents"):
                st.header(f"Filtering on words, for {self.num_docs_for_words} {self.lang} documents")

                st.markdown(
                    f"Since the number of words is way larger than the number of documents, "
                    f"we consider in this section words for only {self.num_docs_for_words} documents."
                )

                Visualization_for_lang.display_dataset(
                    self.words, np.invert(all_conds_words), "Discarded words", "words"
                )

                # st.subheader("Display discarded words by filter")
                display_discarded_words_by_filter = st.checkbox("Display discarded words by filter")

                if display_discarded_words_by_filter:

                    if "len_word" in columns:
                        cond_filter = np.invert(conds_words["len_word"])
                        Visualization_for_lang.display_dataset(
                            self.words,
                            cond_filter,
                            "Discarded words for the filter on length",
                            "words",
                        )

                    if "incorrect_substrings" in columns:
                        cond_filter = np.invert(conds_words["incorrect_substrings"])
                        Visualization_for_lang.display_dataset(
                            self.words,
                            cond_filter,
                            "Discarded words for the filter on incorrect substrings",
                            "words",
                        )

                Visualization_for_lang.display_dataset(self.words, all_conds_words, "Retained words", "words")

    def filtering_of_sentences(self):
        def set_sliders():
            columns = list(self.sentences)
            keys = []
            conds = {}

            def get_cond(key, cutoff, max_cutoff, max_pp):
                if max_cutoff:
                    return self.sentences[key] <= min(cutoff, max_pp)
                return self.sentences[key] >= cutoff

            with st.sidebar.expander("Perplexity score"):
                cutoff_def = (
                    "If the perplexity score of a document is higher than this number, the document is removed."
                )
                if config.USE_MAX_PERPLEXITY:
                    max_pp = int(np.max(self.docs["perplexity_score"])) + 1
                else:
                    max_pp = config.USER_DEF_MAX_PERPLEXITY
                cutoff_perplexity_score = st.slider(cutoff_def, 0, max_pp, max_pp)
                new_key = ("ppl", cutoff_perplexity_score, True)
                keys.append(new_key)
                Visualization_for_lang.plot_hist(self.sentences, new_key)
                cond = get_cond(new_key[0], new_key[1], new_key[2], max_pp)
                Visualization_for_lang.print_discarded_by_cond(cond)
                conds["ppl"] = [cond]

            return keys, conds

        st.sidebar.subheader("Parameters of the filtering on sentences")

        keys, conds = set_sliders()
        # self.parameters = keys * 1

        all_conds = [subcond for cond in list(conds.values()) for subcond in cond]
        all_conds = np.all(all_conds, axis=0)

        with st.expander(f"Filtering on sentences, for {self.num_docs_for_sents} {self.lang} documents"):
            st.header(f"Filtering on sentences, for {self.num_docs_for_sents} {self.lang} documents")

            Visualization_for_lang.display_dataset(self.sentences, np.invert(all_conds), "Discarded sentences", "sents")

            Visualization_for_lang.display_dataset(self.sentences, all_conds, "Retained sentences", "sents")

    def download_parameters(self):
        st.sidebar.subheader("Download parameters")
        btn = st.sidebar.download_button(
            label="Download current parameters as json",
            data=json.dumps(self.parameters),
            file_name=f"parameters_{self.lang_dataset_id}.json",
        )

    """
    def plot_zipf_law(self):
        if not (self.words is None):
            st.header("Zipf's Law")

            display_zipf_law = st.checkbox("Display Zipf's Law")

            if display_zipf_law:

                freq_words = {}
                for _, row in self.words.iterrows():
                    freq_words[row["word"]] = freq_words.get(row["word"], 0) + 1
                freq_words = np.array(list(freq_words.values()))
                freq_words = -np.sort(-freq_words)

                fig, ax = plt.subplots()
                ax.loglog(freq_words)
                ax.set_title("Zipf's Law")
                ax.set_xlabel("$i$-th most frequent word")
                ax.set_ylabel("frequency in the documents")
                st.pyplot(fig)
    """

    def analyse_personal_doc(self):
        with st.expander("Analyse your own document"):
            st.header("Analyse your own document")

            personal_doc = st.text_area(
                label="Paste here the document you want to analyse",
                value="",
                max_chars=10000,
            )

            is_discarded = False

            def is_doc_discarded(key, score):
                if key[2]:  # max cutoff
                    return score > key[1]
                else:
                    return score < key[1]

            if personal_doc:

                st.markdown("Statistics of the document:")

                for key in self.keys:
                    if key[0] == "number_tokens":
                        words = ModifyingDocuments.get_words_from_document(
                            personal_doc,
                            self.sentencepiece_model_tok,
                            lower_case=False,
                            strip_characters=self.param["strip_characters"],
                        )
                        if key[2]:
                            st.markdown(f"Number of words: {len(words)}")
                        if is_doc_discarded(key, len(words)):
                            is_discarded = True

                    elif key[0] == "character_repetition_ratio":
                        character_repetition_ratio = Filtering.compute_character_repetition_ratio(
                            personal_doc, int(key[3])
                        )
                        character_repetition_ratio = round(character_repetition_ratio, 3)
                        st.markdown(f"Character repetition ratio: {character_repetition_ratio}")
                        if is_doc_discarded(key, character_repetition_ratio):
                            is_discarded = True

                    elif key[0] == "token_repetition_ratio":
                        word_repetition_ratio = Filtering.compute_word_repetition_ratio(
                            personal_doc,
                            self.sentencepiece_model_tok,
                            self.param["strip_characters"],
                            int(key[3]),
                        )
                        word_repetition_ratio = round(word_repetition_ratio, 3)
                        st.markdown(f"Token repetition ratio: {word_repetition_ratio}")
                        if is_doc_discarded(key, word_repetition_ratio):
                            is_discarded = True

                    elif key[0] == "special_characters_ratio":
                        special_characters_ratio = Filtering.compute_special_characters_ratio(
                            personal_doc, self.param["special_characters"]
                        )
                        special_characters_ratio = round(special_characters_ratio, 3)
                        st.markdown(f"Special characters ratio: {special_characters_ratio}")
                        if is_doc_discarded(key, special_characters_ratio):
                            is_discarded = True

                    elif key[0] == "stopwords_ratio":
                        stopwords_ratio = Filtering.compute_stopwords_ratio(
                            personal_doc,
                            self.sentencepiece_model_tok,
                            self.param["strip_characters"],
                            self.param["cond_words_augmentation"],
                            self.param["words_augmentation_group_sizes"],
                            self.param["words_augmentation_join_char"],
                            self.stopwords,
                        )
                        stopwords_ratio = round(stopwords_ratio, 3)
                        st.markdown(f"Stop words ratio: {stopwords_ratio}")
                        if is_doc_discarded(key, stopwords_ratio):
                            is_discarded = True

                    elif key[0] == "flagged_words_ratio":
                        flagged_words_ratio = Filtering.compute_flagged_words_ratio(
                            personal_doc,
                            self.sentencepiece_model_tok,
                            self.param["strip_characters"],
                            self.param["cond_words_augmentation"],
                            self.param["words_augmentation_group_sizes"],
                            self.param["words_augmentation_join_char"],
                            self.flagged_words,
                        )
                        flagged_words_ratio = round(flagged_words_ratio, 3)
                        st.markdown(f"Flagged words ratio: {flagged_words_ratio}")
                        if is_doc_discarded(key, flagged_words_ratio):
                            is_discarded = True

                    elif key[0] == "lang_id_score":
                        (
                            lang_pred_dataset_id,
                            lang_id_score,
                        ) = Filtering.compute_lang_id_pred_score(personal_doc, self.model_lang_id)
                        lang_id_score = round(lang_id_score, 3)
                        st.markdown(f"Language identification confidence score: {lang_id_score}")
                        if is_doc_discarded(key, lang_id_score) or (self.lang_dataset_id != lang_pred_dataset_id):
                            is_discarded = True

                    elif key[0] == "perplexity_score":
                        perplexity_score = Filtering.compute_perplexity_score(
                            personal_doc,
                            self.sentencepiece_model,
                            self.kenlm_model,
                        )
                        perplexity_score = round(perplexity_score, 3)
                        st.markdown(f"Perplexity score: {perplexity_score}")
                        if is_doc_discarded(key, perplexity_score):
                            is_discarded = True

                is_discarded = "" if is_discarded else "not "
                st.markdown(f"With the current filtering parameters, this document **is {is_discarded}discarded**.")

    def visualization_for_lang(self):
        self.set_title()
        self.open_data()
        self.filtering_of_docs()
        self.download_parameters()
        self.analyse_personal_doc()


class Visualization:
    def __init__(self, path_instructions):
        self.path_instructions = path_instructions

    def preamble(self):
        def get_binary_file_downloader_html(bin_file, file_label="File"):
            with open(bin_file, "rb") as f:
                data = f.read()
            bin_str = base64.b64encode(data).decode()
            href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">{file_label}</a>'
            return href

        st.markdown(
            "Before diving into this demo, you might want to take a look at how the filtering pipeline looks like in more detail in this "
            + get_binary_file_downloader_html(
                self.path_instructions,
                "pdf",
            )
            + ".",
            unsafe_allow_html=True,
        )

    def warning_preamble(self):
        st.markdown(
            "This demo can be a little slow, and only allows you to process up to 5000 documents "
            "for a decent speed. If you want to display up to three times more documents and have "
            "a faster visualization, we invite you to run this "
            "[code](https://github.com/bigscience-workshop/data_tooling/tree/master/ac_dc/visualization) "
            "on your computer."
        )

    def file_select_on_change(self):
        # clear annotation state when a new file is selected
        if "annotation_data" in st.session_state:
            del st.session_state.annotation_data
        
    def choose_lang(self):
        options = config.FILES_IN_GENERATED_SIGNALS_DIR
        file_chosen = st.selectbox("Select the file for visualization", options, on_change=self.file_select_on_change)

        if file_chosen != "None":
            file_chosen_value = file_chosen.split('/')[-1]
            file_chosen_dataset_id = file_chosen_value[0:2]

            if file_chosen_dataset_id not in config.LANG_IDS:
                config.LANG_IDS.append(file_chosen_dataset_id)
            st.session_state.file_chosen = file_chosen


    def visualization(self):
        # Check if the language has been selected
        if 'file_chosen' in st.session_state:
            file_chosen = st.session_state.file_chosen
            # ensure that sub folder does not affect the loading of file
            file_chosen_value = file_chosen.split('/')[-1]
            # set the language data set in readme
            lang_dataset_id = file_chosen_value[0:2]

            # Exit if the file is not valid
            if not file_chosen.endswith('.json'):
                st.error("The selected file is not a valid JSON file.")

            # Load your parameters based on the selected language
            if lang_dataset_id in config.LANGS_SET:
                kenlm_path = config.KENLM_PATH
                path_fasttext_model = config.FASTTEXT_MODEL_PATH
                path_sentencepiece_model = os.path.join(kenlm_path, f"{lang_dataset_id}.sp.model")
                path_kenlm_model = os.path.join(kenlm_path, f"{lang_dataset_id}.arpa.bin")

                # Check if the FastText model exists
                if not os.path.exists(path_fasttext_model):
                    raise FileNotFoundError(f"FastText model not found at {path_fasttext_model}.")

                # Check if the SentencePiece model exists
                if not os.path.exists(path_sentencepiece_model):
                    raise FileNotFoundError(f"SentencePiece model not found at {path_sentencepiece_model}.")

                # Check if the KenLM model exists
                if not os.path.exists(path_kenlm_model):
                    raise FileNotFoundError(f"KenLM model not found at {path_kenlm_model}.")

                # If all models are found, continue setting parameters
                visualization_for_lang = Visualization_for_lang(
                    path_data=os.path.join(config.GENERATED_SIGNALS_DIR, file_chosen),
                    lang=langs_id.loc[langs_id["dataset_id"]== lang_dataset_id, "lang"].iloc[0],
                    num_docs=config.NUM_DATA_SAMPLES,
                    num_docs_for_words=config.NUM_DATA_SAMPLES,
                    max_len_text_display=10000,
                    lang_dataset_id=lang_dataset_id,
                    path_fasttext_model=path_fasttext_model,
                    path_sentencepiece_model=path_sentencepiece_model,
                    path_kenlm_model=path_kenlm_model,
                )
                visualization_for_lang.visualization_for_lang()
            else:
                st.error(f"Please use a correct lang_id: {lang_dataset_id}")

        
def load_visualization():
    path_instructions = config.INSTRUCTIONS_PDF_PATH
    visualization_instance = Visualization(path_instructions)
    visualization_instance.choose_lang()
    visualization_instance.visualization()
    
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    load_visualization() 
    
    
