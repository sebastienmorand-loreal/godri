"""Range parsing utilities for slides and other operations."""

import logging
from typing import List, Set, Optional
import re


class RangeParser:
    """Utility class for parsing range expressions like '1-3,5,7-9'."""

    def __init__(self):
        """Initialize range parser."""
        self.logger = logging.getLogger(__name__)

    def parse_range(self, range_str: str) -> List[int]:
        """Parse range string and return list of numbers.

        Args:
            range_str: Range string like '1-3,5,7-9' or '2'

        Returns:
            Sorted list of unique numbers

        Raises:
            ValueError: If range string is invalid
        """
        if not range_str or not range_str.strip():
            return []

        numbers: Set[int] = set()

        # Split by comma and process each part
        parts = [part.strip() for part in range_str.split(",")]

        for part in parts:
            if not part:
                continue

            # Check if it's a range (contains dash)
            if "-" in part:
                self._parse_range_part(part, numbers)
            else:
                # Single number
                try:
                    num = int(part)
                    if num < 1:
                        raise ValueError(f"Numbers must be positive, got: {num}")
                    numbers.add(num)
                except ValueError as e:
                    raise ValueError(f"Invalid number in range: '{part}'") from e

        if not numbers:
            raise ValueError(f"No valid numbers found in range: '{range_str}'")

        return sorted(list(numbers))

    def _parse_range_part(self, part: str, numbers: Set[int]) -> None:
        """Parse a range part like '1-3' and add numbers to set.

        Args:
            part: Range part string
            numbers: Set to add numbers to

        Raises:
            ValueError: If range part is invalid
        """
        # Split by dash
        range_parts = part.split("-")

        if len(range_parts) != 2:
            raise ValueError(f"Invalid range format: '{part}'. Expected format: 'start-end'")

        start_str, end_str = range_parts

        try:
            start = int(start_str.strip())
            end = int(end_str.strip())
        except ValueError as e:
            raise ValueError(f"Invalid numbers in range: '{part}'") from e

        if start < 1 or end < 1:
            raise ValueError(f"Range numbers must be positive: '{part}'")

        if start > end:
            raise ValueError(f"Range start must be <= end: '{part}'")

        # Add all numbers in range
        for num in range(start, end + 1):
            numbers.add(num)

    def validate_range(self, range_str: str, max_value: Optional[int] = None) -> bool:
        """Validate range string without parsing.

        Args:
            range_str: Range string to validate
            max_value: Maximum allowed value (optional)

        Returns:
            True if range is valid
        """
        try:
            numbers = self.parse_range(range_str)
            if max_value is not None and max(numbers) > max_value:
                return False
            return True
        except ValueError:
            return False

    def format_range(self, numbers: List[int]) -> str:
        """Format list of numbers into compact range string.

        Args:
            numbers: List of numbers to format

        Returns:
            Compact range string like '1-3,5,7-9'
        """
        if not numbers:
            return ""

        # Sort and deduplicate
        sorted_numbers = sorted(set(numbers))

        if not sorted_numbers:
            return ""

        ranges = []
        start = sorted_numbers[0]
        end = start

        for i in range(1, len(sorted_numbers)):
            current = sorted_numbers[i]

            if current == end + 1:
                # Continue current range
                end = current
            else:
                # End current range and start new one
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = current
                end = current

        # Add final range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ",".join(ranges)


# Global range parser instance
range_parser = RangeParser()
