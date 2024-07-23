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
    # drop rows where 'line' = -1 or 'line' >= 50
    df = df[(df['line'] != -1) & (df['line'] < 50)]

    return df


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
    df['ref_start'] = df['unformatted'] != df['unformatted'].shift(1)
    df['ref_end'] = df['ref_start'].shift(-1)
    df.loc[0, 'ref_start'] = True # first row
    df.loc[df.index[-1], 'ref_end'] = True # last row

    return df


def compute_counts_ref(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the 'counts_ref' column, which is a list of tuples (segment label, count).
    :param df: with 'ref_start', 'ref_end' columns
    :return: modified df with 'counts_ref' column
    """
    df['counts_ref'] = None
    current_counts = None

    for idx, row in df.iterrows():
        if row['ref_start']:
            current_counts = row['counts']
        df.at[idx, 'counts_ref'] = current_counts

    return df


def compute_count_diff_helper(counts_start, counts_end) -> int:
    """
    Computes the common number between two sets of tuples of the format (segment label, count).
    :param counts_start:
    :param counts_end:
    :return: common number (int)
    """
    # set of segment labels in counts_start
    start_indices = set([i[0] for i in counts_start])
    end_indices = set([i[0] for i in counts_end])
    diff = start_indices - end_indices
    if diff:
        # example:
        # counts_start = [(1, 5), (2, 3), (3, 4), (4, 1)]
        # counts_end = [(1, 5), (3, 4)]
        # start_indices = {1, 2, 3, 4}
        # end_indices = {1, 3}
        # diff = {2, 4}
        # want to choose 2 because it corresponds to the element with the largest count
        counts_diff = [(i, j) for i, j in counts_start if i in diff]
        return max(counts_diff, key=lambda x: x[1])[0]
    else:
        return 0


def compute_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the 'counts' column, which 'tallies' the number of characters under each segment label.
    :param df: with 'segments', 'counts' columns
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
    - Sorts the df by 'unformatted' ascending, then 'start' descending.
    - Produces the 'ref_start', 'ref_end', and 'count_ref' intermediate columns.
    - Computes the 'common_number' column (-1 if there is no common number).

    :param df: with 'unformatted', 'line', 'start', 'counts', 'counts_ref' columns
    :return: modified df
    """

    # this sorting order is very crucial!!!
    df = df.sort_values(by=['unformatted', 'line', 'start'], ascending=[True, False, False]).reset_index(drop=True)
    df = compute_ref_start_end(df)
    df = compute_counts_ref(df)

    # compute common number column
    chain_number_memory = None
    df['common_number'] = None

    for i in df.index[::-1]:
        if df.loc[i, 'ref_end']:
            chain_number_memory = compute_count_diff_helper(df.loc[i, 'counts'], df.loc[i, 'counts_ref'])
        df.at[i, 'common_number'] = chain_number_memory

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


def create_remainders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates the 'remainder' column by using the 'segments' and 'common_number' data.
    :param df: with 'segments'. 'common_number' columns
    :return: df with 'remainder' column
    """
    # 'remainder' column
    # technical details below:
    # if the row has common_number = 0, then the remainder is the unformatted text
    # else, if none of the segments have the common_number, then the remainder is the unformatted text
    # else, the remainder is the concatenation of the segments starting with
    # the first instance of a segment with the common_number
    # use lambda function to apply to each row
    df['remainder'] = df.apply(lambda x: compute_remainder_for_row_helper(x), axis=1)
    return df


def compute_remainder_for_row_helper(row: pd.Series) -> str:
    """
    Computes the 'remainder' column for a single row.
    :param row: a single row of a DataFrame
    :return: the 'remainder' string
    """
    if row['common_number'] == 0:
        return row['unformatted']
    else:
        # find first segment with the index that contains the common number
        # example: [(1, 'abc'), (2, 'def'), (1, 'ghi'), (3, 'jkl')], common_number = 2
        # matching_idx = 1
        # output: 'defghijkl'
        matching_idx = next((i for i, v in enumerate(row['segments']) if v[0] == row['common_number']), None)
        # matching_idx is guaranteed not to be None
        output = ''.join([i[1] for i in row['segments'][matching_idx:]])

        if output == '':
            return row['unformatted']
        else:
            return output


def collapse_similar_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapses the 'start', 'end', 'remainder' columns based on similarity with next row.

    This is to handle subtitles, where the characters 'fade in'.
    :param df: with 'start', 'end', 'remainder' columns
    :return: modified df
    """
    df['next_end'] = df['end'].shift(-1)
    df['next_remainder'] = df['remainder'].shift(-1)

    # iterate through rows, and dropping any similar rows
    current_idx = 0
    indices_to_drop = []

    for i in range(len(df) - 1):
        if df.iloc[i]['remainder'] == df.iloc[i]['next_remainder'] and df.iloc[i]['start'] == df.iloc[i]['next_end']:
            # update the current row
            df.loc[df.index[current_idx], ['start', 'next_end', 'next_remainder']] = df.iloc[i + 1][
                ['start', 'next_end', 'next_remainder']].values
            # mark the next row for deletion
            indices_to_drop.append(df.index[i + 1])
        else:
            # move onto the next row
            current_idx = i + 1

    df = df.drop(indices_to_drop)
    df = df.drop(['next_end', 'next_remainder'], axis=1)
    df = df.reset_index(drop=True)
    return df


def rotate_remainders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rearranges the remainder entries into the correct positions.
    :param df: with 'unformatted', 'remainder' columns
    :return:
    """
    df['next_remainder'] = df['remainder'].shift(-1)
    df.at[df.index[-1], 'next_remainder'] = df.at[df.index[-1], 'remainder']

    df['next_unformatted'] = df['unformatted'].shift(-1)
    df.at[df.index[-1], 'next_unformatted'] = ""

    # make this a lambda function
    df['remainder'] = df.apply(lambda x: x['next_remainder'] if x['unformatted'] == x['next_unformatted']
                               else x['unformatted'], axis=1)

    # drop the temporary columns
    df = df.drop(columns=['next_remainder', 'next_unformatted'])

    return df


def create_tokens(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates tokens based on information from the remainders.
    :param df: with 'remainder' column.
    :return:
    """
    df['prev_remainder'] = df['remainder'].shift(1)
    df.at[0, 'prev_remainder'] = ''

    df['prev_unformatted'] = df['unformatted'].shift(1)
    df.at[0, 'prev_unformatted'] = ''

    df['token'] = df.apply(token_helper, axis=1)

    return df


def token_helper(row: pd.Series) -> str:
    """
    Computes the 'tokens' column for a single row.
    :param row: a single row of a DataFrame
    :return: the 'tokens' string
    """
    if row['unformatted'] != row['prev_unformatted']:  # new line
        return row['remainder']
    elif row['prev_remainder'] == row['remainder']:  # chorus lines
        return row['remainder']
    else:
        # continuing the line (normal/vast majority of the case)
        if row['remainder'].endswith(row['prev_remainder']):
            return row['remainder'][:-len(row['prev_remainder'])]
        # not sure if it's (still) needed, but just in case
        if row['prev_remainder'].endswith(row['remainder']):
            return row['remainder']
        else:
            # this shouldn't happen; can be used for debugging
            return "ERROR"
