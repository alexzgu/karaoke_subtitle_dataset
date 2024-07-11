import os
import pandas as pd
import re


# helper
def unformatted(text: str):
    # remove any '|'
    return text.replace('|', '')


# helper
# function to filter non-alphanumeric characters
def filter_non_alphanumeric(s):
    return re.sub(r'\W+', '', s)


# helper
def chain_labeling(df: pd.DataFrame):
    # adds a column containing unformatted text
    chain_threshold = 0.5
    current_chain_label = 0

    df['unformatted'] = df['text'].apply(unformatted)

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
        file_name=('file_name', 'first')
    ))
    df['text'] = df.index.get_level_values('text')
    df = df.sort_values(by=['unformatted', 'start']).reset_index(drop=True)

    return df


# adds columns to the dataframe to help identify singletons
def find_singletons(df, filename):
    twice_length_limit = 10  # limit for length of unformatted text (alphanumeric only) that appears exactly twice

    # adds a column containing the name of the file
    df['file_name'] = filename

    df = chain_labeling(df)

    # removes rows where the unformatted text is unique
    unformatted_tallies = df['unformatted'].value_counts()
    unformatted_tallies = unformatted_tallies[unformatted_tallies > 1]
    df = df[df['unformatted'].isin(unformatted_tallies.index)].copy()

    # removes rows where the unformatted text appears exactly twice (corresponds to unformatted_tallies = 2)
    # and its length (alphanumeric characters) is greater than 10
    df['unformatted_length'] = df['unformatted'].apply(lambda x: len(filter_non_alphanumeric(x)))
    # print any rows that meet the condition into console
    if ((df['unformatted_length'] > twice_length_limit) & (df['unformatted'].map(unformatted_tallies) == 2)).any():
        print(filename + " has unformatted_length > 10 and unformatted_tallies == 2")
        # print the text of each row that meets this
        for i, row in df[((df['unformatted_length'] > twice_length_limit) &
                          (df['unformatted'].map(unformatted_tallies) == 2))].iterrows():
            print(row['text'])
        df = df[~((df['unformatted_length'] > twice_length_limit) &
                  (df['unformatted'].map(unformatted_tallies) == 2))].copy()
    # drop unformatted_length
    df = df.drop(columns=['unformatted_length'])

    # adds a column containing booleans
    # true if this row and the next row both have 'True' in the 'start_of_new_chain' column
    df['singleton'] = df['start_of_new_chain'] & df['start_of_new_chain'].shift(-1)

    return df


# removes rows with null values or empty unformatted values
def edge_cases(df, filename):
    # if there are any nulls, print
    if df.isnull().values.any():
        print(filename + " has null values")
        df = df.dropna(how='any', axis=0)

    # if a row has unformatted = "", print into console and remove
    # just for you, 91.csv ;)
    if (df['unformatted'] == "").any():
        print(filename + " has empty unformatted values")
        df = df[df['unformatted'] != ""].copy()

    return df


# prints rows to output_df if singleton is true
def print_singletons(df, output_df):
    # adds rows to output_df if singleton is true
    for i, row in df.iterrows():
        if row['singleton']:
            output_df.loc[len(output_df)] = [row['start'], row['end'], row['position'], row['line'], row['text'],
                                             row['file_name'], row['unformatted'],
                                             row['start_of_new_chain'], row['singleton']]


def main():
    input_path = "../data/stage_1_processed/"
    output_path = "../data/stage_2_processed/"

    output_df = pd.DataFrame(
        columns=['start', 'end', 'position', 'line', 'text',
                 'file_name', 'unformatted', 'start_of_new_chain', 'singleton'])

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:
            df = pd.read_csv(f)

            df = find_singletons(df, filename)

            df = edge_cases(df, filename)

            print_singletons(df, output_df)

            df.to_csv(os.path.abspath(output_path + "csvs/" + filename), index=False)

    output_df.to_csv(os.path.abspath(output_path + "singletons.csv"), index=False)


if __name__ == '__main__':
    main()
