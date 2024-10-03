# SEA-LION Quality Signal EDA Visualisation tool

This visualization tool is adapted from this: https://huggingface.co/spaces/huggingface/text-data-filtering.

## Getting Started
### Environment setup
1. Create the conda environment
```bash
conda env create -n [ENV_NAME] -f environment.yml

conda activate [ENV_NAME] 
``` 

2. Install the required packages
```bash
pip install -r requirements.txt
```

### Model(s) setup
1. Download the required fasttext model and place them under the `models` folder.

2. Download the required KenLM and SentencePiece models and place them under the `models/kenlm` folder. 

### Data setup 
You are expected to provide a json (or jsonl) file for the data you are visualizing.

To generate this data:

1. Place the source json (or jsonl) file in the `data/datasets` folder

2. Use data preparation scripts in `data_prep` as needed to prepare the data. Functionality includes shuffling the JSON, extracting `n` number of lines, as well as one Python script to replace double newlines (`\n\n`), which is the convention for our paragraph delimiting, to single newline (`\n`) as needed for the visualizing of lines.

3. Edit the following variables in `config.py` to define the data file you are visualizing, language, and other settings.

```
TRAIN_DATA_PATH= 
LANG_IDS=
KEY_FOR_TEXT=
```

4. Run `get_data_for_visualization.py` to do signal generation using:

    ```bash
    python data_prep/get_data_for_visualization.py
    ```

   This generates a stats file for all documents to be used by visualizer.


### Running the application

Finally, run the streamlit app by running `visualization.py`:

```bash
streamlit run visualization/visualization.py
```

