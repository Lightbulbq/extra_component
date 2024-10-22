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

3. Place the source json language files/folders which start with the language you are trying to generate the signals, inside the `data/generated_signals` folder following the format `LANGS_SET = ["en", "id", "km", "lo", "ms", "my", "ta", "th", "tl", "vi", "zh"]` 
- Similar to the fomat below  e.g. `en_[name_of_file].json`: 
<img width="773" alt="Screenshot 2024-10-22 at 2 15 01 PM" src="https://github.com/user-attachments/assets/cd6906f2-1b1d-4621-9edd-1c169aed0f6e">


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

