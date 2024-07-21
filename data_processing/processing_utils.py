import pandas as pd
import re
import ast


def filter_rows(df):
    """
    NOTE: used only for RO data, NOT JP data!!!
    
    In other words, this is for dataset-specific processing, which you may not need.
    Would recommend commenting out this function first.
    :param df:
    :return: df with some rows removed
    """

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
    return df


def convert_segments_to_tuples(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the 'segments' column from string to list of tuples.
    Needed if segments are stored in an intermediate file, which is then read as a string
    when the intermediate file is read.
    :param df:
    :return: modified df with 'segments' column as list of tuples
    """
    def string_to_tuple_list(segment_str):
        return ast.literal_eval(segment_str)

    df['segments'] = df['segments'].apply(string_to_tuple_list)
    return df


def compute_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the 'counts' column, which 'tallies' the number of characters under each segment label.
    :param df:
    :return: modified df with 'counts', a set of tuples (segment label, count)
    """
    # compute the length of each segment
    df['counts'] = df['segments'].apply(lambda x: [(i[0], len(i[1])) for i in x])

    # sum the lengths of segments with the same segment number
    df['counts'] = df['counts'].apply(lambda x: [(i[0], sum([j[1] for j in x if j[0] == i[0]])) for i in x])
    df['counts'] = df['counts'].apply(lambda x: list(set(x)))
    return df


def compute_common_number(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts the df by 'unformatted' ascending, then 'start' descending.
    Computes the 'common_number' column (-1 if there is no common number).

    :param df: must have 'counts' column
    :return:
    """
    # assumption: the dataframe has the 'counts' columns

    # sort by unformatted ascending, then start descending
    df = df.sort_values(by=['unformatted', 'start'], ascending=[True, False]).reset_index(drop=True)

    df['ref_end'] = df['unformatted'].shift(-1) != df['unformatted']
    df['ref_start'] = df['ref_end'].shift(1)
    # first row has 'ref_start' = True and 'ref_end' = False
    df.loc[0, 'ref_start'] = True
    df.loc[0, 'ref_end'] = False

    # compute another list of tuples column ('counts_ref')
    df['counts_ref'] = None
    current_counts = None
    for idx, row in df.iterrows():
        if row['ref_start']:
            current_counts = row['counts']
        df.at[idx, 'counts_ref'] = current_counts

    # compute common number column
    def compute_count_diff(counts_start, counts_end) -> int:
        counts_start = set(counts_start)
        counts_end = set(counts_end)
        diff = counts_start - counts_end
        if diff:
            return max(diff, key=lambda x: x[1])[0]

    chain_number_memory = None
    df['common_number'] = -1

    for i in df.index[::-1]:
        if df.loc[i, 'ref_end']:
            chain_number_memory = compute_count_diff(df.loc[i, 'counts'], df.loc[i, 'counts_ref'])
        df.at[i, 'common_number'] = chain_number_memory

    df = df.drop(columns=['ref_start', 'ref_end', 'counts_ref'])

    return df


def create_partitions(df: pd.DataFrame) -> pd.DataFrame:
    # assumption: the dataframe has 'segments' column
    def process_segment(segment_str):
        # convert string representation of list to actual list of tuples
        # if segments is a string
        if isinstance(segment_str, str):
            segments = ast.literal_eval(segment_str)
        else:
            segments = segment_str
        # extract the second element (string) from each tuple and join
        return '|'.join([i[1] for i in segments])

    # apply the processing function to each row
    df['partition'] = df['segments'].apply(process_segment)
    return df
