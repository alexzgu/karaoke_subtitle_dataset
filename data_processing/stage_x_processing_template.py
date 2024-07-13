import os
import pandas as pd


def some_helper_function(df: pd.DataFrame) -> pd.DataFrame:
    return df


def process_file(f) -> pd.DataFrame:
    df = pd.read_csv(f)
    return df


def main():
    stage_no = 3
    input_path = f"../data/stage_{stage_no - 1}_processed/csvs/"
    output_path = f"../data/stage_{stage_no}_processed/"

    for filename in os.listdir(os.path.abspath(input_path)):
        with open(os.path.abspath(input_path + filename)) as f:

            df = process_file(f)

            df.to_csv(os.path.abspath(output_path + "csvs/" + filename), index=False)


if __name__ == '__main__':
    main()
