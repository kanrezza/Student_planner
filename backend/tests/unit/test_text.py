import unicodedata

from app.lib.text import ci_key, contains_ci, nfc

COMPOSED = "Giáo dục thể chất"  # NFC: chữ có dấu dựng sẵn
DECOMPOSED = unicodedata.normalize("NFD", COMPOSED)  # NFD: chữ cái + dấu tổ hợp


def test_nfd_and_nfc_differ_as_raw_strings():
    assert DECOMPOSED != COMPOSED


def test_nfc_normalizes_and_strips():
    assert nfc(f"  {DECOMPOSED}  ") == COMPOSED


def test_ci_key_ignores_case_and_normalization_form():
    assert ci_key(DECOMPOSED.upper()) == ci_key(COMPOSED)


def test_contains_ci_matches_vietnamese_subject_names():
    assert contains_ci("GIÁO DỤC THỂ CHẤT 2", COMPOSED)
    assert contains_ci(unicodedata.normalize("NFD", "giáo dục thể chất 2"), COMPOSED)
    assert not contains_ci("Giải tích 1", COMPOSED)
