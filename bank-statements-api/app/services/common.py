import hashlib

from app.services.schema_detection.heuristic_schema_detector import find_header_values


def _hash_columns(file_type: str, columns) -> str:
    hasher = hashlib.sha256()
    hasher.update(file_type.encode())
    if columns:
        hasher.update(",".join(str(col) for col in columns).encode())
    return hasher.hexdigest()


def compute_hash(file_type: str, raw_df) -> str:
    if len(raw_df) == 0:
        return _hash_columns(file_type, [])
    return _hash_columns(file_type, find_header_values(raw_df))


def compute_legacy_hash(file_type: str, raw_df) -> str:
    if len(raw_df) == 0:
        return _hash_columns(file_type, [])
    return _hash_columns(file_type, list(raw_df.columns))


def find_metadata_with_fallback(file_type: str, raw_df, finder):
    primary_hash = compute_hash(file_type, raw_df)
    metadata = finder(primary_hash)
    if metadata is not None:
        return metadata

    legacy_hash = compute_legacy_hash(file_type, raw_df)
    if legacy_hash == primary_hash:
        return None
    return finder(legacy_hash)


def process_dataframe(raw_df, header_row_index, data_start_row_index):
    processed_df = raw_df.copy()

    if header_row_index > 0:
        header_values = raw_df.iloc[header_row_index - 1].tolist()
        processed_df.columns = header_values

    start_row = max(data_start_row_index - 1, 0)
    processed_df = processed_df.iloc[start_row:].reset_index(drop=True)

    return processed_df
