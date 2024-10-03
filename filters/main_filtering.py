"""Filtering."""

from multiprocessing import cpu_count
import os
import argparse
import glob

from datasets import load_dataset, Features, Value, load_from_disk

from filtering import DatasetFiltering
from parameters_filtering import parameters_filtering

import json
from os.path import join as pjoin

def check_num_proc(num_proc: int = -1) -> int:
    """
    Check the number of processors. Return a safe-checked value.

    Parameters
    ----------
    num_proc : int, optional
        Number of processors to use, by default -1

    Returns
    -------
    int
        Number of processors to use

    Raises
    ------
    ValueError
        If the input exceeds the number of processors available
    """
    maximum: int = cpu_count()
    if num_proc > maximum:
        raise ValueError(
            f"{num_proc} exceeds the maximum number ({maximum}) of processors"
        )

    if num_proc == -1:
        num_proc = maximum
        print(f"Using {num_proc} processors")
    else:
        print(f"Using {num_proc} processors out of {maximum} can be slow")

    return num_proc


def parseArgs():
    parser = argparse.ArgumentParser(description="Filtering.")
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="oscar",
        help="Name of the dataset to load.",
    )
    parser.add_argument(
        "--config_name",
        type=str,
        default=None,
        help="Name of the dataset config to pass.",
    )
    parser.add_argument(
        "--data_files",
        type=str,
        default=None,
        help="'load_dataset' returns all files that match the Unix style pattern passed by 'data_files'",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Split of the dataset to consider.",
    )
    parser.add_argument(
        "--lang_dataset_id",
        type=str,
        default="af",
        help="ID of the language in which the dataset is written.",
    )
    parser.add_argument(
        "--path_fasttext_model",
        type=str,
        default="ac_dc/lid.176.bin", # Automated Classification & Dataset Curation
        help="Path to the Fasttext model used for language identification.",
    )
    parser.add_argument(
        "--path_sentencepiece_model",
        type=str,
        default="ac_dc/af.sp.model",
        help="Path to the Sentence Piece model used to tokenize text for perplexity scores.",
    )
    parser.add_argument(
        "--path_kenlm_model",
        type=str,
        default="ac_dc/af.arpa.bin",
        help="Path to the KenLM model used to compute perplexity scores.",
    )
    parser.add_argument(
        "--max_len_prefilter",
        type=int,
        default=None,
        help="Maximum length of documents to keep. Longer documents might crash the pipeline.",
    )
    parser.add_argument(
        "--remove_meta",
        action="store_true",
        help="Only keep text and id column in dataset.",
    )
    parser.add_argument(
        "--num_proc",
        type=int,
        default=-1,
        help="Number of processes for multiprocessing. Default at the number of processors available.",
    )
    parser.add_argument(
        "--path_dir_save_dataset",
        type=str,
        default="../dataset_filtered/",
        help="Path to the directory where the filtered version of the dataset will be saved.",
    )

    ### NGAN add more
    parser.add_argument(
        "--do_train",
        action="store_true",
        help="Process train or validation",
    )

    args = parser.parse_args()
    return args

def process_each_subset(args, data_type, data_files):
    dataset = load_dataset(
        'json', 
        data_files=data_files,
        split=data_type,
        # split=f"{data_type}[:1000]",
        # streaming=True,
        # field=['id', 'text'],
        # features=data_features
    )

    if args.remove_meta:
        dataset = dataset.remove_columns([column for column in dataset.column_names if column not in ["text", "id"]])

    print("Filtering too-long documents") # OK
    if args.max_len_prefilter is not None:
        dataset = dataset.filter(lambda x: len(x["text"]) < args.max_len_prefilter,
                                 num_proc=check_num_proc(args.num_proc))
    print("Too-long documents filtered")

    dataset_filtering = DatasetFiltering(
        dataset=dataset,
        lang_dataset_id=args.lang_dataset_id,
        path_fasttext_model=args.path_fasttext_model,
        path_sentencepiece_model=args.path_sentencepiece_model,
        path_kenlm_model=args.path_kenlm_model,
        num_proc=check_num_proc(args.num_proc),
        path_dir_save_dataset=f"{args.path_dir_save_dataset}/{args.lang_dataset_id}/{data_type}",
        # path_dir_save_dataset=args.path_dir_save_dataset,
    )


    print("Modifying documents") # QUITE OK
    dataset_filtering.modifying_documents()
    print("Modifying step done")

    print("Filtering documents") # STILL HAVE MANY GAMBLING ARTICLES -> modify
    dataset_filtering.filtering()
    print("Filtering step done")
    print(len(dataset_filtering.ds))

    print("Saving dataset")
    dataset_filtering.save_dataset()
    print("Dataset saved")

    # save data params
    params = parameters_filtering[args.lang_dataset_id] 
    params_copy = params.copy()
    del params_copy['strip_characters']
    del params_copy['special_characters']
    print(params_copy)


    with open(f'{args.path_dir_save_dataset}/{args.lang_dataset_id}/params.json', 'w') as f:
        json.dump(params_copy, f, indent=4)

def main():
    args = parseArgs()

    # set exception for Tagalog/Filipino
    if args.lang_dataset_id == 'tl':
        lang_dataset_id = 'fil'
    else:
        lang_dataset_id = args.lang_dataset_id


    # list dir
    data_root_path = '/data/projects/11003280/vault/data/c4/multilingual_3.10'
    f_dirs = glob.glob(f"{data_root_path}/c4-{lang_dataset_id}.*.json")
    # print(f_dirs)

    data_files = {
        'validation': {'validation': f'{data_root_path}/c4-{lang_dataset_id}-validation.*.json'},
        # 'val_debug': {'val_debug': f'{data_root_path}/c4-{args.lang_dataset_id}-validation.*.json'},
    }


    if args.do_train:
        for f_d in f_dirs:
            f_name = 'train_' + f_d.split("/")[-1].split(".")[1].replace('-', '_')
            # print(f_d)
            file_subset = {f_name: [f_d]}
            data_files[f_name] = file_subset

    ##############
    # num_of_files_per_set = 4

    # for i in range(len(f_dirs)//num_of_files_per_set + 1):
    #     file_subset = f_dirs[i*num_of_files_per_set:(i+1)*num_of_files_per_set]

    #     if len(file_subset) == 0:
    #         continue

    #     data_files[f'train_subset_{i}'] = {
    #         f'train_subset_{i}': file_subset
    #     }

    # process_each_subset(args, 'validation', data_files['validation'])
    ##############


    # DONE_LIST = [
    # ]

    import os
    DONE_LIST = os.listdir(f'data/mC4_3.1.0/cleaned_and_filtered/{args.lang_dataset_id}/')
    # DONE_LIST = []
    # print('hiii')
    # print(DONE_LIST)
    # exit()
    MISS_LIST = [
        'train_00880_00881_00882_00883_00884_00885_00886_00887',

    ]

    for k, v in data_files.items():
        # if k in DONE_LIST :
        #     continue
        # print(k)
        if k not in MISS_LIST:
            continue
        print(f'Process {args.lang_dataset_id} {k}')
        process_each_subset(args, k, v)
        # break


if __name__ == "__main__":
    main()
