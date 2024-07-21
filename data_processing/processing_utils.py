import pandas as pd
import re
import ast
# note: df['segments'] = ast.literal_eval(df['segments'])
# will convert the string representation of a list of tuples


def filter_rows(df):
    df = df.drop_duplicates()

    # Drop rows where 'line' = -1 or 'line' >= 50
    df = df[(df['line'] != -1) & (df['line'] < 50)]

    return df


def convert_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the string timestamps 'start' and 'end' columns to seconds elapsed (float) with 3 decimal places.
    :param df: df with 'start' and 'end' columns (strings)
    :return: df with modified 'start' and 'end' columns (now floats)
    """
    # Convert 'start' and 'end' columns to Timedelta
    df['start'] = pd.to_timedelta(df['start'])
    df['end'] = pd.to_timedelta(df['end'])

    # Convert Timedelta to total seconds with 3 decimal places
    df['start'] = df['start'].dt.total_seconds().round(3)
    df['end'] = df['end'].dt.total_seconds().round(3)
    return df


def unformatted(text: str) -> str:
    return re.sub(r'<[^>]*>', '', text)


def create_segments(df: pd.DataFrame) -> pd.DataFrame:
    df['segments'] = df['text'].apply(lambda x: x.split('</c>'))

    df['segments'] = df['segments'].apply(
        lambda x: [(int(re.search(r'<(\d+)>', i).group(1)), re.sub(r'<\d+>', '', i)) if re.search(r'<\d+>', i)
                   else (i, '') for i in x if i != ''])
    return df


def sort_rows(df: pd.DataFrame) -> pd.DataFrame:
    # sort by unformatted ascending, then start descending
    return df.sort_values(by=['start', 'end']).reset_index(drop=True)
