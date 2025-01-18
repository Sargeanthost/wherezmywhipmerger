import httpx
import os
from dataclasses import dataclass
from random import randint
from routeplanner import RoutePlan, Stop, Location, Request


ids = []


class Mapbox:
    BASE_URL: str = os.environ.get("MAPBOX_URL")  # type: ignore
    API_KEY: str = os.environ.get("MAPBOX_KEY")  # type: ignore

    def __init__(self):
        self.client = httpx.Client(
            base_url=Mapbox.BASE_URL, params={"access_token": Mapbox.API_KEY}
        )

    def _createRequestPath(self, locations: list[Request]) -> tuple[str, str]:
        """Creates a URL path to append to the mapbox optimizer url to send to the MapBox API for optimization.

        Args:
            locations (list[Request]): list of requests

        Returns:
            dict: _description_
        """
        # distributions : pickup,dropoff. which is in reference to the coordinate list
        coordinate_list_url: str = ""
        distribution_list_url: str = ""  # 0 indexed. need to add as a param
        coordinate_pairs_in_url: int = 0

        for request in locations:
            combined_locs = f"{request.start_loc.lon},{request.start_loc.lat};{request.end_loc.lon},{request.end_loc.lat}"

            if len(coordinate_list_url) > 0:
                coordinate_list_url += ";"
            coordinate_list_url += f"{combined_locs}"
            coordinate_pairs_in_url += 2

            if len(distribution_list_url) > 0:
                distribution_list_url += ";"
            distribution_list_url += (
                f"{coordinate_pairs_in_url - 2},{coordinate_pairs_in_url - 1}"
            )

        return coordinate_list_url, distribution_list_url

    def _parseSolutionJson(self, json: dict) -> RoutePlan:
        """Parses a MapBox solution into a Route Plan

        Args:
            json (dict): a mapbox solution json
        """
        print(json)
        return RoutePlan([], [])

    def requestOptimizedTrip(self, locations: list[Request]):
        """Takes in a list of Requests and returns an optimized trip that goes through all points.

        Args:
            locations (list[Request]): _description_

        Returns:
            _type_: _description_
        """

        _locations, _distributions = self._createRequestPath(locations)
        resp = self.client.get(
            f"optimized-trips/v1/mapbox/driving/{_locations}?distributions={_distributions}",
        )

        match resp.status_code:
            case 200:
                match resp.json()["code"]:
                    case "Ok":
                        return self._parseSolutionJson(resp.json())
                    case "NoRoute":
                        raise Exception("Failed to get optimized trip")
                    case "NoTrips":
                        raise Exception("Failed to get optimized trip")
                    case "NotImplemented":
                        raise Exception("Failed to get optimized trip")
                    case "NoSegment":
                        raise Exception("Failed to get optimized trip")
            case 422:
                raise Exception(f"Invalid request: {resp.json()['message']}")
            case _:
                resp.raise_for_status()


if __name__ == "__main__":
    thing = Mapbox()

    thing.requestOptimizedTrip(
        [
            Request(
                Location(42.257255, -71.820379), Location(42.259998, -71.820529), 5
            ),
            Request(
                Location(42.255953, -71.818582),
                Location(42.263959, -71.807391),
                5,
            ),
        ]
    )
