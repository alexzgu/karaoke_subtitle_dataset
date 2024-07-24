mod index_data;
use index_data::index_raw_files;
mod parse_vtt;
use parse_vtt::parse_vtts;

/// Indexes raw files and parses VTT files.
fn main() {
    // read arguments
    index_raw_files(false); // optional
    parse_vtts(None, None); // custom_input_directory, custom_output_directory
    // remember to create the directories before running this!
}
