import httpx
from main import Location, Request
import os
from dataclasses import dataclass
from main import RoutePlan, Stop
from random import randint


@dataclass
class MapboxLocation:
    name: str
    coordinates: list[int]  # long, lat

ids = []


class Mapbox:
    BASE_URL: str = os.environ.get("MAPBOX_URL")  # type: ignore
    API_KEY: str = os.environ.get("MAPBOX_KEY")  # type: ignore

    def __init__(self):
        self.client = httpx.Client(
            base_url=Mapbox.BASE_URL, params={"access_token": Mapbox.API_KEY}
        )

    def _getOptimizedTrip(self, id: str):
        while True:  # TODO this needs to be backed off
            resp = self.client.get(f"/optimized-trips/v2/{id}")
            resp.raise_for_status()
            if resp.json().get("status") == "complete":
                return self._parseSolutionJson(resp.json())
        pass

    def _createRequestDocument(self, locations: list[Request]) -> dict:
        """Creates a document to send to the MapBox API for optimization. Creates shipments and will set start_locs in a request to a pickup requirement.

        Args:
            locations (list[Request]): _description_

        Returns:
            dict: _description_
        """
        global ids
        request_document = {
            "version": 1,
            "locations": [],
            "vehicles": [],
            "shipments": [],
        }

        _locations = []
        for request in locations:
           while id := randint(1,)
            randint()
            loc1 = MapboxLocation("")
            _locations.append([request.start_loc.lon, request.start_loc.lat])
            _locations.append([request.end_loc.lon, request.end_loc.lat])

    def _parseSolutionJson(self, json: dict) -> RoutePlan:
        """Parses a MapBox solution into a Route Plan

        Args:
            json (dict): a mapbox solution json
        """
        return RoutePlan([], [])

    def requestOptimizedTrip(self, locations: list[Request]) -> RoutePlan:
        """Takes in a list of Requests and returns an optimized trip that goes through all points.

        Args:
            locations (list[Request]): _description_

        Returns:
            _type_: _description_
        """

        content = self._createRequestDocument(locations)
        resp = self.client.post(
            "optimized-trips/v1/mapbox/driving",
            content=content,
        )
        resp.raise_for_status()
        match resp.status_code:
            case 202:
                return self._getOptimizedTrip(resp.json().get("id"))
            case 200:
                return self._parseSolutionJson(resp.json())  # this is optimized trip
            case _:
                raise Exception("Failed to get optimized trip")

    def getIsochrone(self, location: Location):
        # isochrone / v1 / mapbox / driving
        pass

    def getRoute(self, start_loc: Location, end_loc: Location):
        pass
