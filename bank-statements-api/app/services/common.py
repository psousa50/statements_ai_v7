import hashlib


def compute_hash(filename: str, file_content: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(filename.encode())
    hasher.update(file_content)
    return hasher.hexdigest()


def process_dataframe(raw_df, header_row_index, data_start_row_index):
    processed_df = raw_df.copy()

    if header_row_index > 0:
        header_values = raw_df.iloc[header_row_index - 1].tolist()
        processed_df.columns = header_values

    processed_df = processed_df.iloc[data_start_row_index - 1 :].reset_index(drop=True)

    return processed_df
