import os
from processing_utils import *


def process_file(f) -> pd.DataFrame or None:

    df = pd.read_csv(f)
    # if the df has less than 3 rows, then skip it
    if len(df) < 3:
        print(f"Skipping {f.name.split('/')[-1]} because it has less than 3 rows.")
        return None

    df = convert_segments_to_tuples(df)
    df = clean_segments(df)

    df = create_remainders(df)
    df = collapse_similar_columns(df)

    return df


def main():
    stage_no = 3
    input_path = f"../data/stage_{stage_no - 1}_processed/"
    output_path = f"../data/stage_{stage_no}_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)

            if df is None:
                continue

            df.to_csv(os.path.abspath(output_path + filename), index=False)


if __name__ == '__main__':
    main()
