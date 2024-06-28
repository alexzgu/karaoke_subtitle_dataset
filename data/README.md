Tutorial:
1. I typed the below command into terminal:

```bash
yt-dlp --ignore-errors --continue --no-overwrites --download-archive progress.txt --write-sub --sub-lang en "{URL of playlist}"
```

Make sure the videos are in .webm format!

2. Create the below directories at project root:
- data/
    - raw/
    - indexed/
      - vtts/
      - videos/
    - parsed/
    - stage_1_processed/
    - stage_2_processed/
      - csvs/

3. run src/index_data::index_raw_files (when in doubt, delete index.tsv and rerun)

4. run src/parse_vtt::parse_vtts

5. run data_processing/stage_1_processing.py

6. run data_processing/stage_2_processing.py