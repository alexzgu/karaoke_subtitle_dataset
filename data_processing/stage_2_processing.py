import os
import pandas as pd
from typing import List


def join_common_segments(segments: List[str], next_segments: List[str]) -> List[str]:
    dupe_idx = 1

    while dupe_idx < len(segments) and segments[-dupe_idx] == next_segments[-dupe_idx]:
        dupe_idx += 1

    joined_after = ''.join(segments[-dupe_idx:])
    joined_before = ''.join(segments[:-dupe_idx])

    return [joined_before, joined_after]


def standardize_partition_formatting(df: pd.DataFrame, f) -> pd.DataFrame:
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
        else join_common_segments(x['segments'], x['next_segments'])
        , axis=1)

    df['next_segments'] = df['segments'].shift(-1)

    # remainder is unformatted if start_of_new_chain; otherwise, next_segments[-1]
    df['remainder'] = df.apply(
        lambda x: x['unformatted'] if x['start_of_new_chain']
        else x['next_segments'][-1]
        , axis=1)

    # print filename if df has any updated segments with length 0 or > 2
    if df['segments'].apply(lambda x: len(x) == 0 or len(x) > 2).any():
        print(f.name + " has updated segments with length 0 or > 2")
        # print(df[df['updated_segments'].apply(lambda x: len(x) == 0 or len(x) > 2)])

    # drop segment columns
    df = df.drop(columns=['next_segments', 'prev_segments',
                          'segments'
                          ])

    return df


def tokenize(df: pd.DataFrame) -> pd.DataFrame:
    # prev_remainder
    df['prev_remainder'] = df['remainder'].shift(1)

    # if end_of_chain, then token = remainder
    # else, token = remainder[:len(remainder)-len(prev_remainder)]
    df['token'] = df.apply(
        lambda x: x['remainder'] if x['end_of_chain']
        else x['remainder'][:len(x['remainder']) - len(x['prev_remainder'])]
        , axis=1)

    # drop remainder and prev_remainder columns
    df = df.drop(columns=['prev_remainder'])

    return df


def process_file(f) -> pd.DataFrame:
    df = pd.read_csv(f)

    # processing
    df = standardize_partition_formatting(df, f)

    df = tokenize(df)

    df = df.drop(columns=['unformatted', 'remainder', 'start_of_new_chain', 'end_of_chain', 'singleton'])

    return df


def main():
    input_path = "../data/stage_1_processed/"
    output_path = "../data/stage_2_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:
            df = process_file(f)
            df.to_csv(os.path.abspath(output_path + "csvs/" + filename), index=False)


if __name__ == '__main__':
    main()
