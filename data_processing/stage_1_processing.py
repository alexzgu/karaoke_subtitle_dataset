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


def unformatted(text: str):
    # remove any '|'
    return text.replace('|', '')


def collapse_same_partitions(df: pd.DataFrame):
    # adds a column containing unformatted text
    chain_threshold = 0.5
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
    # removes rows where the unformatted text is unique
    unformatted_tallies = df['unformatted'].value_counts()
    unformatted_tallies = unformatted_tallies[unformatted_tallies > 1]
    df = df[df['unformatted'].isin(unformatted_tallies.index)].copy()

    return df


def chain_labeling(df: pd.DataFrame) -> pd.DataFrame:
    df['end_of_chain'] = False
    # all rows with end_of_chain precedes rows with start_of_new_chain
    df['end_of_chain'] = df['start_of_new_chain'].shift(-1)
    # set the last row to True
    df.loc[df.index[-1], 'end_of_chain'] = True
    # singletons are rows that are both the start and end of a chain
    df['singleton'] = df['start_of_new_chain'] & df['end_of_chain']
    return df


def process_file(f) -> pd.DataFrame:
    df = pd.read_csv(f)

    # if there are any nulls, print
    if df.isnull().values.any():
        print(f + " has null values")
        df = df.dropna(how='any', axis=0)

    df = df.drop_duplicates()
    df = convert_time(df)
    df['text'] = df['text'].str.lower()

    df['unformatted'] = df['text'].apply(unformatted)
    df = collapse_same_partitions(df)
    df = remove_one_offs(df)
    df = chain_labeling(df)

    return df


def main():
    # directory paths
    input_path = "../data/parsed/"
    output_path = "../data/stage_1_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:
            df = process_file(f)
            df.to_csv(os.path.abspath(output_path + filename), index=False)


if __name__ == '__main__':
    main()
