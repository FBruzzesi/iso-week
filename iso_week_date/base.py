from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from enum import Enum
from typing import ClassVar, Generator, Literal, Type, TypeVar, Union, overload

from iso_week_date._utils import classproperty, format_err_msg, weeks_of_year
from iso_week_date.mixin import ComparatorMixin, ConverterMixin, ParserMixin

try:
    from typing import Self  # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import Self  # type: ignore[attr-defined]

BaseIsoWeek_T = TypeVar("BaseIsoWeek_T", bound=Union[str, date, datetime, "BaseIsoWeek"])


class InclusiveEnum(str, Enum):
    """Inclusive enum"""

    both = "both"
    left = "left"
    right = "right"
    neither = "neither"


_inclusive_values = tuple(e.value for e in InclusiveEnum)
Inclusive_T = Literal[_inclusive_values]  # type: ignore


class BaseIsoWeek(ABC, ComparatorMixin, ConverterMixin, ParserMixin):
    """
    Base abstract class for `IsoWeek` and `IsoWeekDate` classes.

    It defines the common interface for both classes and implements the common methods
    between them.

    Attributes:
        value_: stores the string value representing the iso-week date in the
            `_format` format
        offset_: class variable, stores the offset to be used when converting to
            and from `datetime` and `date` objects
        _pattern: class variable, stores the regex pattern to validate iso-week string
            format. Semiprivate, do not use it directly
        _format: class variable, stores the string format of the iso-week date.
            Semiprivate, do not use it directly
        _date_format: class variable, stores the string format with datetime conventions.
            Semiprivate, do not use it directly
    """

    offset_: ClassVar[timedelta] = timedelta(days=0)

    _pattern: ClassVar[re.Pattern]
    _format: ClassVar[str]
    _date_format: ClassVar[str]

    __slots__ = ("value_",)

    def __init__(self: Self, value: str) -> None:
        """
        Initializes `BaseIsoWeek` object from iso-week string.

        Arguments:
            value: iso-week string to initialize `BaseIsoWeek` object,
                must match the `_pattern` pattern of the class or a `ValueError` will be
                raised.
        """
        self.value_ = self._validate(value)

    @classmethod
    def _validate(cls: Type[Self], value: str) -> str:
        """Validates iso-week string format."""
        _match = re.match(cls._pattern, value)

        if not _match:
            raise ValueError(format_err_msg(cls._format, value))

        year, week = int(_match.group(1)), int(_match.group(2)[1:])

        if weeks_of_year(year) < week:
            raise ValueError(
                f"Invalid week number. Year {year} has only {weeks_of_year(year)} weeks."
            )

        return value

    def __repr__(self: Self) -> str:
        """Custom representation."""
        return f"{self.name}({self.value_}) with offset {self.offset_}"

    def __str__(self: Self) -> str:
        """String conversion operator, returns iso-week string value ignoring offset."""
        return self.value_

    @classproperty
    def _compact_pattern(cls: Type[Self]) -> re.Pattern:
        """Returns compiled compact pattern."""
        return re.compile(cls._pattern.pattern.replace(")-(", ")("))

    @classproperty
    def _compact_format(cls: Type[Self]) -> str:
        """Returns compact format as string."""
        return cls._format.replace("-", "")

    @property
    def name(self: Self) -> str:
        """Returns class name."""
        return self.__class__.__name__

    @property
    def year(self: Self) -> int:
        """
        Returns year number as integer.

        Usage:
        ```py
        from iso_week_date import IsoWeek, IsoWeekDate

        IsoWeek("2023-W01").year # 2023
        IsoWeekDate("2023-W01-1").year # 2023
        ```
        """
        return int(self.value_[:4])

    @property
    def week(self: Self) -> int:
        """
        Returns week number as integer.

        Usage:
        ```py
        from iso_week_date import IsoWeek, IsoWeekDate

        IsoWeek("2023-W01").week  # 1
        IsoWeekDate("2023-W01-1").week  # 1
        ```
        """
        return int(self.value_[6:8])

    @abstractmethod
    def __add__(
        self: Self, other: Union[int, timedelta]
    ) -> BaseIsoWeek:  # pragma: no cover
        """Implementation of addition operator."""
        ...

    @overload
    def __sub__(
        self: Self, other: Union[int, timedelta]
    ) -> BaseIsoWeek:  # pragma: no cover
        """Annotation for subtraction with `int` and `timedelta`"""
        ...

    @overload
    def __sub__(self: Self, other: BaseIsoWeek) -> int:  # pragma: no cover
        """Annotation for subtraction with other `BaseIsoWeek`"""
        ...

    @abstractmethod
    def __sub__(
        self: Self, other: Union[int, timedelta, BaseIsoWeek]
    ) -> Union[int, BaseIsoWeek]:  # pragma: no cover
        """Implementation of subtraction operator."""
        ...

    def __next__(self: Self) -> BaseIsoWeek:
        """Implementation of next operator."""
        return self + 1

    @classmethod
    def range(
        cls: Type[Self],
        start: BaseIsoWeek_T,
        end: BaseIsoWeek_T,
        step: int = 1,
        inclusive: Inclusive_T = "both",
        as_str: bool = True,
    ) -> Generator[Union[str, BaseIsoWeek], None, None]:
        """
        Generates `BaseIsoWeek` (or `str`) between `start` and `end` values with given
        `step`.

        `inclusive` parameter can be used to control inclusion of `start` and/or
        `end` week values.

        If `as_str` is flagged as `True`, it will return str values, otherwise it will
        return `BaseIsoWeek` objects.

        Arguments:
            start: starting value. It can be `BaseIsoWeek`, `date`, `datetime` or `str`
            end: ending value. It can be `BaseIsoWeek`, `date`, `datetime` or `str`
            step: step between generated values, must be positive integer
            inclusive: inclusive type, can be one of "both", "left", "right" or "neither"
            as_str: whether to return `str` or `BaseIsoWeek` object

        Returns:
            generator of `IsoWeeks`/`str` between `start` and `end` values with given
            `step`

        Raises:
            ValueError: if `start` > `end`,
                `inclusive` not one of "both", "left", "right" or "neither",
                `step` is not strictly positive
            TypeError: if `step` is not int

        Usage:
        ```python
        from iso_week_date import IsoWeek

        tuple(IsoWeek.range(
            start="2023-W01",
            end="2023-W07",
            step=2,
            inclusive="both",
            as_str=True)
            ) # ('2023-W01', '2023-W03', '2023-W05', '2023-W07')
        ```
        """

        _start: BaseIsoWeek = cls._cast(start)
        _end: BaseIsoWeek = cls._cast(end)

        if _start > _end:
            raise ValueError(
                f"`start` must be before `end` value, found: {_start} > {_end}"
            )

        if not isinstance(step, int):
            raise TypeError(f"`step` must be integer, found {type(step)}")

        if step < 1:
            raise ValueError(
                f"`step` value must be greater than or equal to 1, found {step}"
            )

        if inclusive not in _inclusive_values:
            raise ValueError(
                f"Invalid `inclusive` value. Must be one of {_inclusive_values}"
            )

        _delta = _end - _start
        range_start = 0 if inclusive in ("both", "left") else 1
        range_end = _delta + 1 if inclusive in ("both", "right") else _delta

        weeks_range: Generator[Union[str, BaseIsoWeek], None, None] = (
            (_start + i).to_string() if as_str else _start + i
            for i in range(range_start, range_end, step)
        )

        return weeks_range
