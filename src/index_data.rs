use std::fs::{OpenOptions, File, read_to_string, rename, read_dir};
use std::path::{Path};
use std::io::{Write};
use regex::Regex;

/// Indexes all raw video files to generate a list of indexed files.
/// Note: the contents of these files have not been processed yet.
pub fn index_raw_files() {
    let data_directory = "data/";
    // initialize index file
    let index_file_path: &str = &format!("{data_directory}/indexed/index.tsv");
    let starting_index = initialize_index_file(index_file_path);

    println!("Index: {}", starting_index);
    let mut idx = starting_index;

    let dir_path = format!("{}/raw", data_directory);

    // Read the directory
    if let Ok(entries) = read_dir(&dir_path) {
        for entry in entries {
            if let Ok(entry) = entry {
                if let Some(file_name) = entry.file_name().to_str() {
                    //println!("{}", file_name.clone());
                    // Skip files ending with .webm
                    if !file_name.ends_with(".vtt") {
                        continue;
                    }
                    // Extract video title, video ID, and subtitle language
                    let (video_name, video_id, language) = extract_video_info(file_name);
                    // if the outputted video name is empty, skip this file
                    if video_name.is_empty() {
                        println!("Skipping file: {}", file_name);
                        continue;
                    }
                    let video_exists = find_video(&video_name, &video_id, &dir_path);
                    match video_exists {
                        0 => {
                            println!("Video file not found for: {}", file_name);
                        }
                        1 => {
                            let entry = format!("{}\t{}\t{}\t{}\n", idx, &video_name, &video_id, &language);
                            let appended = append_entry_to_index_file(index_file_path, &entry);
                            match appended {
                                1 => {
                                    let indexed = index_files(idx, &file_name, &video_name, &video_id, &data_directory);
                                    match indexed {
                                        1 => {
                                            idx += 1;
                                        }
                                        _ => {
                                            println!("Error indexing files: {}", entry);
                                        }
                                    }
                                }
                                _ => {
                                    println!("Error appending entry to index file: {}", entry);
                                }
                            }
                        }
                        _ => {
                            println!("Error finding video file: {}", file_name);
                        }
                    }

                }
            }
        }
    } else {
        eprintln!("Failed to read directory: {}", dir_path);
    }
}

/// Extracts the video title, video ID, and subtitle language from the file name.
fn extract_video_info(file_name: &str) -> (String, String, String) {
    // Parse the file name using regex
    let re = Regex::new(r"^(?P<video_name>.+)\s+\[(?P<video_id>.+)\]\.(?P<subtitle_language>.+)\.vtt$").unwrap();
    if let Some(captures) = re.captures(file_name) {
        // Extract named capture groups
        let video_name = captures["video_name"].to_string();
        let video_id = captures["video_id"].to_string();
        let subtitle_language = captures["subtitle_language"].to_string();

        (video_name, video_id, subtitle_language)
    } else {
        eprintln!("Failed to parse file name: {}", file_name);
        (String::new(), String::new(), String::new())
    }
}

/// Tries to append an entry to the index file.
/// *Returns* 1 if successful, 0 if not.
fn append_entry_to_index_file(index_file_path: &str, entry: &String) -> i32 {
    let file = OpenOptions::new()
        .write(true)
        .append(true)
        .open(index_file_path);
    match file {
        Ok(_) => {
            file.unwrap().write_all(entry.as_bytes()).unwrap();
            1
        }
        Err(_) => {
            //println!("Error: {:?}", e);
            0
        }
    }
}

/// Checks if index file exists.
/// If it does, set index number to last index number + 1.
/// If it doesn't, create index file.
/// *Returns* the next index number available.
pub fn initialize_index_file(index_file_path:&str) -> i32 {
    let index_file = read_to_string(index_file_path);
    match index_file {
        Ok(file) => {
            let lines: Vec<&str> = file.split("\n").collect();
            if lines.len() < 2 {
                return lines.len() as i32 - 1;
            }
            let last_line = lines.get(lines.len()-2).unwrap();
            println!("Last line: {}", last_line);
            let last_index = last_line.split("\t").collect::<Vec<&str>>()[0];
            println!("Last index: {}", last_index);
            let idx_number = last_index.parse::<i32>();
            match idx_number {
                Ok(idx) => {return idx + 1;},
                Err(e) => {
                    println!("Error parsing index number: {:?}", e);
                    panic!("Idx file exists, but can't read last idx number. Panic button!");
                }
            }
        }
        Err(e) => {
            if e.kind() == std::io::ErrorKind::NotFound {
                println!("Index file not found. Creating index file...");
                let mut file = File::create(index_file_path).unwrap();
                file.write_all(b"Index\tTitle\tID\tLanguage\n").unwrap();
                0
            } else {
                // some other kind of error
                panic!("Something went wrong initializing index file. Panic button! Error: {:?}", e);
            }
        }
    }
}

/// Sees if a corresponding <b>.webm</b> video file exists in the directory.
/// *Returns* 1 if found, 0 if not found.
fn find_video(video_name: &str, video_id: &str, directory: &str) -> i32 {// Construct the expected video file name pattern
    let video_file_name = format!("{} [{}].webm", video_name, video_id);
    let video_file_path = Path::new(directory).join(video_file_name);
    if video_file_path.exists() {
        1
    } else {
        0
    }
}

fn index_files(idx: i32, file_name: &str, video_name: &str, video_id: &str, data_directory: &str) -> i32 {
    // renames the vtt file "{...}.vtt" to idx.vtt
    // and moves it from "{data_directory}/raw" to "{data_directory}/indexed/vtts"
    // and renames the video file "{...}.webm" to idx.webm (refer to video_path)
    // and moves it from "{data_directory}/raw" to "{data_directory}/indexed/videos"
    // if both successful, return 1
    // code:
    let video_dest = format!("{data_directory}/indexed/videos/{idx}.webm");
    let vtt_dest = format!("{data_directory}/indexed/vtts/{idx}.vtt");

    let video_path = format!("{data_directory}/raw/{video_name} [{video_id}].webm");

    let video_moved = rename(&video_path, &video_dest);
    let vtt_moved = rename(&format!("{data_directory}/raw/{file_name}"), vtt_dest);

    match video_moved {
        Ok(_) => {
            match vtt_moved {
                Ok(_) => {
                    1
                }
                Err(e) => {
                    println!("Error: {:?}", e);
                    rename(video_dest, video_path).unwrap();
                    0
                }
            }
        }
        Err(e) => {
            println!("Error: {:?}", e);
            0
        }
    }
}