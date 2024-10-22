from datasets import load_dataset
from tqdm import tqdm
import json
import os
import sys

# Add the parent directory to the system path to import custom modules
sys.path.insert(1, os.path.join(sys.path[0], ".."))

from filters.filtering import LoadParameters, ModifyingDocuments, Filtering
import config


class GetDataForVisualization:
    def __init__(
        self,
        dataset,
        num_iter,
        lang_dataset_id,
        path_fasttext_model,
        path_sentencepiece_model,
        path_kenlm_model,
        path_save_stats,
    ):
        """
        Initialize the GetDataForVisualization class with the given parameters.

        Parameters:
        - dataset: The dataset to be processed.
        - num_iter: Number of iterations for processing the dataset.
        - lang_dataset_id: Language dataset identifier.
        - path_fasttext_model: Path to the FastText model.
        - path_sentencepiece_model: Path to the SentencePiece model.
        - path_kenlm_model: Path to the KenLM model.
        - path_save_stats: Path to save the computed statistics.
        """
        self.ds = dataset
        self.num_iter = num_iter
        self.lang_dataset_id = lang_dataset_id

        # Load various parameters and models for language processing
        self.param = LoadParameters.load_parameters(lang_dataset_id)
        self.stopwords = LoadParameters.load_stopwords(lang_dataset_id) if config.ENABLE_STOPWORDS_RATIO else None
        self.flagged_words = LoadParameters.load_flagged_words(lang_dataset_id)
        self.model_lang_id = LoadParameters.load_model_lang_id(lang_dataset_id, path_fasttext_model)
        self.sentencepiece_model = LoadParameters.load_sentencepiece_model(lang_dataset_id, path_sentencepiece_model)
        self.sentencepiece_model_tok = self.sentencepiece_model if self.param["tokenization"] else None
        self.kenlm_model = LoadParameters.load_kenlm_model(lang_dataset_id, path_kenlm_model)
        self.path_save_stats = path_save_stats

    def compute_stats_on_lines(self):
        """
        Compute statistics on lines of text from the dataset. This function splits documents into lines and applies the filter on the lines.
        Therefore, 'docs' here refers to individual lines.
        """
        # Convert the dataset into an iterator
        dataset = iter(self.ds)
        stats = []

        # Iterate through the dataset using a progress bar
        for i in tqdm(range(self.num_iter)):
            # Get the next example from the dataset
            example = next(dataset)
            list_of_docs = example[config.KEY_FOR_TEXT]

            # Split the document into sentences (lines)
            list_of_docs = list_of_docs.split("\n")

            # Process each line (document) individually
            for document in list_of_docs:
                stats_document = {}
                # Extract words from the document using the SentencePiece model and other parameters
                words = ModifyingDocuments.get_words_from_document(
                    document,
                    sentencepiece_model_tok=self.sentencepiece_model_tok,
                    lower_case=True,
                    strip_characters=self.param["strip_characters"],
                )
                words = [
                    {
                        "len_word": len(word),
                        "incorrect_substrings": any(
                            [(i_substr in word) for i_substr in self.param["incorrect_word_substrings"]]
                        ),
                        "word": word,
                    }
                    for word in words
                ]

                if not self.param["tokenization"]:
                    stats_document["words"] = words

                # Compute number of words and put it in the stats_document dictionary
                number_words = len(words)
                stats_document["number_tokens"] = number_words

                # Compute character repetition ratios
                character_repetition_ratios = {
                    n: round(Filtering.compute_character_repetition_ratio(document, n), 4) for n in range(2, 16)
                }
                stats_document["character_repetition_ratio"] = character_repetition_ratios

                # Compute word repetition ratios
                word_repetition_ratios = {
                    n: round(
                        Filtering.compute_word_repetition_ratio(
                            document,
                            self.sentencepiece_model_tok,
                            self.param["strip_characters"],
                            n,
                        ),
                        4,
                    )
                    for n in range(3, 11)
                }
                stats_document["token_repetition_ratio"] = word_repetition_ratios

                # Compute special characters ratio
                special_characters_ratio = Filtering.compute_special_characters_ratio(
                    document, self.param["special_characters"]
                )
                stats_document["special_characters_ratio"] = special_characters_ratio

                # Compute stopwords ratio if stopwords are provided
                if self.stopwords:
                    stopwords_ratio = Filtering.compute_stopwords_ratio(
                        document,
                        self.sentencepiece_model_tok,
                        self.param["strip_characters"],
                        self.param["cond_words_augmentation"],
                        self.param["words_augmentation_group_sizes"],
                        self.param["words_augmentation_join_char"],
                        self.stopwords,
                    )
                    stats_document["stopwords_ratio"] = stopwords_ratio

                # Compute flagged words ratio if flagged words are provided
                if self.flagged_words:
                    flagged_words_ratio = Filtering.compute_flagged_words_ratio(
                        document,
                        self.sentencepiece_model_tok,
                        self.param["strip_characters"],
                        self.param["cond_words_augmentation"],
                        self.param["words_augmentation_group_sizes"],
                        self.param["words_augmentation_join_char"],
                        self.flagged_words,
                    )
                    stats_document["flagged_words_ratio"] = flagged_words_ratio

                # Compute language identification score if model is provided
                if self.model_lang_id:
                    _, lang_id_score = Filtering.compute_lang_id_pred_score(document, self.model_lang_id)
                    stats_document["lang_id_score"] = lang_id_score

                # Compute perplexity score if KenLM model is provided
                if self.kenlm_model:
                    perplexity_score = Filtering.compute_perplexity_score(
                        document, self.sentencepiece_model, self.kenlm_model
                    )
                    stats_document["perplexity_score"] = perplexity_score

                # Add the original text to the statistics
                stats_document["text"] = document
                stats.append(stats_document)

        # Save the computed statistics to a JSON file
        self.stats = stats
        with open(self.path_save_stats, "w") as f:
            json.dump(self.stats, f)

    def compute_stats(self):
        """
        Compute statistics on whole documents from the dataset.
        """
        # Convert the dataset into an iterator
        dataset = iter(self.ds)
        stats = []

        # Iterate through the dataset using a progress bar
        for i in tqdm(range(self.num_iter)):
            # Get the next example from the dataset
            example = next(dataset)
            document = example[config.KEY_FOR_TEXT]

            stats_document = {}
            # Extract words from the document using the SentencePiece model and other parameters
            words = ModifyingDocuments.get_words_from_document(
                document,
                sentencepiece_model_tok=self.sentencepiece_model_tok,
                lower_case=True,
                strip_characters=self.param["strip_characters"],
            )
            words = [
                {
                    "len_word": len(word),
                    "incorrect_substrings": any(
                        [(i_substr in word) for i_substr in self.param["incorrect_word_substrings"]]
                    ),
                    "word": word,
                }
                for word in words
            ]

            if not self.param["tokenization"]:
                stats_document["words"] = words

            # Compute number of words and put it in the stats_document dictionary
            number_words = len(words)
            stats_document["number_tokens"] = number_words

            # Compute character repetition ratios
            character_repetition_ratios = {
                n: round(Filtering.compute_character_repetition_ratio(document, n), 4) for n in range(2, 16)
            }
            stats_document["character_repetition_ratio"] = character_repetition_ratios

            # Compute word repetition ratios
            word_repetition_ratios = {
                n: round(
                    Filtering.compute_word_repetition_ratio(
                        document,
                        self.sentencepiece_model_tok,
                        self.param["strip_characters"],
                        n,
                    ),
                    4,
                )
                for n in range(3, 11)
            }
            stats_document["token_repetition_ratio"] = word_repetition_ratios

            # Compute special characters ratio
            special_characters_ratio = Filtering.compute_special_characters_ratio(
                document, self.param["special_characters"]
            )
            stats_document["special_characters_ratio"] = special_characters_ratio

            # Compute stopwords ratio if stopwords are provided
            if self.stopwords:
                stopwords_ratio = Filtering.compute_stopwords_ratio(
                    document,
                    self.sentencepiece_model_tok,
                    self.param["strip_characters"],
                    self.param["cond_words_augmentation"],
                    self.param["words_augmentation_group_sizes"],
                    self.param["words_augmentation_join_char"],
                    self.stopwords,
                )
                stats_document["stopwords_ratio"] = stopwords_ratio

            # Compute flagged words ratio if flagged words are provided
            flagged_words_ratio = 0
            if self.flagged_words:
                flagged_words_ratio = Filtering.compute_flagged_words_ratio(
                    document,
                    self.sentencepiece_model_tok,
                    self.param["strip_characters"],
                    self.param["cond_words_augmentation"],
                    self.param["words_augmentation_group_sizes"],
                    self.param["words_augmentation_join_char"],
                    self.flagged_words,
                )
            stats_document["flagged_words_ratio"] = flagged_words_ratio

            # Compute language identification score if model is provided
            if self.model_lang_id:
                _, lang_id_score = Filtering.compute_lang_id_pred_score(document, self.model_lang_id)
                stats_document["lang_id_score"] = lang_id_score

            # Compute perplexity score if KenLM model is provided
            if self.kenlm_model:
                perplexity_score = Filtering.compute_perplexity_score(
                    document, self.sentencepiece_model, self.kenlm_model
                )
                stats_document["perplexity_score"] = perplexity_score

            # Add the original text to the statistics
            stats_document["text"] = document
            stats.append(stats_document)

        # Save the computed statistics to a JSON file
        self.stats = stats
        with open(self.path_save_stats, "w") as f:
            json.dump(self.stats, f)


def get_data(lang_dataset_id):
    """
    Prepare the paths and parameters for the GetDataForVisualization class and initiate the data processing.

    Parameters:
    - lang_dataset_id: Language dataset identifier.
    """
    # Output path for saving statistics
    os.makedirs(config.GENERATED_SIGNALS_DIR, exist_ok=True)
    path_save_stats = os.path.join(config.GENERATED_SIGNALS_DIR, f"{lang_dataset_id}_examples_with_stats_sent_lvl_{config.GENERATED_SIGNALS_FILE_SUFFIX}.json")

    # Paths for language detection models
    path_fasttext_model = config.FASTTEXT_MODEL_PATH
    if lang_dataset_id in config.LANGS_SET:
        kenlm_path = config.KENLM_PATH
    else:
        print("Please use correct lang_id")
        exit()
    path_sentencepiece_model = f"{kenlm_path}/{lang_dataset_id}.sp.model"
    path_kenlm_model = f"{kenlm_path}/{lang_dataset_id}.arpa.bin"

    data_files = {
        "train": config.TRAIN_DATA_PATH,
        # "validation": "/mnt/data/nicholas/ngan_data_visualization/nscc_working/arf/cleaning_and_filtering/visualization/data/small_8days_dedup.jsonl",
        #'train': f'{data_root_path}/c4-{lang_dataset_id}.*.json',
        # 'validation': f'{data_root_path}/c4-{lang_dataset_id}-validation.*.json',
        # 'train_debug': f'{data_root_path}/c4-{lang_dataset_id}.00432-00433-00434-00435-00436-00437-00438-00439.json' # for debugging
    }
    split = "train"

    # number of documents to visualize
    num_iter = config.NUM_DATA_SAMPLES

    print(f"Start to load {lang_dataset_id} data")
    dataset = load_dataset("json", data_files=data_files, split=split, streaming=True).shuffle(
        buffer_size=num_iter, seed=42
    )
    print("Done load data - OK")

    get_data_for_visualization = GetDataForVisualization(
        dataset,
        num_iter,
        lang_dataset_id,
        path_fasttext_model,
        path_sentencepiece_model,
        path_kenlm_model,
        path_save_stats,
    )

    if config.VISUALIZE_WHOLE_DOCUMENTS:
        get_data_for_visualization.compute_stats()
    else:
        get_data_for_visualization.compute_stats_on_lines()


if __name__ == "__main__":
    # process each language
    for lang_id in config.LANG_IDS:
        get_data(lang_id)
