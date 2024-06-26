use std::fs::File;
use std::io::{BufRead, BufReader, Write}; // Import Write trait
use regex::Regex;
use crate::index_data;


pub fn parse_vtts() {
    let data_directory = "data/";
    let index_file_path: &str = &format!("{data_directory}/indexed/index.tsv");
    let current_idx: i32 = index_data::initialize_index_file(index_file_path);
    for i in 0..current_idx {
        parse_vtt(i, data_directory);
    }
}

fn parse_vtt(file_idx: i32, data_directory: &str) {

    let input_file = format!("{}/indexed/vtts/{}.vtt", data_directory, file_idx);
    let output_file = format!("{}/parsed/{}.csv", data_directory, file_idx);

    // Open input file
    let file = File::open(input_file).expect("Failed to open input file");
    let reader = BufReader::new(file);

    // Open output file
    let mut output = File::create(output_file).expect("Failed to create output file");

    // Write CSV header
    writeln!(output, "start_time,end_time,position_percentage,line_percentage,text").unwrap();

    // State variables
    let mut start_time = String::new();
    let mut end_time = String::new();
    let mut position_percentage = -1;
    let mut line_percentage = -1;
    let mut text = String::new();
    let mut in_cue_block = false;
    let mut line_count = 0; // For debugging

    // Process each line
    for line in reader.lines() {
        let line = line.expect("Failed to read line");
        line_count += 1;

        if line.starts_with("##") {
            // Found end of metadata section
            in_cue_block = true;
            continue;
        }

        if in_cue_block {
            if line.trim().is_empty() {
                // Empty line indicates end of cue block
                if !start_time.is_empty() {
                    // Output the cue block as CSV line
                    writeln!(output, "{},{},{},{},\"{}\"", start_time, end_time, position_percentage, line_percentage, unformatted_text(&text)).unwrap();
                }
                // Reset for the next cue block
                start_time.clear();
                end_time.clear();
                position_percentage = -1;
                line_percentage = -1;
                text.clear();
                continue;
            }

            // Parse start_time and end_time
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
                            if let Some(percentage) = item.split(":").nth(1) {
                                if let Ok(parsed_percentage) = percentage.trim().trim_end_matches('%').parse::<i32>() {
                                    position_percentage = parsed_percentage;
                                }
                            }
                        } else if item.starts_with("line:") {
                            if let Some(percentage) = item.split(":").nth(1) {
                                if let Ok(parsed_percentage) = percentage.trim().trim_end_matches('%').parse::<i32>() {
                                    line_percentage = parsed_percentage;
                                }
                            }
                        } else {
                            // For console printing or additional handling
                            println!("Line [{}], unprocessed: {}", line_count, item);
                        }
                    }
                }
            } else {
                // Process text line
                // Accumulate text
                let cleaned_line = line.replace("\"", "\\\"");

                text.push_str(&cleaned_line);
                //text.push(' '); // Add space to separate lines in the text field
            }
        }
    }
}

fn unformatted_text(text: &String) -> String {
    let mut cleaned_line = text.clone();
    let re = Regex::new(r"[ ,'?\t\u{200B}]").unwrap();
    cleaned_line = re.replace_all(&cleaned_line, "").to_string();
    // pattern to replace any "<...>" tags with "|"
    let re = Regex::new(r"<[^>]*>").unwrap();
    cleaned_line = re.replace_all(&cleaned_line, "|").to_string();
    cleaned_line = cleaned_line.replace("||", "|");
    // exclude first two and last two characters
    cleaned_line = cleaned_line.chars().skip(2).take(cleaned_line.len() - 4).collect();
    cleaned_line
}