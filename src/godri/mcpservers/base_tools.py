"""Base class for MCP tool modules."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP


class BaseTools(ABC):
    """Base class for MCP tool modules."""

    def __init__(self):
        """Initialize base tools."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def register_tools(self, server: FastMCP) -> None:
        """Register all tools with the MCP server.

        Args:
            server: FastMCP server instance
        """
        pass

    def handle_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Handle errors consistently across all tools.

        Args:
            error: Exception that occurred
            operation: Description of the operation that failed

        Returns:
            Error response dictionary
        """
        error_msg = f"Error in {operation}: {str(error)}"
        self.logger.error(error_msg, exc_info=True)

        return {"error": error_msg, "success": False, "operation": operation}
