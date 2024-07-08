import os
import pandas as pd


def find_common_start_idx(string1: str, string2: str) -> int:
    idx = 0
    while idx < len(string1) and idx < len(string2) and string1[idx] == string2[idx]:
        idx += 1
    return idx


def generate_tokens(df: pd.DataFrame) -> pd.DataFrame:
    # replace all || in every 'text' entry with |
    df['text'] = df['text'].apply(lambda x: x.replace('||', '|'))

    # sort first by unformatted ascending, then by start descending
    df = df.sort_values(by=['unformatted', 'start'], ascending=[True, False]).reset_index(drop=True)

    # value of the next row's 'text' entry, with "" for the last row
    df['next_text'] = df['text'].shift(-1)
    df.at[len(df) - 1, 'next_text'] = ""
    
    # if singleton, df['common_start_idx'] = -1
    # if unformatted = next_unformatted, then
    # df['common_start_idx'] = find_common_start_idx(next_text, text)
    # else, df['common_start_idx'] = -1
    df['common_start_idx'] = [-1] * len(df)
    for i in range(len(df) - 1):
        if df.iloc[i]['unformatted'] == df.iloc[i + 1]['unformatted']:
            df.at[df.index[i], 'common_start_idx'] = find_common_start_idx(df.iloc[i]['text'], df.iloc[i + 1]['text'])

    # if common_start_idx = -1, then remainder is text
    # else, remainder is text[common_start_idx:]
    df['remainder'] = df['text']
    for i in range(len(df)):
        if df.iloc[i]['common_start_idx'] != -1:
            df.at[df.index[i], 'remainder'] = df.iloc[i]['next_text'][df.iloc[i]['common_start_idx']:]
    # remove | from remainder
    df['remainder'] = df['remainder'].str.replace('|', '')

    # prev_shared_idx
    df['prev_shared_idx'] = df['common_start_idx'].shift(1)
    df.at[0, 'prev_shared_idx'] = -1
    # make prev_shared_idx an integer
    df['prev_shared_idx'] = df['prev_shared_idx'].astype(int)

    # prev_remainder
    df['prev_remainder'] = df['remainder'].shift(1)
    df.at[0, 'prev_remainder'] = ""

    # if prev_idx = -1, then token = remainder
    # else, token = remainder - prev_remainder, where prev_remainder is at the end of the current remainder
    # for example, if remainder = "abcde" and prev_remainder = "cde", then token = "ab"
    df['token'] = df['remainder']
    for i in range(len(df)):
        if df.iloc[i]['prev_shared_idx'] != -1:
            df.at[df.index[i], 'token'] = df.iloc[i]['remainder'][:-len(df.iloc[i]['prev_remainder'])]

    return df


def main():
    output_df = pd.DataFrame(
        columns=['start', 'end', 'position', 'line', 'text',
                 'file_name', 'unformatted', 'start_of_new_chain', 'singleton'])

    for filename in os.listdir(os.path.abspath("../data/stage_1_processed/")):
        with open(os.path.abspath("../data/stage_1_processed/" + filename)) as f:
            df = pd.read_csv(f)

            # processing
            df = generate_tokens(df)

            df.to_csv(os.path.abspath("../data/stage_2_processed/csvs/" + filename), index=False)

    output_df.to_csv(os.path.abspath("../data/stage_2_processed/singletons.csv"), index=False)


if __name__ == '__main__':
    main()
