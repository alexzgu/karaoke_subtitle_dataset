import os
import pandas as pd


def process_file(df: pd.DataFrame) -> pd.DataFrame:
    # sort by start ascending, then reset index
    df = df.sort_values(by='start').reset_index(drop=True)

    # print if a file has null values
    if df.isnull().values.any():
        print(df['file_name'][0] + " has null values")

    df.drop(columns=['unformatted', 'start_of_new_chain', 'file_name', 'singleton'], inplace=True)

    return df


def main():

    # directory paths
    input_path = "../data/stage_3_processed/csvs/"
    output_path = "../data/final_dataset/"
    index_file_path = "../data/indexed/index.tsv"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:
            df = pd.read_csv(f)

            # processing
            df = process_file(df)

            df.to_csv(os.path.abspath(output_path + "csvs/" + filename), index=False)

    # make a copy of the index file
    with open(os.path.abspath(index_file_path)) as f:
        df = pd.read_csv(f, sep='\t')
        df.to_csv(os.path.abspath(output_path + "index.tsv"), sep='\t', index=False)


if __name__ == '__main__':
    main()
