Tutorial:

Notes:
- Ran this from Arch Linux, so the commands might be different for other OSes.
- requires yt-dlp, rust, and python

1. Create the below directories at project root:
   - data/
       - raw/
       - indexed/
         - vtts/
         - videos/
       - parsed/
       - stage_1_processed/
       - stage_2_processed/
         - csvs/
       - stage_3_processed/
         - csvs/
       - final_dataset/
         - csvs/

2. cd into data/raw/

3. Type the below command into terminal:

    ```bash
    yt-dlp --ignore-errors --continue --no-overwrites --download-archive progress.txt --write-sub --sub-lang {language of subtitles (en/ja/etc.)} "{URL of playlist}"
    ```

    Note that some videos may be in formats other than .webm, or may not come with subtitles (which may be in a different language than the one specified).
    It is up to you to sort out these discrepancies manually.

4. run src/index_data::index_raw_files (when in doubt, delete index.tsv and rerun)

5. run src/parse_vtt::parse_vtts

6. cd to data_processing/ (because the below scripts use relative paths)

7. run data_processing/stage_1_processing.py

8. run data_processing/stage_2_processing.py

9. run data_processing/stage_3_processing.py

10. run data_processing/generate_final_dataset.py

11. further cleaning is left to the user