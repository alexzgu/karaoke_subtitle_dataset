use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader, Write}; // Import Write trait
use regex::Regex;


/// Parses all VTT files and outputs CSV files containing parsed data.
/// The input location is data/indexed/vtts/ by default, but a custom input directory can be specified.
/// The output location is data/parsed/ by default, but a custom output directory can be specified.
pub fn parse_vtts(custom_input_directory: Option<&str>, custom_output_directory: Option<&str>) {
    let data_directory = "data/";
    // read into data/indexed/vtts/
    let mut dir_path = format!("{}/indexed/vtts", data_directory);
    match custom_input_directory {
        Some(input_directory) => { dir_path = format!("{}", input_directory); }
        None => {}
    }

    // Read the directory
    if let Ok(entries) = std::fs::read_dir(&dir_path) {
        for entry in entries {
            if let Ok(entry) = entry {
                parse_vtt(entry.file_name().to_str().unwrap(), data_directory, custom_output_directory);
            }
        }
    }
}

/// Parses a single VTT file and outputs the parsed data to a CSV file.
fn parse_vtt(file: &str, data_directory: &str, custom_output_directory: Option<&str>) {
    let file_idx = file.trim_end_matches(".vtt");
    let input_file = format!("{}/indexed/vtts/{}.vtt", data_directory, file_idx);
    let output_file = match custom_output_directory {
        Some(dir) => format!("{}", dir),
        None => format!("{}/parsed/{}.csv", data_directory, file_idx)
    };
    let file = File::open(input_file.clone()).expect("Failed to open input file");
    let reader = BufReader::new(file);
    let mut output = File::create(output_file).expect("Failed to create output file");

    writeln!(output, "start,end,position,line,text").unwrap();

    let mut color_map = HashMap::new();
    let mut color_index = 1;
    // Updated regex pattern to match cue() and capture its contents
    let color_regex = Regex::new(r"cue\((c\.[^\)]+)\)").unwrap();

    // First pass: build the color map with the new regex pattern
    for line in reader.lines() {
        let line = line.expect("Failed to read line");
        for cap in color_regex.captures_iter(&line) {
            let color = cap.get(1).unwrap().as_str(); // Capture the content inside cue()
            color_map.entry(color.to_string()).or_insert_with(|| {
                let current_index = color_index;
                color_index += 1;
                current_index
            });
        }
    }

    // Reset the file reader
    let file = File::open(input_file).expect("Failed to open input file");
    let reader = BufReader::new(file);

    let mut start_time = String::new();
    let mut end_time = String::new();
    let mut position_percentage = -1;
    let mut line_percentage = -1;
    let mut text = String::new();
    let mut in_cue_block = false;

    // Second pass: process the file
    for line in reader.lines() {
        let line = line.expect("Failed to read line");

        if line.starts_with("##") {
            in_cue_block = true;
            continue;
        }

        if in_cue_block {
            if line.trim().is_empty() {
                if !start_time.is_empty() {
                    writeln!(
                        output,
                        "{},{},{},{},\"{}\"",
                        start_time,
                        end_time,
                        position_percentage,
                        line_percentage,
                        unformatted_text(&text, &color_map)
                    )
                    .unwrap();
                }
                start_time.clear();
                end_time.clear();
                position_percentage = -1;
                line_percentage = -1;
                text.clear();
                continue;
            }

            if line.contains("-->") {
                let times: Vec<&str> = line.split_whitespace().collect();
                if times.len() < 3 {
                    eprintln!("Invalid time format: {}", line);
                    panic!("Invalid time format");
                }
                start_time = times[0].to_string();
                end_time = times[2].to_string();
                if times.len() > 3 {
                    for item in times.iter().skip(3) {
                        if item.starts_with("position:") {
                            if let Some(parsed_percentage) = parse_percentage(item) {
                                position_percentage = parsed_percentage;
                            }
                        } else if item.starts_with("line:") {
                            if let Some(parsed_percentage) = parse_percentage(item) {
                                line_percentage = parsed_percentage;
                            }
                        }

                    }
                }
            } else {
                let cleaned_line = line.replace("\"", "");
                text.push_str(&cleaned_line);
            }
        }
    }
}

fn parse_percentage(item: &str) -> Option<i32> {
    item.split(":").nth(1)
        .and_then(|percentage| percentage.trim().trim_end_matches('%').parse::<i32>().ok())
}

fn unformatted_text(text: &str, color_map: &HashMap<String, usize>) -> String {
    let mut cleaned_line = text.to_string();

    // Remove all spaces, commas, newlines, tabs, zero-width space, pipe, and double quotes
    let re = Regex::new(r"[ ,\n\t\u{200B}\u{007C}\u{0022}]").unwrap();
    cleaned_line = re.replace_all(&cleaned_line, "").to_string();

    // Replace color tags with indexed versions
    let re = Regex::new(r"<c[^>]+>").unwrap();
    cleaned_line = re.replace_all(&cleaned_line, |caps: &regex::Captures| {
        let color = caps.get(0).unwrap().as_str();
        let color = &color[1..color.len() - 1]; // Remove the < and > characters
        format!("<{}>", color_map.get(color).unwrap_or(&0))
    }).to_string();

    cleaned_line
}