<h1>Purpose</h1>

This is intended to parse publicly available karaoke-style subtitles
found on YT into datasets containing timestamped tokens.

The parsing process is intended to be as simple as possible,
while also retaining as much of the information present in the original data.

The below figure summarizes what this process does.

![image of process](about/input_output.png "Process")

---
<h1>High-Level Overview</h1>

Below is a high-level overview of the data parsing pipeline
(inaccuracies present for presentation purposes).

![Pipeline](about/pipeline.png "Pipeline")

___

<h1>Tutorial</h1>

<h2>Notes</h2>
<h3>Tools used</h3>
  - Rust
  - Python
  - [YT-DLP](https://github.com/yt-dlp) (default, but optional: see below)

<h2>Steps</h2>
<h3>1. Create the below directories at project root:</h3>
![Directory Structure](about/directories.png)
<h3>2. Attain WebVTT files</h3>
<p>By default, the indexing functionality written here is intended to use both a VTT
and its video to be downloaded from yt-dlp. If you do not want to download the video 
while generating the dataset, I suggest going for <b>Option 2</b>.</p>
<h4>Option 1: Use `yt-dlp`</h4>

1. `cd` into `data/raw/`

2. Type the following into terminal:
`yt-dlp --ignore-errors --continue --no-overwrites --download-archive progress.txt 
    --write-sub --sub-lang {language of subtitles (en/ja/etc.)} "{URL of playlist}"`

<p><b>Note:</b> some videos may be downloaded in formats other than .webm, 
or may not come with subtitles (which may be in a different language
than the one specified).</p>

<p>It is up to you to sort out these discrepancies manually.</p>

<h4>Option 2: Use other means</h4>
1. Attain WebVTT files.

   1. <b>Tip:</b> If you want just the VTT's (and no videos) while using yt-dlp, you can add the `--skip-download` flag 
   (refer to <b>Option 1</b> for a template `yt-dlp` call).

2. Place them in `data/indexed/` (default option), or in a custom directory.

<h3>4. Run `src/main.rs `</h3>
If you chose the default (<b>Option 1</b>), then run the file as is.
Otherwise (<b>Option 2</b>)...

- Comment out the index_files() line.

- (OPTIONAL) Specify a custom input (`data/indexed/` default)
   and output (`data/parsed/` default) directory
   for the `parse_files()` function.

<h3>5. `cd` to `data_processing/` </h3>
- (because the below script uses relative paths)

<h3>6. Run `data_processing/parsed_to_tokens.py`</h3>
- If you chose the default options, run as-is.

- Otherwise, the custom input you specify should match the output of the `parse_files()` function in `src/main.rs`.

<h3>7. Enjoy the final* generated dataset!</h3>
*further cleaning is left to the user

Sidenote: the `data_processing/stage_{1/2/3/4}_processing.py` files are available for debugging purposes.

___

<h1>Assumptions about the Data</h1>

1. The original subtitles data are in WebVTT format that supports <> formating tags.
2. The parsing process takes a <u>color-based</u> approach to separate the text into the tokens (see examples below).
   1. If your subtitles do not use color to separate spoken text in a line, this repository will not help you.
3. The entire line of text must be <u>visible</u> and <u>unchanged</u> the entire time it's displayed (see examples below).

Below are <u>examples</u> and <u>non-examples</u> of supported subtitle formatting.</h3>

![image of examples and nonexamples of supported color formats](about/examples.png "Examples")










