mod index_data;
use index_data::index_raw_files;
mod parse_vtt;
use parse_vtt::parse_vtts;

fn main() {
    index_raw_files();
    parse_vtts();
}