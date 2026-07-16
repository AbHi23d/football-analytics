"""Data collection module for football analytics."""

from .api_client import FootballDataAPIClient
from .database import DatabaseManager
from .data_fetcher import DataFetcher

__all__ = ["FootballDataAPIClient", "DatabaseManager", "DataFetcher"]
