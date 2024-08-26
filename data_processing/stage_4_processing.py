import os
from processing_utils import *


def process_file(f) -> pd.DataFrame or None:
    na_values = ["",
                 "#N/A",
                 "#N/A N/A",
                 "-1.#IND",
                 "-1.#QNAN",
                 "1.#IND",
                 "1.#QNAN",
                 "<NA>",
                 "N/A",
                 "NULL",
                 "n/a", ]
    df = pd.read_csv(f, na_values=na_values, keep_default_na=False)
    # if the df has less than 3 rows, then skip it
    if len(df) < 3:
        print(f"Skipping {f.name.split('/')[-1]} because it has less than 3 rows.")
        return None

    df = df.drop(columns=['ref_start', 'ref_end', 'dupe', 'segments', 'unformatted'])
    return df


def main():
    stage_no = 4
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
