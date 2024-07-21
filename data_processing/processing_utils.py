import pandas as pd
import re
import ast


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


def collapse_same_partitions(df: pd.DataFrame, chain_threshold: float = 0.5) -> pd.DataFrame:
    """
    Combines rows with the same 'text' values and 'start' times within 'chain_threshold' seconds.
    Marks rows preceding a 'start_of_new_chain' with an indicator.

    Side effect: it adds `start_of_new_chain` and `indicator` columns to df.
    :param df:
    :param chain_threshold:
    :return: modified df
    """
    current_chain_label = 0
    df = df.sort_values(by=['unformatted', 'start']).reset_index(drop=True)
    df['chain_label'] = [current_chain_label] * df.shape[0]

    # adds new columns called 'start_of_new_chain' and 'indicator' to the dataframe
    prev_row_unf_text = ""
    prev_end = 0
    start_of_new_chain = []
    indicator = []
    for i, row in df.iterrows():
        row_value = not (row['unformatted'] == prev_row_unf_text
                         and (row['start'] - prev_end) < chain_threshold)
        start_of_new_chain.append(row_value)

        # Set indicator for the previous row if this row starts a new chain
        if i > 0:
            indicator.append(row_value)
        if i == df.shape[0] - 1:  # For the last row
            indicator.append(False)

        prev_row_unf_text = row['unformatted']
        if row_value:
            current_chain_label += 1
        df.loc[i, 'chain_label'] = current_chain_label
        prev_end = row['end']

    df['start_of_new_chain'] = start_of_new_chain
    df['indicator'] = indicator

    # group by text, chain label, and indicator, then aggregate start(min) and end(max)
    df = (df.groupby(['text', 'chain_label', 'indicator']).agg(
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


def create_segments(df: pd.DataFrame) -> pd.DataFrame:
    df['segments'] = df['text'].apply(lambda x: x.split('</c>'))

    df['segments'] = df['segments'].apply(
        lambda x: [(int(re.search(r'<(\d+)>', i).group(1)), re.sub(r'<\d+>', '', i)) if re.search(r'<\d+>', i)
                   else (i, '') for i in x if i != ''])

    # compute the length of each segment
    df['counts'] = df['segments'].apply(lambda x: [(i[0], len(i[1])) for i in x])

    # sum the lengths of segments with the same segment number
    df['counts'] = df['counts'].apply(lambda x: [(i[0], sum([j[1] for j in x if j[0] == i[0]])) for i in x])
    df['counts'] = df['counts'].apply(lambda x: list(set(x)))
    # first element of each tuple converted to an integer
    # part of filename after 'processed/' and before '.csv'
    df['counts'] = df['counts'].apply(lambda x: [(int(i[0]), i[1]) for i in x])

    # look at the rows of the df in reverse order
    # make a new column called 'counts_end', which is computed by the following:
    # if the row is end_of_chain, set counts_end to counts
    # else, set counts_end to the counts of the most recent end_of_chain row seen
    # iterate through the rows in reverse order
    counts_end_memory = None
    df['counts_end'] = None  # Initialize the column
    for i in df.index[::-1]:  # Iterate in reverse order
        if df.loc[i, 'end_of_chain']:
            counts_end_memory = df.loc[i, 'counts']
        df.at[i, 'counts_end'] = counts_end_memory

    # chain number is computed as the following:
    # if the row is the start of a chain, you first find
    # the tuple in counts that is not in counts_end, and set the chain number to the first element of that tuple
    # else, set the chain number to the chain number of the last start_of_new_chain row seen
    # code here !!!
    # chain number computation

    # filename column

    chain_number_memory = None
    df['chain_number'] = None  # Initialize the column
    for i in df.index:
        if df.loc[i, 'start_of_new_chain']:
            counts_set = set(df.loc[i, 'counts'])
            counts_end_set = set(df.loc[i, 'counts_end']) if df.loc[i, 'counts_end'] is not None else set()
            diff = counts_set - counts_end_set
            # if diff has more than one element, print the filename and the diff set
            if diff:
                # get the first element of the element of the diff set with the largest second element
                chain_number_memory = max(diff, key=lambda x: x[1])[0]
        df.at[i, 'chain_number'] = chain_number_memory

    # drop counts and counts_end columns
    df = df.drop(columns=['counts', 'counts_end'])

    return df


def compute_remainder_for_row(row):
    chain_number = row['chain_number']
    segments_str = row['segments']

    # Convert string representation of list of tuples back to actual list of tuples
    segments = ast.literal_eval(segments_str)

    remainder = ""
    found_chain = False
    for i, segment in enumerate(segments):
        if segment[0] == chain_number:
            found_chain = True
        if found_chain:
            remainder += segment[1]

    return remainder


def create_remainder(df: pd.DataFrame) -> pd.DataFrame:
    df['remainder'] = df.apply(lambda x: x['unformatted'] if x['end_of_chain'] else compute_remainder_for_row(x),
                               axis=1)

    return df


def sort_remainder(df: pd.DataFrame) -> pd.DataFrame:
    # Create a mask for singleton rows
    singleton_mask = df['singleton'] == True

    # Create a temporary column to store the end_of_chain remainders
    df['temp_remainder'] = df['remainder']

    # Iterate through the DataFrame to handle chains
    chain_remainder = None
    for i in range(len(df)):
        if df.loc[i, 'start_of_new_chain']:
            # Find the corresponding end_of_chain row
            end_index = df.index[df['end_of_chain'] & (df.index >= i)].min()
            chain_remainder = df.loc[end_index, 'remainder']

        if not singleton_mask[i]:
            if df.loc[i, 'start_of_new_chain']:
                df.loc[i, 'temp_remainder'] = chain_remainder
            elif i > 0:  # Not the first row
                df.loc[i, 'temp_remainder'] = df.loc[i - 1, 'remainder']

    # Update the remainder column
    df.loc[~singleton_mask, 'remainder'] = df.loc[~singleton_mask, 'temp_remainder']

    # Drop the temporary column
    df = df.drop('temp_remainder', axis=1)

    return df


def tokenize(df: pd.DataFrame) -> pd.DataFrame:
    # next_remainder and prev_remainder columns
    df['next_remainder'] = df['remainder'].shift(-1)
    # if end_of_chain is True, token remainder
    # else, token is remainder[:len(remainder) - len(next_remainder)]
    df['token'] = df.apply(lambda x: x['remainder'] if x['end_of_chain']
    else x['remainder'][:len(x['remainder']) - len(x['next_remainder'])], axis=1)
    return df
