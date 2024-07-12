import os
import pandas as pd
import re


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
    # df['text'] = df['text'].str.replace('~', '')
    # df['text'] = df['text'].str.replace('-', '')
    # df['text'] = df['text'].str.replace('(', '')
    # df['text'] = df['text'].str.replace(')', '')

    # removes any characters that is not alphanumeric or japanese character
    # df['text'] = df['text'].str.replace(r'[^\w\sぁ-んァ-ン一-龯]', '')

    # strip all characters from the front and back of 'text' that are not alphanumeric
    # or a kana character (hiragana or katakana) (even stripping japanese punctuation)
    #df['text'] = df['text'].str.replace(r'[\w\u3040-\u309F\u30A0-\u30FF]+', '')
    def clean_string(input_str: str) -> str:
        pattern = r'[\w\u3040-\u309F\u30A0-\u30FF|]+'

        # Use re.findall to extract all matching substrings
        filtered = re.findall(pattern, input_str)

        # Join the filtered substrings to form the final cleaned string
        cleaned_str = ''.join(filtered)
        return cleaned_str
    df['text'] = df['text'].apply(clean_string)

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
