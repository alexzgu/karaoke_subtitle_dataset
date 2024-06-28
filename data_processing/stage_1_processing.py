import os
import pandas as pd


def main():
    for filename in os.listdir(os.path.abspath("../data/parsed/")):
        with open(os.path.abspath("../data/parsed/" + filename)) as f:
            df = pd.read_csv(f)
            df = df.drop_duplicates()
            # drop rows where line = -1 or line >= 50
            df = df[(df['line'] != -1) & (df['line'] < 50)]

            # if there are any nulls, print
            if df.isnull().values.any():
                print(filename + " has null values")
                df = df.dropna(how='any', axis=0)

            # output to "../data/stage_1_processed/"
            df.to_csv(os.path.abspath("../data/stage_1_processed/" + filename), index=False)


if __name__ == '__main__':
    main()
