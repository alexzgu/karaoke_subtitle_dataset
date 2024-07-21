import os
from processing_utils import *


def process_file(f) -> pd.DataFrame:
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
    # df = remove_one_offs(df)
    df = create_segments(df)

    # temporary for debugging purposes
    # drop 'line', 'position', and 'text' columns
    # !!! DEBUGGING PURPOSES ONLY
    df = df.drop(columns=['line', 'position', 'text'])

    return df


def main():
    stage_no = 1
    input_path = f"../data/parsed/"
    output_path = f"../data/stage_{stage_no}_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)

            df.to_csv(os.path.abspath(output_path + filename), index=False)


if __name__ == '__main__':
    main()
