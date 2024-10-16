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
    df['time_diff'] = df['end'].sub(df['start'].shift(1)).abs().gt(0.5)
    df['unf_diff'] = df['unformatted'] != df['unformatted'].shift(1).fillna(True)
    df['line_diff'] = df['line'] != df['line'].shift(1).fillna(True)
    df['ref_start'] = (
            (df['unformatted'].ne(df['unformatted'].shift(1))) |
            (df['line'].ne(df['line'].shift(1))) |
            (df['end'].sub(df['start'].shift(1)).abs().gt(0.5)) |
            (df.index == 0)
    )
    df['ref_end'] = df['ref_start'].shift(-1)
    # set last row ref_end to True
    df.loc[df.index[-1], 'ref_end'] = True

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


def compare_character_segments(list_a, list_b):
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
            raise ValueError(f"Character mismatch bwn lists\n{list_a}\nand\n{list_b}\nat index {i}")
        if int_a != int_b:
            if first_idx is None:
                first_idx = i
            diff_chars.append(char_a)
    if first_idx is None:
        first_idx = -1
    return ''.join(diff_chars), first_idx


def generate_tokens(df: pd.DataFrame) -> pd.DataFrame:
    """

    :param df:
    :return:
    """
    # prev_segments column
    df['prev_segments'] = df['segments'].shift(1).fillna(df['segments'])
    # next_segments column
    df['next_segments'] = df['segments'].shift(-1).fillna(df['segments'])

    def helper_token(row):
        if row['ref_end']:
            if row['ref_start']: # singleton (both ref_start and ref_end)
                return ''.join([char for _, char in row['segments']])

            ref_idx = compare_character_segments(row['segments'], row['prev_segments'])[1]
            if ref_idx == -1:
                return "<dupe_ref_end>"

            # return a string containing everything in segments before the ref_idx
            output = ''.join([char for _, char in row['segments'][:ref_idx-1]])
            if output == "":
                return "<dupe_ref_end>"
            return output
        else:
            text, ref_idx = compare_character_segments(row['next_segments'], row['segments'])
            if ref_idx == -1:
                return "<dupe>"
            return text

    df['token'] = df.apply(helper_token, axis=1)

    # drop columns
    df = df.drop(columns=['prev_segments', 'next_segments', 'time_diff', 'unf_diff', 'line_diff'])

    return df


def process_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    def process_dupe_ref_end(input_row):
        ref_color = input_row['segments'][-1][0]

        idx = -1
        for color, char in input_row['segments'][::-1]:
            if color != ref_color:
                out = ''.join([char for _, char in input_row['segments'][:idx+1]])
                return "<dupe_ref_end_1>" if out == "" else out
            idx -= 1
        out = input_row['unformatted']
        return "<dupe_ref_end_2>" if out == "" else out

    # apply process_dupe_ref_end to all rows
    # with token = "<dupe_ref_end>"
    df['token'] = df.apply(lambda x: process_dupe_ref_end(x) if x['token'] == '<dupe_ref_end>' else x['token'], axis=1)

    # dupe boolean column
    def dupe_helper(input_row) -> bool:
        if input_row['token'] == '<dupe>':
            return True
        if input_row['token'] == '<dupe_ref_end>':
            return True
        return False
    df['dupe'] = df.apply(dupe_helper, axis=1)
    # iterate through the df and replace any row with token = "<dupe>" with
    # the token of the last row with dupe = False, which is not necessarily the previous row
    last_non_dupe_token = None
    for index, row in df[::-1].iterrows():
        if row['token'] != '<dupe>': # not row['dupe']:
            last_non_dupe_token = row['token']
        elif last_non_dupe_token is not None:
            df.at[index, 'token'] = last_non_dupe_token

    # process <dupe_ref_end> tokens
    # iterate through dataframe, keep track of the token of the last row seen
    # with 'token' != "<dupe_ref_end>" (denoted token_last_seen),
    # if a row with "<dupe_ref_end>" is found, then...
    # if the row has ref_start == True, then set its token equal to the value in its 'unformatted' column
    # else, set its token to token_last_seen

    """token_last_seen = None
    for index, row in df.iterrows():
        if row['token'] != '<dupe_ref_end>':
            token_last_seen = row['token']
        elif token_last_seen is not None:
            if row['ref_start']:
                df.at[index, 'token'] = row['unformatted']
            else:
                df.at[index, 'token'] = token_last_seen
        else:
            # print(df.loc[index])
            # raise ValueError("No token_last_seen found for <dupe_ref_end> token.")
            df.at[index, 'token'] = row['unformatted']"""

    return df


def filter_tokens(df: pd.DataFrame) -> pd.DataFrame:

    # remove all characters that

    return df
