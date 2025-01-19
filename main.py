import os
from typing import Self

from dataclasses import dataclass
from routeplanner import RoutePlan, Stop, Location, Request
from mapboxclient import Mapbox
import numpy as np
from supabaseclient import (
    getTodayRequests,
    pushRoutesToTable,
    giveRequestIDRouteID,
    setPickupTime,
)


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
                - 1
                - (requests[i].start_loc.travelTimeTo(requests[i].end_loc)),
                1,
            )
        )
        # if not len(stops) == 1:
        stops.append(Stop(requests[i].end_loc, False, requests[i].end_time - 1, 1))
        pass
    plan.route = stops
    return plan


def tripJsonToStops(chosenRequests):
    planner: Mapbox = Mapbox()
    # If one, Never Give Fail Times

    # print(chosenRequests)
    print("\nRoutes")
    for route in chosenRequests:
        print(route)
    out: tuple[dict, list[tuple[tuple[dict, dict], dict]]]
    route_json: dict

    route_json, out = planner.requestOptimizedTrip(chosenRequests)  # type: ignore

    # Point1, Point2, Leg
    # Point: Distance, Name, Location: list[float, float], Waypoint Index, Trips Index
    # Leg: Steps, Summary, weight, duration: float, distance

    # print("OUT")
    # print(out, len(out))

    fullRouteTime = 0
    for i in range(len(out)):
        duration = out[i][1]["duration"]
        fullRouteTime += duration

    lastUserTime = 0
    for i in range(len(chosenRequests)):
        lastUserTime = max(lastUserTime, chosenRequests[i].end_time)

    # lastUserTime = out[len(out) - 1][0][1]["location"]
    # print(lastUserTime, fullRouteTime)

    currentTime = (
        lastUserTime - fullRouteTime - 60
    )  # Last Person Will be 1 Minute Early
    stops: list[Stop] = []

    for i in range(len(out)):
        point = out[i][0][0]["location"]  # list[float, float]
        # print(point)
        loc = Location(point[1], point[0])
        drop = loc.isLocationDrop(chosenRequests)

        stops.append(Stop(loc, not drop, currentTime, 1))
        # if i != len(out) - 1:
        duration = out[i][1]["duration"]
        # print(duration)
        currentTime += duration
        if i == (len(out) - 1):
            endpoint = out[i][0][1]["location"]  # list[float, float]
            # print(endpoint)
            ep = Location(endpoint[1], endpoint[0])
            drop = ep.isLocationDrop(chosenRequests)
            stops.append(Stop(ep, not drop, currentTime, 1))

    print(len(out))
    print(stops)

    return RoutePlan(chosenRequests, stops), route_json


def checkGroupIndexes(
    requests: list[Request], groups: list[list[int]]
):  # -> list[RoutePlan] | False:
    # groups = [ [1,2,5], [3] ]

    planner: Mapbox = Mapbox()
    npRequests = np.array(requests)

    # requestGroupsIndexes = [[]]  # Routes [6,7,8,9,3]  INDEXES #[1,3,4]
    validGrouping = True
    plans = []
    routesJsons = []
    # Check if Each route is valid
    for i, groupIndexes in enumerate(groups):  # Size is numRoutes
        chosenRequests: list[Request] = list(
            npRequests[np.array(groupIndexes)]
        )  # Values [7,9,3]

        # plan: RoutePlan = forcedPath(chosenRequests)

        # print("ST", len(plan.route), plan.route)
        plan, route_json = tripJsonToStops(chosenRequests)
        # plan: RoutePlan

        # print("\n")
        # print(plan)
        # planner.requestOptimizedTrip(chosenRequests)

        # print(f"ROUTE num {i}")
        # for stop in plan.route:
        #     print(stop)

        plans.append(plan)
        routesJsons.append(route_json)

        if not plan.isValid():
            # print("INVALID")
            validGrouping = False
            break
        else:
            pass
            # print("Valid")
    if validGrouping:
        return plans, routesJsons

    return False, False


def subdivideGroups(requests, groups):
    # print(groups)
    successGroup, routesJson = checkGroupIndexes(requests, groups)
    # print(f"SUB SUC {successGroup}")

    if successGroup:
        return groups
    else:
        middle = (len(groups[0]) + 1) // 2
        # print(middle)
        first_part = [groups[0][:middle]]
        second_part = [groups[0][middle:]]
        # print(first_part, second_part)

        firstSuccess = subdivideGroups(requests, first_part)
        secondSuccess = subdivideGroups(requests, second_part)

        # print(
        #     f"Group {groups}, {successGroup != False}, {first_part} {firstSuccess != False}, {second_part} {secondSuccess != False}"
        # )

        # print(f"F {firstSuccess}, S {secondSuccess}")
        ret = []
        for group in firstSuccess:
            ret.append(group)
        for group in secondSuccess:
            ret.append(group)
        # print(f"RET: {ret}")
        return ret


# MAIN FUNCTION
def calculateMinimumRoutes(requests: list[Request]) -> list[RoutePlan]:
    # Takes in a list of peoples reservations, (all who have the same car type)
    # Returns the RoutePlans with the minimum Number of routes(drivers) needed to cover everyones plan within the constraints

    # naiveGroups = [[i] for i in range(len(requests))]
    allOneGroup = [[i for i in range(len(requests))]]
    print(allOneGroup)
    successGroup = subdivideGroups(
        requests, allOneGroup
    )  # checkGroupIndexes(requests, allOneGroup)

    print(successGroup)
    ret, routesJson = checkGroupIndexes(requests, successGroup)
    # print(ret)

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
    return ret, routesJson  # type: ignore


def main():
    # At Midnight Each day or on request
    runDailyRouteMerge()


def runDailyRouteMerge():
    # Fetch Data

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
    AReq: Request = Request(AS, AD, 10, 1)

    BS: Location = Location(5.5, 2)
    BD: Location = Location(6, 3)
    BReq: Request = Request(BS, BD, 10, 1)

    CS: Location = Location(6.75, 5)
    CD: Location = Location(5.25, 4)
    CReq: Request = Request(CS, CD, 8, 1)

    DS: Location = Location(2, 6.25)
    DD: Location = Location(3.25, 5.5)
    DReq: Request = Request(DS, DD, 3, 1)

    ES: Location = Location(1, 3)
    ED: Location = Location(2.5, 4)
    EReq: Request = Request(ES, ED, 11, 1)

    # Request()
    requests = [AReq, BReq, CReq, DReq, EReq]

    todayRequests = getTodayRequests()
    print(todayRequests, len(todayRequests))

    sol, routesJson = calculateMinimumRoutes(
        todayRequests
    )  # List[RoutePlan], List[Json]
    # sol = calculateMinimumRoutes(requests)
    print(sol)
    # print(AReq)

    # Push To DB}
    routeIDs = pushRoutesToTable(sol, routesJson)
    print("RouteIDs", routeIDs)
    for i, routePlan in enumerate(sol):
        for j, request in enumerate(routePlan.requests):
            giveRequestIDRouteID(request.user_id, routeIDs[i])
            setPickupTime(request.user_id, routePlan.requestPickupTime(requestIndex=j))

    carlosRequests = [
        Request(
            Location(42.257255, -71.820379), Location(42.259998, -71.820529), 200, 1
        ),
        Request(
            Location(42.255953, -71.818582), Location(42.263959, -71.807391), 500, 2
        ),
    ]

    # Route 0,300,600,900
    # Schedule = 400, 950
    # Before and 300 Sec Earlier

    # tripJsonToStops(carlosRequests)

    # sol = calculateMinimumRoutes(carlosRequests)
    # print(sol)
    print("Done")
