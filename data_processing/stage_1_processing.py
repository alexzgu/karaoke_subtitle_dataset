import os
from processing_utils import *


def process_file(f) -> pd.DataFrame or None:

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

    return df


def main():
    stage_no = 1
    input_path = f"../data/parsed/"
    output_path = f"../data/stage_{stage_no}_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)

            if df is None:
                continue

            df.to_csv(os.path.abspath(output_path + filename), index=False)


if __name__ == '__main__':
    main()
