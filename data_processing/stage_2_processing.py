import os
import pandas as pd


# helper
def unformatted(text: str):
    # remove any '|'
    return text.replace('|', '')


# helper
def chain_labeling(df: pd.DataFrame):
    # adds a column containing unformatted text
    df['unformatted'] = df['text'].apply(unformatted)

    # adds a new column called 'start_of_new_chain' to the dataframe
    prev_row_unf_text = ""
    start_of_new_chain = []
    for i, row in df.iterrows():
        start_of_new_chain.append(not (row['unformatted'] == prev_row_unf_text))
        prev_row_unf_text = row['unformatted']
    df['start_of_new_chain'] = start_of_new_chain

    return df


# adds columns to the dataframe to help identify singletons
def find_singletons(df, filename, output_df):
    # adds a column containing the name of the file
    df['file_name'] = filename

    df = chain_labeling(df)

    # removes rows where the unformatted text is unique
    unformatted_tallies = df['unformatted'].value_counts()
    unformatted_tallies = unformatted_tallies[unformatted_tallies > 1]
    df = df[df['unformatted'].isin(unformatted_tallies.index)].copy()

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
        df = df[df['unformatted'] != ""]

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
    output_df = pd.DataFrame(
        columns=['start', 'end', 'position', 'line', 'text',
                 'file_name', 'unformatted', 'start_of_new_chain', 'singleton'])

    for filename in os.listdir(os.path.abspath("../data/stage_1_processed/")):
        with open(os.path.abspath("../data/stage_1_processed/" + filename)) as f:
            df = pd.read_csv(f)

            df = find_singletons(df, filename, output_df)

            df = edge_cases(df, filename)

            print_singletons(df, output_df)

            df.to_csv(os.path.abspath("../data/stage_2_processed/csvs/" + filename), index=False)

    output_df.to_csv(os.path.abspath("../data/stage_2_processed/singletons.csv"), index=False)


if __name__ == '__main__':
    main()
