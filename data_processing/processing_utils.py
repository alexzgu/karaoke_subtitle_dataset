import pandas as pd
import re
import ast


def convert_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the string timestamps 'start' and 'end' columns to seconds elapsed (float) with 3 decimal places.
    :param df: df with 'start' and 'end' columns (strings)
    :return: df with modified 'start' and 'end' columns (now floats)
    """
    # convert 'start' and 'end' columns to Timedelta
    df['start'] = pd.to_timedelta(df['start'])
    df['end'] = pd.to_timedelta(df['end'])

    # convert Timedelta to total seconds with 3 decimal places
    df['start'] = df['start'].dt.total_seconds().round(3)
    df['end'] = df['end'].dt.total_seconds().round(3)

    return df


def unformatted(text: str) -> str:
    """
    :param text:
    :return: text with all <> tags removed
    """
    return re.sub(r'<[^>]*>', '', text)


def create_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates the 'segments' column, which is a list of tuples (segment label, segment text).
    :param df: df with 'text' column
    :return: modified df with 'segments' column
    """
    df['segments'] = df['text'].apply(lambda x: x.split('</c>'))

    df['segments'] = df['segments'].apply(
        lambda x: [(int(re.search(r'<(\d+)>', i).group(1)), re.sub(r'<\d+>', '', i)) if re.search(r'<\d+>', i)
                   else (i, '') for i in x if i != ''])

    # filter out any segments with empty text
    df['segments'] = df['segments'].apply(lambda x: [i for i in x if i[1] != ''])

    return df


def convert_segments_to_tuples(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the 'segments' column from string to list of tuples.
    Needed if segments are stored in an intermediate file that is read later.
    :param df: with 'segments' column
    :return: modified df with 'segments' column as list of tuples
    """
    def string_to_tuple_list(segment_str):
        return ast.literal_eval(segment_str)

    df['segments'] = df['segments'].apply(string_to_tuple_list)

    return df


def compute_ref_start_end(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assumes dataframe is sorted unformatted ascending, start descending.
    Adds 'ref_start' and 'ref_end' columns to the df.
    :param df: with 'unformatted' column
    :return: modified df with 'ref_start' and 'ref_end' columns
    """
    df['ref_start'] = (df['unformatted'] != df['unformatted'].shift(1)) | (df['line'] != df['line'].shift(1))
    df['idx_diff'] = df['line'] != df['line'].shift(-1)
    df.loc[0, 'ref_start'] = True  # first row

    df['ref_end'] = df['ref_start'].shift(-1)
    df.loc[df.index[-1], 'ref_end'] = True  # last row

    return df


def clean_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes all instances of <> tags from every segment of the list, for all segments entries.
    :param df: with 'segments' column
    :return: modified df
    """
    # for each entry in segments, remove any instance of <> tags from every segment of the list
    df['segments'] = df['segments'].apply(lambda x: [(i[0], re.sub(r'<[^>]*>', '', i[1])) for i in x])
    return df


def create_character_segments(df):
    """
    Takes a pandas DataFrame with a 'segments' column containing lists of (string, int) tuples
    and returns a new DataFrame with each string replaced by individual characters.
    :param df:
    :return:
    """

    def replace_with_chars(segment_list):
        new_segment_list = []
        for segment in segment_list:
            color_idx, string = segment
            new_segment_list.extend([(color_idx, char) for char in string])
        return new_segment_list

    df['segments'] = df['segments'].apply(replace_with_chars)
    return df


def compare_character_segments(list_a, list_b, uwu=False):
    """
    Takes two lists of (char, int) tuples and returns a string containing the characters
    where the integer values differ between the two lists.
    :param list_a:
    :param list_b:
    :return:
    """
    i = 0
    first_idx = None
    diff_chars = []
    for (int_a, char_a), (int_b, char_b) in zip(list_a, list_b):
        i += 1
        if char_a != char_b:
            raise ValueError(f"Character mismatch bwn lists\n{list_a}\nand\n{list_b}\nat index {i} and uwu={uwu}")
        if int_a != int_b:
            if first_idx is None:
                first_idx = i
            diff_chars.append(char_a)
    if first_idx is None:
        first_idx = i
    if uwu:
        if first_idx == i:
            print(f"hmmm...\n{list_a}\nand\n{list_b}")
    return ''.join(diff_chars), first_idx


def generate_tokens(df: pd.DataFrame) -> pd.DataFrame:
    """

    :param df:
    :return:
    """
    # prev_segments column
    df['prev_segments'] = df['segments'].shift(1)
    # next_segments column
    df['next_segments'] = pd.Series(dtype=df['segments'].dtype)
    df['next_segments'] = df['segments'].shift(-1)
    # for the last row, next_segments is the same as segments
    df.loc[df.index[-1:], 'next_segments'] = df.loc[df.index[-1:], 'segments']

    def helper_token(row):
        if row['ref_start']:
            if row['ref_end']:
                # string with all characters from segments
                return ''.join([char for _, char in row['segments']])
            ref_idx = compare_character_segments(row['segments'], row['next_segments'])[1]
            if ref_idx == len(row['segments'])-1:
                return "<dupe>"

            # return a string containing everything in segments before the ref_idx
            return ''.join([char for _, char in row['segments'][ref_idx-1:]])
        else:
            return compare_character_segments(row['prev_segments'], row['segments'])[0]

    df['token'] = df.apply(helper_token, axis=1)

    return df
