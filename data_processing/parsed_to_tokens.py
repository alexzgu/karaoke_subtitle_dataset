import os
from processing_utils import *


def process_file(f) -> pd.DataFrame or None:
    """
    Generates a dataset containing token information.

    Note that it is up to the user to do further munging.
    :param f: CSV file containing data parsed from a WebVTT file (with formatting).
    :return: A processed DataFrame containing token information.
    """
    df = pd.read_csv(f)
    # if the df has less than 3 rows, then skip it
    if len(df) < 3:
        print(f"Skipping {f.name.split('/')[-1]} because it has less than 3 rows.")
        return None

    df = df.drop_duplicates()
    # df = filter_rows(df)  # !!! NOTE that this is only for EN subtitles

    # if there are any nulls, print
    if df.isnull().values.any():
        print(f + " has null values")
        df = df.dropna(how='any', axis=0)

    df = convert_time(df)

    df['text'] = df['text'].apply(lambda x: x.replace("'", "\\'"))
    df['text'] = df['text'].str.lower()

    df['unformatted'] = df['text'].apply(unformatted)
    # drop columns where 'unformatted' is empty
    df = df[df['unformatted'] != '']

    # --------------------------------------------

    df = create_segments(df)
    # df = df.drop(columns=['line', 'position', 'text'])  # !!! DEBUGGING PURPOSES ONLY
    df = compute_counts(df)

    df = compute_common_number(df)

    df = df.drop(columns=['counts_ref', 'counts'])
    
    # --------------------------------------------

    df = clean_segments(df)

    df = create_remainders(df)
    df = collapse_similar_columns(df)

    # --------------------------------------------

    df = df.drop(columns=['segments', 'ref_start', 'ref_end', 'common_number'])
    df = rotate_remainders(df)
    df = create_tokens(df)
    df = df.drop(columns=['unformatted', 'prev_unformatted', 'remainder', 'prev_remainder'])

    # --------------------------------------------

    df = df.sort_values(by=['start', 'line'], ascending=[True, False])

    return df


def main(custom_input_directory=None, custom_output_directory=None):
    """
    Processes the parsed data and generates a dataset containing timestamped tokens.
    :param custom_input_directory: by default, will look at data/parsed/.
    :param custom_output_directory: by default, will output to data/final_dataset/.
    :return:
    """
    data_path = "../data/"
    input_path = custom_input_directory if custom_input_directory else data_path + "parsed/"
    output_path = custom_output_directory if custom_output_directory else data_path + "final_dataset/"
    index_file_path = data_path + "indexed/index.tsv"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)
            if df is None:
                continue

            # if the directory does not exist, create it
            csv_output = output_path + "/csvs/"
            if not os.path.exists(os.path.abspath(csv_output)):
                os.makedirs(os.path.abspath(csv_output))

            df.to_csv(os.path.abspath(csv_output + filename), index=False)

        # index file
        idx_path = os.path.abspath(index_file_path)
        if os.path.exists(idx_path):
            with open(idx_path) as f:
                df = pd.read_csv(f, sep='\t')
                df.to_csv(os.path.abspath(output_path + "index.tsv"), sep='\t', index=False)
        else:
            print("Index file does not exist. If this is intended, please ignore this message.")


if __name__ == '__main__':
    main(custom_input_directory=None, custom_output_directory=None)
