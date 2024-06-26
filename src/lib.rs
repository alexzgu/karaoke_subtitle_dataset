mod index_data;
use index_data::index_raw_files;

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn some_test() {
        index_raw_files();
    }
}