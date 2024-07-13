import os
import pandas as pd


def process_file(f) -> pd.DataFrame:
    df = pd.read_csv(f)
    # sort by start ascending, then reset index
    df = df.sort_values(by='start').reset_index(drop=True)

    # print if a file has null values
    if df.isnull().values.any():
        print(df['file_name'][0] + " has null values")

    return df


def main():

    stage_no = 3

    # directory paths
    input_path = f"../data/stage_{stage_no - 1}_processed/csvs/"
    output_path = "../data/final_dataset/"
    index_file_path = "../data/indexed/index.tsv"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)

            df.to_csv(os.path.abspath(output_path + "csvs/" + filename), index=False)

    # make a copy of the index file
    with open(os.path.abspath(index_file_path)) as f:
        df = pd.read_csv(f, sep='\t')
        df.to_csv(os.path.abspath(output_path + "index.tsv"), sep='\t', index=False)


if __name__ == '__main__':
    main()
