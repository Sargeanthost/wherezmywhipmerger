import httpx
import os
from routeplanner import RoutePlan, Stop, Location, Request
import urllib.parse


ids = []


class Mapbox:
    BASE_URL: str = os.environ.get("MAPBOX_URL")  # type: ignore
    API_KEY: str = os.environ.get("MAPBOX_KEY")  # type: ignore

    def __init__(self):
        self.optimizer_client = httpx.Client(
            base_url=Mapbox.BASE_URL,
            params={
                "access_token": Mapbox.API_KEY,
                "roundtrip": False,
                "source": "first",
                "destination": "last",
            },
        )
        self.matrix_client = httpx.Client(
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

    def _parseSolutionJson(self, json: dict) -> list[tuple[tuple[dict, dict], dict]]:
        """Parses a MapBox solution into a Route Plan

        Args:
            json (dict): a mapbox solution json
        """

        ordered_waypoints = sorted(
            json.get("waypoints"), key=lambda x: x.get("waypoint_index")
        )  # type: ignore

        batches = [
            (ordered_waypoints[i], ordered_waypoints[i + 1])
            for i in range(len(ordered_waypoints) - 1)
        ]
        # print("batches", batches)

        legs: list = json.get("trips")[0].get("legs")

        waypoints_and_their_legs = []
        for idx, leg in enumerate(legs):
            # skip last leg as its the return to first location if roundtrip is true
            if idx == len(legs):
                break
            waypoints_and_their_legs.append((batches[idx], leg))
        # print(json)
        # print(waypoints_and_their_legs)
        return waypoints_and_their_legs
        # return RoutePlan([], [])

    def requestOptimizedTrip(
        self, locations: list[Request]
    ) -> list[tuple[tuple[dict, dict], dict]]:
        """Takes in a list of Requests and returns an optimized trip that goes through all points.

        Args:
            locations (list[Request]): _description_

        Returns:
            _type_: _description_
        """

        _locations, _distributions = self._createRequestPath(locations)

        resp = self.optimizer_client.get(
            rf"optimized-trips/v1/mapbox/driving/{_locations}",
            params={"distributions": f"{_distributions}"},
        )
        # print(f"request:", {resp.request.url})

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
        raise Exception("Failed to get optimized trip")

    def _getLonLatFromLocations(self, locations: list[Request]) -> str:
        coordinate_list_url: str = ""

        for request in locations:
            combined_locs = f"{request.start_loc.lon},{request.start_loc.lat};{request.end_loc.lon},{request.end_loc.lat}"
            if len(coordinate_list_url) > 0:
                coordinate_list_url += ";"
            coordinate_list_url += f"{combined_locs}"

        return coordinate_list_url

    def _parseMatrixJson(self, json: dict):
        print(json.get("durations"))
        return json

    def getMatrix(self, locations: list[Request]):
        _locations: str = self._getLonLatFromLocations(locations)
        resp = self.matrix_client.get(
            rf"directions-matrix/v1/mapbox/driving/{_locations}",
        )

        match resp.status_code:
            case 200:
                match resp.json()["code"]:
                    case "Ok":
                        return self._parseMatrixJson(resp.json())
                    case "NoRoute":
                        raise Exception("Failed to get optimized trip")
            case 422:
                raise Exception(f"Invalid request: {resp.json()['message']}")
            case _:
                resp.raise_for_status()
        raise Exception("Failed to get optimized trip")


if __name__ == "__main__":
    thing = Mapbox()

    thing.getMatrix(
        [
            Request(
                Location(42.248791, -71.814532), Location(42.272554, -71.801570), 5
            ),
            Request(
                Location(42.267956, -71.800240),
                Location(42.272554, -71.801570),
                5,
            ),
        ]
    )
    # print(
    #     thing.requestOptimizedTrip(
    #         [
    #             Request(
    #                 Location(42.248791, -71.814532), Location(42.272554, -71.801570), 5
    #             ),
    #             # Request(
    #             #     Location(42.267956, -71.800240),
    #             #     Location(42.272554, -71.801570),
    #             #     # Location(42.263959, -71.807391),
    #             #     5,
    #             # ),
    #         ]
    #     )
    # )
