"""Color conversion utilities for Google Sheets and other APIs."""

import logging
import re
from typing import Dict, Tuple


class ColorConverter:
    """Utility class for converting colors between different formats."""

    def __init__(self):
        """Initialize color converter."""
        self.logger = logging.getLogger(__name__)

        # Common color names to RGB (0.0-1.0 scale for Google APIs)
        self.color_names = {
            "white": (1.0, 1.0, 1.0),
            "black": (0.0, 0.0, 0.0),
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 0.8, 0.0),
            "blue": (0.0, 0.0, 1.0),
            "yellow": (1.0, 1.0, 0.0),
            "cyan": (0.0, 1.0, 1.0),
            "magenta": (1.0, 0.0, 1.0),
            "orange": (1.0, 0.65, 0.0),
            "purple": (0.5, 0.0, 0.5),
            "pink": (1.0, 0.75, 0.8),
            "brown": (0.65, 0.16, 0.16),
            "gray": (0.5, 0.5, 0.5),
            "grey": (0.5, 0.5, 0.5),
            "lightgray": (0.83, 0.83, 0.83),
            "lightgrey": (0.83, 0.83, 0.83),
            "darkgray": (0.66, 0.66, 0.66),
            "darkgrey": (0.66, 0.66, 0.66),
        }

    def convert_to_google_rgb(self, color: str) -> Dict[str, float]:
        """Convert color (hex, name, or RGB) to Google Sheets API RGB format (0.0-1.0).

        Args:
            color: Color in various formats (hex, name, rgb)

        Returns:
            Dictionary with red, green, blue keys (0.0-1.0 scale)
        """
        color_lower = color.lower().strip()

        # Check if it's a named color
        if color_lower in self.color_names:
            r, g, b = self.color_names[color_lower]
            return {"red": r, "green": g, "blue": b}

        # Check if it's a hex color
        hex_match = re.match(r"^#?([0-9a-fA-F]{6})$", color.strip())
        if hex_match:
            hex_color = hex_match.group(1)
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return {"red": r, "green": g, "blue": b}

        # Check if it's RGB format like "rgb(255, 0, 0)"
        rgb_match = re.match(r"^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", color.strip(), re.IGNORECASE)
        if rgb_match:
            r = int(rgb_match.group(1)) / 255.0
            g = int(rgb_match.group(2)) / 255.0
            b = int(rgb_match.group(3)) / 255.0
            return {"red": r, "green": g, "blue": b}

        # Default to black if color not recognized
        self.logger.warning("Unrecognized color format '%s', defaulting to black", color)
        return {"red": 0.0, "green": 0.0, "blue": 0.0}

    def convert_to_hex(self, google_rgb: Dict[str, float]) -> str:
        """Convert Google RGB format to hex color.

        Args:
            google_rgb: Dictionary with red, green, blue keys (0.0-1.0 scale)

        Returns:
            Hex color string like '#FF0000'
        """
        r = int(google_rgb.get("red", 0.0) * 255)
        g = int(google_rgb.get("green", 0.0) * 255)
        b = int(google_rgb.get("blue", 0.0) * 255)

        return f"#{r:02X}{g:02X}{b:02X}"

    def get_supported_colors(self) -> Dict[str, str]:
        """Get dictionary of supported color names and their hex values.

        Returns:
            Dictionary mapping color names to hex values
        """
        result = {}
        for name, (r, g, b) in self.color_names.items():
            hex_color = self.convert_to_hex({"red": r, "green": g, "blue": b})
            result[name] = hex_color
        return result


# Global color converter instance
color_converter = ColorConverter()
