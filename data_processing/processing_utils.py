import pandas as pd
from typing import List


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
    Removes any '|' from the text.
    :param text:
    :return: text without '|'
    """
    return text.replace('|', '')


def collapse_same_partitions(df: pd.DataFrame, chain_threshold: float = 0.5) -> pd.DataFrame:
    """
    Combines rows with the same 'text' values and 'start' times within 'chain_threshold' seconds.

    Side effect: it adds `start_of_new_chain` column to df.
    :param df:
    :param chain_threshold:
    :return: modified df
    """
    current_chain_label = 0
    df = df.sort_values(by=['unformatted', 'start']).reset_index(drop=True)
    df['chain_label'] = [current_chain_label] * df.shape[0]

    # adds a new column called 'start_of_new_chain' to the dataframe
    prev_row_unf_text = ""
    prev_end = 0
    start_of_new_chain = []
    for i, row in df.iterrows():
        row_value = not (row['unformatted'] == prev_row_unf_text
                         and (row['start'] - prev_end) < chain_threshold)
        start_of_new_chain.append(row_value)
        prev_row_unf_text = row['unformatted']
        if row_value:
            current_chain_label += 1
        df.loc[i, 'chain_label'] = current_chain_label
        prev_end = row['end']
    df['start_of_new_chain'] = start_of_new_chain

    # group by text and chain label, then aggregate start(min) and end(max)
    df = (df.groupby(['text', 'chain_label']).agg(
        start=('start', 'min'),
        end=('end', 'max'),
        position=('position', 'first'),
        line=('line', 'first'),
        unformatted=('unformatted', 'first'),
        start_of_new_chain=('start_of_new_chain', 'first'),
    ))
    df['text'] = df.index.get_level_values('text')
    df = df.sort_values(by=['unformatted', 'start']).reset_index(drop=True)

    return df


def remove_one_offs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows where the unformatted text is unique.

    Intended to remove rows that likely aren't part of the lyrics/main transcript,
    such as titles, credits, etc.
    :param df:
    :return:
    """

    unformatted_tallies = df['unformatted'].value_counts()
    unformatted_tallies = unformatted_tallies[unformatted_tallies > 1]
    df = df[df['unformatted'].isin(unformatted_tallies.index)].copy()

    return df


def chain_labeling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 'end_of_chain' and 'singleton' columns to the dataframe.
    :param df:
    :return:
    """
    df['end_of_chain'] = False
    # all rows with end_of_chain precedes rows with start_of_new_chain
    df['end_of_chain'] = df['start_of_new_chain'].shift(-1)
    # set the last row to True
    df.loc[df.index[-1], 'end_of_chain'] = True
    # singletons are rows that are both the start and end of a chain
    df['singleton'] = df['start_of_new_chain'] & df['end_of_chain']
    return df


def join_common_segments(segments: List[str], next_segments: List[str]) -> List[str]:
    """
    Joins common segments between the current row and the next row.

    In short, it was used to solve a technical issue with inconsistent formatting in the data,
    which came from stylistic (arbitrary) choices present in the original data.
    :param segments:
    :param next_segments:
    :return: A (standardized) list of strings with 2 elements.
    """
    dupe_idx = 1

    while dupe_idx < len(segments) and segments[-dupe_idx] == next_segments[-dupe_idx]:
        dupe_idx += 1

    joined_after = ''.join(segments[-dupe_idx:])
    joined_before = ''.join(segments[:-dupe_idx])

    return [joined_before, joined_after]


def create_remainder(df: pd.DataFrame, f) -> pd.DataFrame:
    """
    Creates a 'remainder' column in the dataframe.
    :param df:
    :param f:
    :return:
    """
    # replace all ||, |||, etc. in every 'text' entry with |
    df['text'] = df['text'].apply(lambda x: x.replace('||', '|'))
    # remove leading and trailing '|'
    df['text'] = df['text'].str.strip('|')

    # sort first by unformatted ascending, then by start descending
    df = df.sort_values(by=['unformatted', 'start'], ascending=[True, False]).reset_index(drop=True)

    # segments is a list of string separated by |
    df['segments'] = df['text'].str.split('|')

    df['next_segments'] = df['segments'].shift(-1)
    df['prev_segments'] = df['segments'].shift(1)

    # for rows with start_of_new_chain = True, keep them as is.
    # else, replace segments with the joined version
    df['segments'] = df.apply(
        lambda x: [''.join(x['segments'])] if x['end_of_chain']
        else x['segments'] if len(x['segments']) <= 2
        else join_common_segments(x['segments'], x['prev_segments']) if x['start_of_new_chain']
        else join_common_segments(x['segments'], x['next_segments']), axis=1)

    df['next_segments'] = df['segments'].shift(-1)

    # remainder is unformatted if start_of_new_chain; otherwise, next_segments[-1]
    df['remainder'] = df.apply(
        lambda x: x['unformatted'] if x['start_of_new_chain']
        else x['next_segments'][-1], axis=1)

    # print filename if df has any updated segments with length 0 or > 2
    if df['segments'].apply(lambda x: len(x) == 0 or len(x) > 2).any():
        print(f.name + " has updated segments with length 0 or > 2")
        # print(df[df['updated_segments'].apply(lambda x: len(x) == 0 or len(x) > 2)])

    # drop segment columns
    df = df.drop(columns=['next_segments', 'prev_segments','segments'])

    return df


def tokenize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a 'token' column in the dataframe.
    :param df:
    :return:
    """
    # prev_remainder
    df['prev_remainder'] = df['remainder'].shift(1)

    # if end_of_chain, then token = remainder
    # else, token = remainder[:len(remainder)-len(prev_remainder)]
    df['token'] = df.apply(
        lambda x: x['remainder'] if x['end_of_chain']
        else x['remainder'][:len(x['remainder']) - len(x['prev_remainder'])], axis=1)

    # drop remainder and prev_remainder columns
    df = df.drop(columns=['prev_remainder'])

    return df
