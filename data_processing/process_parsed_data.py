import os
from processing_utils import *

total_error = 0


def process_file(f, debug=False) -> pd.DataFrame:
    """
    Generates a dataset containing token information.
    
    Note that it is up to the user to do further munging.
    :param f: CSV file containing data parsed from a WebVTT file (with formatting).
    :return: A processed DataFrame containing token information.
    """
    df = pd.read_csv(f)

    # !!! note that this is only for english subtitles
    df = filter_rows(df)

    # if there are any nulls, print
    if df.isnull().values.any():
        print(f + " has null values")
        df = df.dropna(how='any', axis=0)

    df = df.drop_duplicates()
    df = convert_time(df)

    df['text'] = df['text'].apply(lambda x: x.replace("'", "\\'"))
    df['text'] = df['text'].str.lower()

    df['unformatted'] = df['text'].apply(unformatted)

    df = collapse_same_partitions(df)
    df = remove_one_offs(df)
    df = chain_labeling(df)

    df = create_remainder(df, f, debug=debug)
    df = tokenize(df, debug=debug)

    if not debug:
        df = df.drop(columns=['unformatted', 'remainder', 'start_of_new_chain', 'end_of_chain', 'singleton'])

    # sort by start ascending, then reset index
    # df = df.sort_values(by='start').reset_index(drop=True)

    # debugging --------------------------------------
    # # sort first by unformatted ascending, then by start descending
    # df = df.sort_values(by=['unformatted', 'start'], ascending=[True, False]).reset_index(drop=True)
    #
    # # Check if the first row has 'end_of_chain' = False
    # if not df.iloc[0]['end_of_chain']:
    #     print(f"File {f}: First row has 'end_of_chain' = False")
    #
    # # Check if the last row has 'start_of_new_chain' = False
    # if not df.iloc[-1]['start_of_new_chain']:
    #     print(f"File {f}: Last row has 'start_of_new_chain' = False")
    # debugging --------------------------------------

    # print if a file has any token values = ""
    if df['token'].apply(lambda x: x == "").any():
        print(f.name[f.name.find("parsed/"):] + " has token values = ''")
        global total_error
        total_error += 1

    return df


def main():
    data_path = "../data/"
    input_path = data_path + "parsed/"
    output_path = data_path + "final_dataset/"
    index_file_path = data_path + "indexed/index.tsv"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f, debug=True)

            # if the directory does not exist, create it
            csv_output = output_path + "csvs/"
            if not os.path.exists(os.path.abspath(csv_output)):
                os.makedirs(os.path.abspath(csv_output))

            df.to_csv(os.path.abspath(csv_output + filename), index=False)

        # make a copy of the index file
        with open(os.path.abspath(index_file_path)) as f:
            df = pd.read_csv(f, sep='\t')
            df.to_csv(os.path.abspath(output_path + "index.tsv"), sep='\t', index=False)

    print(f"Total errors: {total_error}")


if __name__ == '__main__':
    main()
