import pandas as pd

from app.services.common import compute_hash, compute_legacy_hash, find_metadata_with_fallback


def _header_on_first_row():
    return pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02"],
            "Amount": ["100.00", "-5.00"],
            "Description": ["A", "B"],
        }
    )


def _preamble_frame(title):
    return pd.DataFrame(
        [
            ["Conta", "0217005412400 - EUR", "", ""],
            ["Data mov.", "Descrição", "Montante", "Saldo"],
            ["11-12-2024", "TRF JORGE COSTA", "51,27", "10.536,05"],
            ["07-12-2024", "COM MANUTENÇÃO", "-10,40", "10.515,25"],
        ],
        columns=[title, '="0217005412400"', "Unnamed: 2", "Unnamed: 3"],
    )


class TestComputeHash:
    def test_header_on_first_row_matches_legacy_hash(self):
        df = _header_on_first_row()
        assert compute_hash("CSV", df) == compute_legacy_hash("CSV", df)

    def test_preamble_hash_differs_from_legacy(self):
        df = _preamble_frame("Consultar saldos - 27-06-2026")
        assert compute_hash("TSV", df) != compute_legacy_hash("TSV", df)

    def test_preamble_hash_is_stable_when_title_row_changes(self):
        first = _preamble_frame("Consultar saldos - 27-06-2026")
        reexport = _preamble_frame("Consultar saldos - 15-08-2026")
        assert compute_hash("TSV", first) == compute_hash("TSV", reexport)
        assert compute_legacy_hash("TSV", first) != compute_legacy_hash("TSV", reexport)

    def test_empty_frame_hashes_file_type_only(self):
        empty = pd.DataFrame()
        assert compute_hash("CSV", empty) == compute_legacy_hash("CSV", empty)


class TestFindMetadataWithFallback:
    def test_returns_primary_match_without_legacy_lookup(self):
        df = _preamble_frame("Consultar saldos - 27-06-2026")
        primary = compute_hash("TSV", df)
        seen = []

        def finder(file_hash):
            seen.append(file_hash)
            return "metadata" if file_hash == primary else None

        assert find_metadata_with_fallback("TSV", df, finder) == "metadata"
        assert seen == [primary]

    def test_falls_back_to_legacy_hash(self):
        df = _preamble_frame("Consultar saldos - 27-06-2026")
        legacy = compute_legacy_hash("TSV", df)

        def finder(file_hash):
            return "legacy-metadata" if file_hash == legacy else None

        assert find_metadata_with_fallback("TSV", df, finder) == "legacy-metadata"

    def test_no_legacy_lookup_when_hashes_match(self):
        df = _header_on_first_row()
        calls = []

        def finder(file_hash):
            calls.append(file_hash)
            return None

        assert find_metadata_with_fallback("CSV", df, finder) is None
        assert len(calls) == 1
