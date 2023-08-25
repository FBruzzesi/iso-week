from contextlib import nullcontext as do_not_raise
from datetime import date, datetime, timedelta

import pytest

from iso_week_date import IsoWeek, IsoWeekDate
from iso_week_date.base import BaseIsoWeek
from iso_week_date.mixin import IsoWeekProtocol


class CustomWeek(IsoWeek):
    offset_ = timedelta(days=1)


class CustomWeekDate(IsoWeekDate):
    offset_ = timedelta(days=1)


isoweek = IsoWeek("2023-W01")
isoweekdate = IsoWeekDate("2023-W01-1")
customweek = CustomWeek("2023-W01")
customweekdate = CustomWeekDate("2023-W01-1")


class NotIsoWeek:
    """Test class for IsoWeekProtocol without required attributes"""

    pass


def test_protocol():
    """
    Tests that:

    - `IsoWeekProtocol` is protocol and cannot be instantiated
    - `NotIsoWeek` is not a valid implementation of IsoWeekProtocol
    - `IsoWeek` and `IsoWeekDate` are valid implementation of IsoWeekProtocol
    """
    with pytest.raises(TypeError):
        IsoWeekProtocol()

    assert not isinstance(NotIsoWeek, IsoWeekProtocol)
    assert isinstance(IsoWeek("2023-W01"), IsoWeekProtocol)
    assert isinstance(IsoWeekDate("2023-W01-1"), IsoWeekProtocol)


# Mixin's methods will be tested directly using the `IsoWeek` and `IsoWeekDate` classes.

## ParserMixin


@pytest.mark.parametrize(
    "_cls, _method, value, expected",
    [
        (IsoWeek, "from_string", "2023-W01", isoweek),
        (IsoWeek, "from_compact", "2023W01", isoweek),
        (IsoWeek, "from_date", date(2023, 1, 2), isoweek),
        (IsoWeek, "from_datetime", datetime(2023, 1, 2, 12), isoweek),
        (IsoWeekDate, "from_string", "2023-W01-1", isoweekdate),
        (IsoWeekDate, "from_compact", "2023W011", isoweekdate),
        (IsoWeekDate, "from_date", date(2023, 1, 2), isoweekdate),
        (IsoWeekDate, "from_datetime", datetime(2023, 1, 2, 12), isoweekdate),
    ],
)
def test_valid_parser(_cls, _method, value, expected):
    """Test ParserMixin methods with valid values"""

    assert getattr(_cls, _method)(value) == expected
    if _method != "from_compact":
        assert getattr(_cls, "_cast")(value) == expected


@pytest.mark.parametrize(
    "_cls, _method, value, context",
    [
        (IsoWeekDate, "from_string", 1234, pytest.raises(TypeError)),
        (IsoWeekDate, "from_compact", date(2023, 1, 2), pytest.raises(TypeError)),
        (IsoWeekDate, "from_date", (1, 2, 3, 4), pytest.raises(TypeError)),
        (IsoWeekDate, "from_datetime", "2023-W01", pytest.raises(TypeError)),
        (IsoWeek, "_cast", 1234, pytest.raises(NotImplementedError)),
        (IsoWeek, "_cast", (1, 2, 3, 4), pytest.raises(NotImplementedError)),
    ],
)
def test_invalid_parser(_cls, _method, value, context):
    """Test ParserMixin methods with invalid value types"""

    with context:
        getattr(_cls, _method)(value)


## ConverterMixin


@pytest.mark.parametrize("iso_obj", [isoweek, isoweekdate])
def test_converter(iso_obj):
    """Tests ConverterMixin methods"""

    assert iso_obj.to_string() == iso_obj.value_
    assert iso_obj.to_compact() == iso_obj.value_.replace("-", "")

    assert isinstance(iso_obj.to_date(), date)
    assert isinstance(iso_obj.to_datetime(), datetime)


## ComparatorMixin


@pytest.mark.parametrize(
    "value, other, comparison_op, expected",
    [
        (isoweek, "2023-W01", "__eq__", True),
        (isoweek, "2023-W02", "__ne__", True),
        (isoweek, "2023-W01", "__le__", True),
        (isoweek, "2023-W02", "__le__", True),
        (isoweek, "2023-W01", "__ge__", True),
        (isoweek, "2022-W52", "__ge__", True),
        (isoweek, "2023-W02", "__lt__", True),
        (isoweek, "2022-W52", "__gt__", True),
        (isoweekdate, "2023-W02-1", "__eq__", False),
        (isoweekdate, "2023-W01-1", "__ne__", False),
        (isoweekdate, "2022-W52-1", "__le__", False),
        (isoweekdate, "2023-W02-1", "__ge__", False),
        (isoweekdate, "2023-W01-1", "__lt__", False),
        (isoweekdate, "2022-W52-1", "__lt__", False),
        (isoweekdate, "2023-W01-1", "__gt__", False),
        (isoweekdate, "2023-W02-1", "__gt__", False),
        (isoweek, customweek, "__eq__", False),
        (isoweekdate, customweekdate, "__ne__", True),
    ],
)
def test_comparisons(value, other, comparison_op, expected):
    """Tests comparison methods of ISO Week classes"""
    _other = value.__class__._cast(other)
    assert getattr(value, comparison_op)(_other) == expected


@pytest.mark.parametrize(
    "other", ["2023-W01", datetime(2023, 1, 1), date(2023, 1, 1), 123, 42.0, customweek]
)
def test_eq_other_types(other):
    """Tests __eq__ method of IsoWeek class with other types"""
    assert not isoweek == other


@pytest.mark.parametrize(
    "other, comparison_op, err_msg",
    [
        ("2023-W01", "__lt__", "Cannot compare `IsoWeek` with type"),
        ("abc", "__gt__", "Cannot compare `IsoWeek` with type"),
        (123, "__ge__", "Cannot compare `IsoWeek` with type"),
        (list("abc"), "__le__", "Cannot compare `IsoWeek` with type"),
        (customweek, "__lt__", "Cannot compare `IsoWeek`'s with different offsets"),
        (customweek, "__gt__", "Cannot compare `IsoWeek`'s with different offsets"),
        (customweek, "__ge__", "Cannot compare `IsoWeek`'s with different offsets"),
        (customweek, "__le__", "Cannot compare `IsoWeek`'s with different offsets"),
    ],
)
def test_comparisons_invalid(other, comparison_op, err_msg):
    """Tests comparison methods of IsoWeek class with invalid arguments"""
    with pytest.raises(TypeError) as exc_info:
        getattr(isoweek, comparison_op)(other)

    assert err_msg in str(exc_info.value)
