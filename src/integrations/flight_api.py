"""
Flight API Integration: AviationStack

Real-time flight data from external API.
Graceful fallback to database if API unavailable.
"""

import requests
from typing import Dict, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class FlightAPIClient:
    """
    Flight API client with fallback to local database.

    Uses AviationStack API (free tier: 100 requests/month)
    https://aviationstack.com/
    """

    def __init__(self, api_key: Optional[str] = None, database=None):
        self.api_key = api_key or os.getenv("AVIATIONSTACK_API_KEY")
        self.database = database
        self.base_url = "http://api.aviationstack.com/v1"

        if self.api_key:
            logger.info("FlightAPI initialized with API key")
        else:
            logger.warning("No API key - will use database fallback only")

    def get_flight_status(self, flight_number: str) -> Dict:
        """
        Get real-time flight status.

        Args:
            flight_number: Flight number (e.g., "NZ1")

        Returns:
            Flight status dictionary
        """

        # Try API first if key available
        if self.api_key:
            try:
                return self._fetch_from_api(flight_number)
            except Exception as e:
                logger.warning(f"API fetch failed: {str(e)}. Falling back to database.")

        # Fallback to database
        if self.database:
            return self._fetch_from_database(flight_number)

        raise Exception("No data source available for flight status")

    def _fetch_from_api(self, flight_number: str) -> Dict:
        """Fetch from AviationStack API"""

        # Map NZ flights to IATA code
        iata_code = flight_number  # e.g., "NZ1"

        params = {
            "access_key": self.api_key,
            "flight_iata": iata_code
        }

        response = requests.get(
            f"{self.base_url}/flights",
            params=params,
            timeout=5
        )

        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}")

        data = response.json()

        if not data.get("data"):
            raise Exception(f"No flight data found for {flight_number}")

        flight = data["data"][0]  # First result

        # Transform to our format
        return {
            "source": "aviationstack_api",
            "flight_number": flight_number,
            "airline": flight.get("airline", {}).get("name", "Air New Zealand"),
            "flight_status": flight.get("flight_status", "unknown"),
            "departure": {
                "airport": flight.get("departure", {}).get("airport", ""),
                "iata": flight.get("departure", {}).get("iata", ""),
                "scheduled": flight.get("departure", {}).get("scheduled", ""),
                "actual": flight.get("departure", {}).get("actual", ""),
                "delay": flight.get("departure", {}).get("delay", 0),
            },
            "arrival": {
                "airport": flight.get("arrival", {}).get("airport", ""),
                "iata": flight.get("arrival", {}).get("iata", ""),
                "scheduled": flight.get("arrival", {}).get("scheduled", ""),
                "estimated": flight.get("arrival", {}).get("estimated", ""),
            },
            "aircraft": {
                "registration": flight.get("aircraft", {}).get("registration", ""),
                "iata": flight.get("aircraft", {}).get("iata", ""),
            },
            "fetched_at": datetime.now().isoformat()
        }

    def _fetch_from_database(self, flight_number: str) -> Dict:
        """Fallback to local database"""

        flight = self.database.get_flight_status(flight_number)

        if not flight:
            raise Exception(f"Flight not found in database: {flight_number}")

        return {
            "source": "local_database",
            "flight_number": flight['flight_number'],
            "airline": "Air New Zealand",
            "flight_status": flight['status'],
            "departure": {
                "airport": flight['origin'],
                "scheduled": flight['scheduled_departure'],
                "actual": flight.get('actual_departure'),
                "delay": flight.get('delay_minutes', 0),
            },
            "arrival": {
                "airport": flight['destination'],
                "scheduled": flight['scheduled_arrival'],
                "actual": flight.get('actual_arrival'),
            },
            "aircraft": {
                "registration": flight.get('aircraft_registration', ''),
            },
            "gate": flight.get('gate'),
            "pax_count": flight.get('pax_count'),
            "fetched_at": datetime.now().isoformat()
        }

    def search_flights(self, params: Dict) -> list:
        """
        Search flights by various criteria.

        Args:
            params: Search parameters (date, origin, destination, etc.)

        Returns:
            List of matching flights
        """

        # For demo, only support database search
        if not self.database:
            return []

        # Simulate search - in production would have proper search logic
        logger.info(f"Searching flights with params: {params}")

        return []  # Placeholder


class MockFlightAPI:
    """Mock flight API for testing without real API key"""

    def __init__(self, database=None):
        self.database = database

    def get_flight_status(self, flight_number: str) -> Dict:
        """Return mock flight status"""

        if self.database:
            try:
                return self._fetch_from_database(flight_number)
            except:
                pass

        # Hardcoded mock data
        return {
            "source": "mock_api",
            "flight_number": flight_number,
            "airline": "Air New Zealand",
            "flight_status": "scheduled",
            "departure": {
                "airport": "Auckland International Airport",
                "iata": "AKL",
                "scheduled": "2024-12-02T14:00:00",
                "delay": 0,
            },
            "arrival": {
                "airport": "Sydney International Airport",
                "iata": "SYD",
                "scheduled": "2024-12-02T17:00:00",
            },
            "aircraft": {
                "registration": "ZK-OKM",
            },
            "fetched_at": datetime.now().isoformat()
        }

    def _fetch_from_database(self, flight_number: str) -> Dict:
        """Same as FlightAPIClient"""
        flight = self.database.get_flight_status(flight_number)

        if not flight:
            raise Exception(f"Flight not found: {flight_number}")

        return {
            "source": "local_database_via_mock",
            "flight_number": flight['flight_number'],
            "airline": "Air New Zealand",
            "flight_status": flight['status'],
            "departure": {
                "airport": flight['origin'],
                "scheduled": flight['scheduled_departure'],
                "delay": flight.get('delay_minutes', 0),
            },
            "arrival": {
                "airport": flight['destination'],
                "scheduled": flight['scheduled_arrival'],
            },
            "aircraft": {
                "registration": flight.get('aircraft_registration', ''),
            },
            "gate": flight.get('gate'),
            "pax_count": flight.get('pax_count'),
            "fetched_at": datetime.now().isoformat()
        }
