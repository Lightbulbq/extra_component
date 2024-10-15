import os
from pathlib import Path


def count_lines(file_path):
    """
    Helper function to count number of lines in a text file
    """
    return sum(1 for _ in Path(file_path).open())


# Directory definitions
ROOT_DIR = os.getcwd()
BASE_DIR = os.path.join(ROOT_DIR, "visualization")
DATA_DIR = os.path.join(ROOT_DIR, "data", "datasets")
GENERATED_SIGNALS_DIR = os.path.join(ROOT_DIR, "data", "generated_signals")

# Data path
TRAIN_DATA_PATH = os.path.join(DATA_DIR, "small_8days_dedup.jsonl")

# Path to the stopwords directory
STOPWORDS_PATH = os.path.join(ROOT_DIR, "data", "stopwords", "raw")

# Path to the instructions pdf
INSTRUCTIONS_PDF_PATH = os.path.join(BASE_DIR, "note", "explanation_filtering_pipeline.pdf")

# Paths to KenLM models, note that 2 distinct groups of languages use different wikipedia sources
LANGS_SET = ["en", "id", "km", "lo", "ms", "my", "ta", "th", "tl", "vi", "zh"]
KENLM_PATH = os.path.join(ROOT_DIR, "models", "kenlm")
# KENLM_PATH_2 = KENLM_PATH_1

# Path to fasttext model (for language identification)
FASTTEXT_MODEL_PATH = os.path.join(ROOT_DIR, "models", "lid.176.bin")

# Defines number of samples to visualize. Use count_lines if you want the maximum, else you can set smaller numbers. Note that if VISUALIZE_WHOLE_DOCUMENTS is false, this refers to the lines of the documents as samples
NUM_DATA_SAMPLES = count_lines(TRAIN_DATA_PATH) # uncomment for all documents/lines

# Defines the language ID - this label is used to choose kenlm model and stopwords list
LANG_IDS = ["en"]  # possibilities from set: {'zh', 'ms', 'my', 'th', 'lo', 'km', 'ta'}

# Defines the key for the text in the json file
KEY_FOR_TEXT = "raw_content"  # possibilities from set: {raw_content, paragraphs}

# Defines the method used to visualize the whole documents - either you want to visualize the whole documents or you want to visualize lines of the documents
VISUALIZE_WHOLE_DOCUMENTS = True

# Defines the method used to upload the flagged words file - either you want to upload the flagged words file or you want to use the prompt to input the flagged words
UPLOAD_FLAGGED_WORDS_FILE = False

# Defines the method used to display selected columns (quality signals) in the main area - either you want to hide the selected columns from the whole set or you want to show only the selected columns
USE_HIDE_SELECTED_COLS_METHOD = True
SELECTED_COLS = ["stopwords_ratio"]

# Flag for generating stopwords_ratio as a signal, requires a re-run of get_data_for_visualization
ENABLE_STOPWORDS_RATIO = False 

# Options for setting the maximum perplexity score
USE_MAX_PERPLEXITY = False
USER_DEF_MAX_PERPLEXITY = 5000