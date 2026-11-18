"""Юнит-тесты функции валидации числовых полей форм parse_int app/main.py."""
import pytest

from app.main import parse_int

@pytest.mark.parametrize("raw_value, expected", [
    ('-5', -5), # negative
    ('0', 0), # zero
    ('12', 12), # positive
    (" 12 ", 12), # whitespaces around int
    ('007', 7) # leading zeros
    ])
def test_valid_raw_value(raw_value, expected):
    assert parse_int(raw_value, "Any Field Label") == expected


@pytest.mark.parametrize("raw_value", [
    "", # empty
    " ", # whitespaces
    "echpochmac", # not numeric
    "-0.7", "0.0", "0.48", # not integer
    "8%", "8 8", "8a", # symbols and nums combinations
    None, # TypeError
    ])
def test_raw_value_invalid(raw_value):
    with pytest.raises(ValueError, match="Поле \"Any Field Label\" должно быть целым числом."):
        parse_int(raw_value, "Any Field Label")


@pytest.mark.parametrize("raw_value, min_value, expected", [
    ('-5', -10, -5), # negative
    ('12', 10, 12), # positive
    ('0', 0, 0), # equal to the lower border
    ])
def test_min_value_valid(raw_value, min_value, expected):
    assert parse_int(raw_value, "Any Field Label", min_value) == expected


@pytest.mark.parametrize("raw_value, min_value", [
    ('-5', -4), # negative
    ('12', 50), # positive
    ])
def test_min_value_invalid(raw_value, min_value):
    with pytest.raises(ValueError, match="Поле \"Any Field Label\" должно быть не меньше " + str(min_value)+ "."):
        parse_int(raw_value, "Any Field Label", min_value)


@pytest.mark.parametrize("raw_value, max_value, expected", [
    ('-5', -1, -5), # negative
    ('12', 50, 12), # positive
    ('0', 0, 0), # equal to the higher border
    ])
def test_max_value_valid(raw_value, max_value, expected):
    assert parse_int(raw_value, "Any Field Label", None, max_value) == expected


@pytest.mark.parametrize("raw_value, max_value", [
    ('-5', -10), # negative
    ('12', 10), # positive
    ])
def test_max_value_invalid(raw_value, max_value):
    with pytest.raises(ValueError, match="Поле \"Any Field Label\" должно быть не больше " + str(max_value)+ "."):
        parse_int(raw_value, "Any Field Label", None, max_value)


@pytest.mark.parametrize("raw_value, min_value, max_value, expected", [
    ('-5', -100, -1, -5), # negative
    ('12', 10, 50, 12), # positive
    ('0', 0, 0, 0), # equal to borders
    ('0', -1, 1, 0) # [neg, pos]
    ])
def test_both_borders_valid(raw_value, min_value, max_value, expected):
    assert parse_int(raw_value, "Any Field Label", min_value, max_value) == expected