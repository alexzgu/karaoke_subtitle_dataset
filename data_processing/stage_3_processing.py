import os
import pandas as pd


def generate_tokens(df: pd.DataFrame) -> pd.DataFrame:
    # replace all || in every 'text' entry with |
    df['text'] = df['text'].apply(lambda x: x.replace('||', '|'))
    # remove leading and trailing '|'
    df['text'] = df['text'].str.strip('|')

    df = df.sort_values(by=['start'], ascending=[True]).reset_index(drop=True)

    df['end_of_chain'] = False
    # if row is the first in df or precedes a row with 'start_of_new_chain' = True, then 'end_of_chain' = True
    for i in range(1, len(df)):
        df.at[i - 1, 'end_of_chain'] = df.at[i, 'start_of_new_chain']
    df.at[len(df) - 1, 'end_of_chain'] = True

    # sort first by unformatted ascending, then by start descending
    df = df.sort_values(by=['unformatted', 'start'], ascending=[True, False]).reset_index(drop=True)

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

    from typing import List

    def get_remainder_2(segments: List[str], next_segments: List[str]) -> str:
        """Start of new chain = False"""

        dupe_idx = 1
        while dupe_idx < len(segments) and segments[-dupe_idx] == next_segments[-dupe_idx]:
            dupe_idx += 1
        # search for idx of first instance when next_segments[-idx] is found in unformatted

        # return next_segments[-dupe_idx]
        # instead of just the above, return the joint of the above and all elements after it
        return ''.join(next_segments[-dupe_idx:])

    df['remainder'] = df.apply(
        lambda x: x['unformatted'] if x[
            'start_of_new_chain'] else get_remainder_2(x['segments'], x['next_segments']), axis=1)

    # prev_remainder
    df['prev_remainder'] = df['remainder'].shift(1)
    df.at[0, 'prev_remainder'] = ""

    def token_function(remainder: str, prev_remainder: str) -> str:
        # if prev_remainder is a substring of remainder, then return remainder - prev_remainder
        # else return remainder
        if prev_remainder == "":
            return remainder
        if prev_remainder in remainder:
            return remainder[:len(remainder) - len(prev_remainder)]
        return remainder

    df['token'] = df.apply(lambda x: x['unformatted'] if x['singleton'] else token_function(x['remainder'], x['prev_remainder']), axis=1)

    debug = False
    if not debug:
        df.drop(columns=['next_text', 'segments', 'next_segments', 'prev_segments', 'remainder',
                         'prev_remainder', 'end_of_chain'], inplace=True)

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
