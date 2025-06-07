import hashlib


def compute_hash(file_type: str, raw_df) -> str:
    hasher = hashlib.sha256()
    hasher.update(file_type.encode())

    if len(raw_df) > 0:
        columns_str = ",".join(raw_df.columns)
        hasher.update(columns_str.encode())

    return hasher.hexdigest()


def process_dataframe(raw_df, header_row_index, data_start_row_index):
    processed_df = raw_df.copy()

    if header_row_index > 0:
        header_values = raw_df.iloc[header_row_index - 1].tolist()
        processed_df.columns = header_values

    start_row = max(data_start_row_index - 1, 0)
    processed_df = processed_df.iloc[start_row:].reset_index(drop=True)

    return processed_df
