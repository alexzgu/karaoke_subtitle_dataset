import os
import pandas as pd


def generate_tokens(df: pd.DataFrame) -> pd.DataFrame:
    # replace all || in every 'text' entry with |
    df['text'] = df['text'].apply(lambda x: x.replace('||', '|'))

    # sort first by unformatted ascending, then by start descending
    df = df.sort_values(by=['unformatted', 'start'], ascending=[True, False]).reset_index(drop=True)

    # prev_unformatted is the 'unformatted' value of the previous row, with "" for the first row
    df['prev_unformatted'] = df['unformatted'].shift(1)
    df.at[0, 'prev_unformatted'] = ""

    # value of the next row's 'text' entry, with "" for the last row
    df['next_text'] = df['text'].shift(-1)
    df.at[len(df) - 1, 'next_text'] = ""

    # if first and last character of text is |, then remove them
    df['text'] = df['text'].apply(lambda x: x[1:-1] if x[0] == '|' and x[-1] == '|' else x)
    # segments is a list of string separated by |
    df['segments'] = df['text'].str.split('|')
    # next_segments
    df['next_segments'] = df['segments'].shift(-1)
    # for last row, next_segments = []
    df.at[len(df) - 1, 'next_segments'] = []
    # prev_segments
    df['prev_segments'] = df['segments'].shift(1)
    df.at[0, 'prev_segments'] = []
    # if singleton, then remainder = ""
    # else if start of new chain, then remainder = unformatted - last element of segments
    # (in the abstract sense; the below implementation makes an assumption)
    # else remainder = last element of next_segments
    df['remainder'] = df.apply(
        lambda x: "" if x['singleton'] else x['unformatted'][:len(x['unformatted']) - len(x['segments'][-1])] if x[
            'start_of_new_chain'] else x['next_segments'][-1], axis=1)
    # prev_remainder
    df['prev_remainder'] = df['remainder'].shift(1)
    df.at[0, 'prev_remainder'] = ""

    # if start of new chain or unformatted != prev_unformatted, then token = remainder
    # else token = the slice of remainder that ends right before index len(remainder) - len(prev_remainder)
    df['token'] = df.apply(
        lambda x: x['remainder'] if x['start_of_new_chain'] or x['unformatted'] != x['prev_unformatted']
        else x['remainder'][:len(x['remainder']) - len(x['prev_remainder'])], axis=1)

    debug = False
    if not debug:
        df.drop(columns=['prev_unformatted', 'next_text', 'segments', 'next_segments', 'prev_segments', 'remainder',
                         'prev_remainder'], inplace=True)

    return df


def main():
    input_path = "../data/stage_2_processed/csvs/"
    output_path = "../data/stage_3_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:
            df = pd.read_csv(f)

            # processing
            df = generate_tokens(df)

            df.to_csv(os.path.abspath(output_path + "csvs/" + filename), index=False)


if __name__ == '__main__':
    main()
