import os
from processing_utils import *


def process_file(f) -> pd.DataFrame:
    """
    Generates a dataset containing token information.
    
    Note that it is up to the user to do further munging.
    :param f: CSV file containing data parsed from a WebVTT file (with formatting).
    :return: A processed DataFrame containing token information.
    """
    df = pd.read_csv(f)

    # if there are any nulls, print
    if df.isnull().values.any():
        print(f + " has null values")
        df = df.dropna(how='any', axis=0)

    df = df.drop_duplicates()
    df = convert_time(df)
    df['text'] = df['text'].str.lower()

    df['unformatted'] = df['text'].apply(unformatted)
    df = collapse_same_partitions(df)
    df = remove_one_offs(df)
    df = chain_labeling(df)

    df = create_remainder(df, f)
    df = tokenize(df)
    df = df.drop(columns=['unformatted', 'remainder', 'start_of_new_chain', 'end_of_chain', 'singleton'])

    # sort by start ascending, then reset index
    df = df.sort_values(by='start').reset_index(drop=True)

    # print if a file has null values
    if df.isnull().values.any():
        print(df['file_name'][0] + " has null values")

    return df


def main():
    data_path = "../data/"
    input_path = data_path + "parsed/"
    output_path = data_path + "final_dataset/"
    index_file_path = data_path + "indexed/index.tsv"

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
