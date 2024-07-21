import os
from processing_utils import *


def process_file(f) -> pd.DataFrame:
    df = pd.read_csv(f)
    df = convert_segments_to_tuples(df)

    df = create_partitions(df)

    return df


def main():
    stage_no = 2
    input_path = f"../data/stage_{stage_no - 1}_processed/"
    output_path = f"../data/stage_{stage_no}_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)

            df.to_csv(os.path.abspath(output_path + filename), index=False)


if __name__ == '__main__':
    main()
