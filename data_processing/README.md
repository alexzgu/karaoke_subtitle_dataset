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
       - final_dataset/

2. cd into data/raw/

3. Type the below command into terminal:

    ```bash
    yt-dlp --ignore-errors --continue --no-overwrites --download-archive progress.txt --write-sub --sub-lang {language of subtitles (en/ja/etc.)} "{URL of playlist}"
    ```

    Note that some videos may be in formats other than .webm, or may not come with subtitles (which may be in a different language than the one specified).
    It is up to you to sort out these discrepancies manually.

4. run src/main.rs

5. cd to data_processing/ (because the below script uses relative paths)

6. run data_processing/process_parsed_data.py

7. further cleaning is left to the user