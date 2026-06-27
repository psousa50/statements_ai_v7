def decode_statement_bytes(file_content: bytes) -> str:
    for encoding in ("utf-8", "cp1252"):
        try:
            return file_content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_content.decode("cp1252", errors="replace")
