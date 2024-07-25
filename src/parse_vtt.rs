use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};
use regex::Regex;

const DATA_DIRECTORY: &str = "data/";

struct ParsedLine {
    start_time: String,
    end_time: String,
    position_percentage: i32,
    line_percentage: i32,
    text: String,
}

/// Parse all VTT files and save the parsed data as CSV files.
/// By default, it reads from `data/indexed/vtts` and writes to `data/parsed`.
pub fn parse_vtts(custom_input_directory: Option<&str>, custom_output_directory: Option<&str>) {
    let default_input_dir = format!("{}/indexed/vtts", DATA_DIRECTORY);
    let default_output_dir = format!("{}/parsed", DATA_DIRECTORY);

    let input_dir = custom_input_directory.unwrap_or(&default_input_dir);
    let output_dir = custom_output_directory.unwrap_or(&default_output_dir);

    if let Ok(entries) = fs::read_dir(input_dir) {
        for entry in entries.flatten() {
            if let Some(file_name) = entry.file_name().to_str() {
                parse_vtt(file_name, input_dir, output_dir);
            }
        }
    }
}


fn parse_vtt(file: &str, input_dir: &str, output_dir: &str) {
    let file_idx = file.trim_end_matches(".vtt");
    let input_file = format!("{}/{}.vtt", input_dir, file_idx);
    let output_file = format!("{}/{}.csv", output_dir, file_idx);

    let file = File::open(&input_file).expect("Failed to open input file");
    let reader = BufReader::new(file);
    let mut output = File::create(&output_file).expect("Failed to create output file");

    writeln!(output, "start,end,position,line,text").unwrap();

    let color_map = build_color_map(&input_file);
    let parsed_lines = parse_lines(reader, &color_map);

    for line in parsed_lines {
        writeln!(
            output,
            "{},{},{},{},\"{}\"",
            line.start_time,
            line.end_time,
            line.position_percentage,
            line.line_percentage,
            line.text
        ).unwrap();
    }
}

fn build_color_map(input_file: &str) -> HashMap<String, usize> {
    let file = File::open(input_file).expect("Failed to open input file");
    let reader = BufReader::new(file);
    let color_regex = Regex::new(r"cue\((c\.[^\)]+)\)").unwrap();
    let mut color_map = HashMap::new();
    let mut color_index = 1;

    for line in reader.lines().flatten() {
        for cap in color_regex.captures_iter(&line) {
            let color = cap[1].to_string();
            color_map.entry(color).or_insert_with(|| {
                let index = color_index;
                color_index += 1;
                index
            });
        }
    }

    color_map
}

fn parse_lines(reader: BufReader<File>, color_map: &HashMap<String, usize>) -> Vec<ParsedLine> {
    let mut parsed_lines = Vec::new();
    let mut current_line = ParsedLine {
        start_time: String::new(),
        end_time: String::new(),
        position_percentage: -1,
        line_percentage: -1,
        text: String::new(),
    };
    let mut in_cue_block = false;

    for line in reader.lines().flatten() {
        if line.starts_with("##") {
            in_cue_block = true;
            continue;
        }

        if !in_cue_block {
            continue;
        }

        if line.trim().is_empty() {
            if !current_line.start_time.is_empty() {
                current_line.text = unformatted_text(&current_line.text, color_map);
                parsed_lines.push(current_line);
                current_line = ParsedLine {
                    start_time: String::new(),
                    end_time: String::new(),
                    position_percentage: -1,
                    line_percentage: -1,
                    text: String::new(),
                };
            }
        } else if line.contains("-->") {
            let times: Vec<&str> = line.split_whitespace().collect();
            if times.len() < 3 {
                eprintln!("Invalid time format: {}", line);
                continue;
            }
            current_line.start_time = times[0].to_string();
            current_line.end_time = times[2].to_string();
            for item in times.iter().skip(3) {
                if let Some(percentage) = parse_percentage(item) {
                    if item.starts_with("position:") {
                        current_line.position_percentage = percentage;
                    } else if item.starts_with("line:") {
                        current_line.line_percentage = percentage;
                    }
                }
            }
        } else {
            current_line.text.push_str(&line.replace("\"", ""));
        }
    }

    parsed_lines
}

fn parse_percentage(item: &str) -> Option<i32> {
    item.split(':').nth(1)?.trim().trim_end_matches('%').parse().ok()
}

fn unformatted_text(text: &str, color_map: &HashMap<String, usize>) -> String {
    let re_clean = Regex::new(r"[ ,\n\t\u{200B}\u{007C}\u{0022}]").unwrap();
    let re_color = Regex::new(r"<c[^>]+>").unwrap();

    let cleaned_line = re_clean.replace_all(text, "");
    re_color.replace_all(&cleaned_line, |caps: &regex::Captures| {
        let color = &caps[0][1..caps[0].len() - 1];
        format!("<{}>", color_map.get(color).unwrap_or(&0))
    }).into_owned()
}