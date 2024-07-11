import os
import pandas as pd


def convert_time(df):
    # Convert 'start' and 'end' columns to Timedelta
    df['start'] = pd.to_timedelta(df['start'])
    df['end'] = pd.to_timedelta(df['end'])

    # Convert Timedelta to total seconds with 3 decimal places
    df['start'] = df['start'].dt.total_seconds().round(3)
    df['end'] = df['end'].dt.total_seconds().round(3)
    return df


def clean_text(df):
    # Remove any '~', '-", and parentheses
    df['text'] = df['text'].str.replace('~', '')
    df['text'] = df['text'].str.replace('-', '')
    df['text'] = df['text'].str.replace('(', '')
    df['text'] = df['text'].str.replace(')', '')

    # Lowercase
    df['text'] = df['text'].str.lower()
    return df


def filter_rows(df):
    df = df.drop_duplicates()

    # Drop rows where 'line' = -1 or 'line' >= 50
    df = df[(df['line'] != -1) & (df['line'] < 50)]

    return df


def main():
    # directory paths
    input_path = "../data/parsed/"
    output_path = "../data/stage_1_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:
            df = pd.read_csv(f)

            # if there are any nulls, print
            if df.isnull().values.any():
                print(filename + " has null values")
                df = df.dropna(how='any', axis=0)

            df = filter_rows(df)
            df = convert_time(df)
            df = clean_text(df)

            df.to_csv(os.path.abspath(output_path + filename), index=False)


if __name__ == '__main__':
    main()
