import os
from typing import Self
from supabase import create_client, Client, PostgrestAPIError, PostgrestAPIResponse
from dataclasses import dataclass
from mapbox import Mapbox
from numpy import np

supabase_url: str = os.environ.get("SUPABASE_URL")  # type: ignore
supabase_key: str = os.environ.get("SUPABASE_KEY")  # type: ignore
supabase: Client = create_client(supabase_url, supabase_key)


@dataclass
class Location:
    lon: int
    lat: int

    def travelTimeTo(self, destination: Self) -> float:
        # Pull from Matrix
        return 0.0


@dataclass
class Request:
    start_loc: Location
    end_loc: Location
    end_time: float


@dataclass
class Stop:
    location: Location
    isPickup: bool
    arrivalTime: float
    peopleTransferred: int


@dataclass
class RoutePlan:
    requests: list[Request]
    route: list[Stop]

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

            # For each Request, start_loc and end_loc are in route
            if startIndex == -1 or endIndex == -1:
                return False

            # For each Request, start_loc (as a Stop) is in route before end_loc
            if startIndex > endIndex:
                return False

            arrivalTime = self.route[endIndex].arrivalTime
            requestedArrivalTime = self.requests[i].end_time
            earlyDropOffThreshold: float = 5 * 60.0

            # For each Request, Stop arrival_time of end_loc is before request end_time and not more than (5) minutes before
            if arrivalTime > requestedArrivalTime or arrivalTime < (
                requestedArrivalTime - earlyDropOffThreshold
            ):
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


def calculateDetourTime(
    startLoc: Location, detourLocation: Location, endLoc: Location
) -> float:
    return (
        startLoc.travelTimeTo(detourLocation) + detourLocation.travelTimeTo(endLoc)
    ) - startLoc.travelTimeTo(endLoc)


def checkGroupIndexes(
    requests: list[Request], groups: list[list[int]]
):  # -> list[RoutePlan] | False:
    # groups = [ [1,2,5], [3] ]

    planner: Mapbox = Mapbox()

    # requestGroupsIndexes = [[]]  # Routes [6,7,8,9,3]  INDEXES #[1,3,4]
    validGrouping = True
    plans = []
    # Check if Each route is valid
    for groupIndexes in groups:  # Size is numRoutes
        chosenRequests = requests[np.array(groupIndexes)]  # Values [7,9,3]
        plan: RoutePlan = planner.requestOptimizedTrip(chosenRequests)
        plans.append(plan)
        if not plan.isValid():
            validGrouping = False
            break
    if validGrouping:
        return plans

    return False


# MAIN FUNCTION
def calculateMinimumRoutes(requests: list[Request]) -> list[RoutePlan]:
    # Takes in a list of peoples reservations, (all who have the same car type)
    # Returns the RoutePlans with the minimum Number of routes(drivers) needed to cover everyones plan within the constraints

    requests = np.array(requests)

    naiveGroups = [[i] for i in range(len(requests))]
    successGroup = checkGroupIndexes(requests, naiveGroups)

    if successGroup:
        return successGroup

    """
    # For Each Number of Routes 1, Route, 2 Routes...
    # Take The first valid Generates as the best because it has the least routes
    for numRoutes in range(1, len(requests)):
        # Choose Some Permutation for each route
        # All Number of people in each Group.
        permutations = []
        for permutation in permutations:
            
            # Else Contiune
    """

    # IF make it here Use Naive Case of One ROutePlan Per Request
    return []


def main():
    # At Midnight Each day or on request
    runDailyRouteMerge()


def runDailyRouteMerge():
    # Fetch Data
    try:
        routes: PostgrestAPIResponse = supabase.table("routes").select("*").execute()
    except PostgrestAPIError as e:
        print(e)
        return

    # Store to Array of Requests
    plans = calculateMinimumRoutes([])
    # Store to Table with (Location, RouteID, and indexInRoute)
    storeRoutesInDatabase(plans)


def storeRoutesInDatabase(plans: list[RoutePlan]):
    for i, routePlan in enumerate(plans):
        for j, stop in enumerate(routePlan.route):
            # Push to Database
            # (Location = stop.location, RouteID = i, indexInRoute = j)
            pass


if __name__ == "__main__":
    main()

    AS: Location = Location(1,2)
    AD: Location = Location(2,3) 
    
    AS: Location = Location(1,2)
    AD: Location = Location(2,3) 

    AS: Location = Location(1,2)
    AD: Location = Location(2,3) 

    AS: Location = Location(1,2)
    AD: Location = Location(2,3)

    AS: Location = Location(1,2)
    AD: Location = Location(2,3)

    AS: Location = Location(1,2)
    AD: Location = Location(2,3) 


    Request()
