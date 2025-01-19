import os
from typing import Self

from dataclasses import dataclass
from math import sqrt

supabase_url: str = os.environ.get("SUPABASE_URL")  # type: ignore
supabase_key: str = os.environ.get("SUPABASE_KEY")  # type: ignore
# supabase: Client = create_client(supabase_url, supabase_key)


@dataclass
class Location:
    lat: float
    lon: float

    def travelTimeTo(self, destination: Self) -> float:
        # Pull from Matrix
        return (
            sqrt((self.lon - destination.lon) ** 2 + (self.lat - destination.lat) ** 2)
            * 100
        )
        # return 0.0

    def __repr__(self) -> str:
        # string = f"x: {self.lon}, y: {self.lat}"
        string = f"({self.lat}, {self.lon})"
        return string


@dataclass
class Request:
    start_loc: Location
    end_loc: Location
    end_time: float

    def __repr__(self) -> str:
        string = f"Start: {self.start_loc}, End: {self.end_loc}, ArrivalTime: {self.end_time}"
        return string


@dataclass
class Stop:
    location: Location
    isPickup: bool
    arrivalTime: float
    peopleTransferred: int

    def __repr__(self) -> str:
        string = f"{'Pickup' if self.isPickup else 'Drop'} at: \t{self.location},Time {self.arrivalTime}"
        return string


@dataclass
class RoutePlan:
    requests: list[Request]
    route: list[Stop]

    def __repr__(self) -> str:
        string = "Route\n"
        for i, stop in enumerate(self.route):
            string += "\tStop: " + str(i + 1) + ":" + str(stop) + "\n"
        string += "\n"
        string += str(self.requests)
        return string

    def isValid(self) -> bool:
        # To add a start_loc as a intermediate point, the driver
        # Todo !!! Consider Routes that jump back and forth between common places.

        for i, request in enumerate(self.requests):
            startIndex = -1
            endIndex = -1

            for j, stop in enumerate(self.route):
                if stop.location == request.start_loc:
                    startIndex = j
                elif stop.location == request.end_loc:
                    endIndex = j

                if j > 0 and self.route[j - 1].arrivalTime > self.route[j].arrivalTime:
                    return False

            # For each Request, start_loc and end_loc are in route
            if startIndex == -1 or endIndex == -1:
                return False

            # For each Request, start_loc (as a Stop) is in route before end_loc
            if startIndex > endIndex:
                return False

            arrivalTime = self.route[endIndex].arrivalTime
            requestedArrivalTime = self.requests[i].end_time
            earlyDropOffThreshold: float = 5 * 60.0

            # print(arrivalTime, requestedArrivalTime, earlyDropOffThreshold)
            # For each Request, Stop arrival_time of end_loc is before request end_time and not more than (5) minutes before
            if arrivalTime > requestedArrivalTime or arrivalTime < (
                requestedArrivalTime - earlyDropOffThreshold
            ):
                # print("INVALID TIME")
                return False

            # For each Request, Stop arrival_time of start_loc is not before (30) + start_loc.travelTimeTo(end_loc)
            directTravelTime = self.requests[i].start_loc.travelTimeTo(
                self.requests[i].end_loc
            )
            trueTravelTime = (
                self.route[endIndex].arrivalTime - self.route[startIndex].arrivalTime
            )
            travelExtraTolerance: float = 30 * 60.0
            if trueTravelTime > travelExtraTolerance + directTravelTime:
                return False

        return True
