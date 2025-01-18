import os
from typing import Self

from supabase import create_client, Client, PostgrestAPIError, PostgrestAPIResponse
from dataclasses import dataclass
from routeplanner import RoutePlan, Stop, Location, Request
from mapboxclient import Mapbox
import numpy as np

supabase_url: str = os.environ.get("SUPABASE_URL")  # type: ignore
supabase_key: str = os.environ.get("SUPABASE_KEY")  # type: ignore
# supabase: Client = create_client(supabase_url, supabase_key)


def calculateDetourTime(
    startLoc: Location, detourLocation: Location, endLoc: Location
) -> float:
    return (
        startLoc.travelTimeTo(detourLocation) + detourLocation.travelTimeTo(endLoc)
    ) - startLoc.travelTimeTo(endLoc)


def forcedPath(requests: list[Request]):  # -> RoutePlan:
    plan: RoutePlan = RoutePlan(requests, [])
    stops: list[Stop] = []
    for i, request in enumerate(requests):
        stops.append(
            Stop(
                requests[i].start_loc,
                True,
                requests[i].end_time
                - (requests[i].start_loc.travelTimeTo(requests[i].end_loc)),
                1,
            )
        )
        stops.append(Stop(requests[i].end_loc, False, requests[i].end_time, 1))
        pass
    plan.route = stops
    return plan


def checkGroupIndexes(
    requests: list[Request], groups: list[list[int]]
):  # -> list[RoutePlan] | False:
    # groups = [ [1,2,5], [3] ]

    planner: Mapbox = Mapbox()
    npRequests = np.array(requests)

    # requestGroupsIndexes = [[]]  # Routes [6,7,8,9,3]  INDEXES #[1,3,4]
    validGrouping = True
    plans = []
    # Check if Each route is valid
    for i, groupIndexes in enumerate(groups):  # Size is numRoutes
        chosenRequests: list[Request] = list(
            npRequests[np.array(groupIndexes)]
        )  # Values [7,9,3]

        plan: RoutePlan = forcedPath(chosenRequests)
        print(plan)
        # planner.requestOptimizedTrip(chosenRequests)

        # print(f"ROUTE num {i}")
        # for stop in plan.route:
        #     print(stop)

        plans.append(plan)
        if not plan.isValid():
            # print("INVALID")
            validGrouping = False
            break
        else:
            pass
            # print("Valid")
    if validGrouping:
        return plans

    return False


def subdivideGroups(requests, groups):
    successGroup = checkGroupIndexes(requests, groups)

    if successGroup:
        return successGroup
    else:
        middle = (len(groups) + 1) // 2
        first_part = groups[:middle]
        second_part = groups[middle:]

        firstSuccess = subdivideGroups(requests, first_part)
        secondSuccess = subdivideGroups(requests, second_part)

        print(
            f"Group {groups}, {successGroup}, {first_part} {firstSuccess}, {second_part} {secondSuccess}"
        )


# MAIN FUNCTION
def calculateMinimumRoutes(requests: list[Request]) -> list[RoutePlan]:
    # Takes in a list of peoples reservations, (all who have the same car type)
    # Returns the RoutePlans with the minimum Number of routes(drivers) needed to cover everyones plan within the constraints

    # naiveGroups = [[i] for i in range(len(requests))]
    allOneGroup = [[i for i in range(len(requests))]]
    successGroup = subdivideGroups(
        requests, allOneGroup
    )  # checkGroupIndexes(requests, allOneGroup)

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
        pass
        # routes: PostgrestAPIResponse = supabase.table("routes").select("*").execute()
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
    # main()

    AS: Location = Location(1, 2)
    AD: Location = Location(2, 3)
    AReq: Request = Request(AS, AD, 10)

    BS: Location = Location(5.5, 2)
    BD: Location = Location(6, 3)
    BReq: Request = Request(BS, BD, 9)

    CS: Location = Location(6, 4.5)
    CD: Location = Location(5.25, 4)
    CReq: Request = Request(CS, CD, 8)

    DS: Location = Location(2, 6.25)
    DD: Location = Location(3.25, 5.5)
    DReq: Request = Request(DS, DD, 7)

    ES: Location = Location(1, 3)
    ED: Location = Location(2.5, 4)
    EReq: Request = Request(ES, ED, 6)

    # Request()
    requests = [AReq, BReq, CReq, DReq, EReq]
    sol = calculateMinimumRoutes(requests)
    print(sol)
    # print(AReq)
    print("Done")
