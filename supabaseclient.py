# take in routplans to push to db
import os
from supabase import create_client, Client, PostgrestAPIError, PostgrestAPIResponse
from routeplanner import Location, Request, RoutePlan
from dataclasses import dataclass
from shapely.wkb import loads
import binascii
from datetime import datetime, timezone, timedelta
from dateutil import parser


supabase_url: str = os.environ.get("SUPABASE_URL")  # type: ignore
supabase_key: str = os.environ.get("SUPABASE_KEY")  # type: ignore
supabase_client: Client = create_client(supabase_url, supabase_key)


resp: PostgrestAPIResponse = supabase_client.table("request").select("*").execute()

# print(type(resp))


@dataclass
class TableRequests:
    id: int
    pickup: Location
    destination: Location
    arrival: int  # Epoc Sec
    vehicle: str
    ride_share: bool
    people_transfered: int
    requesterID: str
    pickup_name: str
    destination_name: str
    pickup_time: int  # Epoc Sec

    def __repr__(self) -> str:
        string = (
            str(self.pickup)
            + " to "
            + str(self.destination)
            + " at "
            + str(self.arrival)
        )
        return string


resp = resp.data
# print(resp.data)

table: list[TableRequests] = []


def geoToLocation(geo: str) -> Location:
    # WKB in hexadecimal
    # wkb_hex = "0101000020E61000008E5C37A5BC56C0BF62A1D634EFC04940"

    # Convert the hex string to binary and load it
    point = loads(binascii.unhexlify(geo))

    return Location(point.y, point.x)


def timeStampStringToSec(timestamp: str) -> int:
    # Input timestamp
    # timestamp = "2025-01-18T22:29:49.763+00:00"

    # Parse the ISO 8601 timestamp
    dt = parser.isoparse(timestamp)

    # Convert to epoch seconds
    epoch_seconds = int(dt.timestamp())

    # print(epoch_seconds)  # Output: 173724178
    return epoch_seconds


def get_current_day_of_year():
    # Get current date and time
    now = datetime.now()
    # Return the day of the year
    return now.timetuple().tm_yday - 1


def get_day_of_year_from_epoch(epoch_seconds):
    # Convert epoch seconds to a timezone-aware datetime object in UTC
    eastern = timezone(timedelta(hours=-5))

    # dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    dt = datetime.fromtimestamp(epoch_seconds, tz=eastern)

    # Return the day of the year
    # print("Current Hour:", dt.hour)
    return dt.timetuple().tm_yday


def pushRoutesToTable(plans: list[RoutePlan], routesJson):
    routeIDs = []
    for i in range(len(plans)):
        startLocation = plans[i].firstLocation()
        print("PUSH TO TABLE")

        pointStr = f"POINT({startLocation.lon} {startLocation.lat})"
        print(pointStr)

        outDict = (
            supabase_client.table("route")
            .insert(
                {
                    "route": routesJson[i],
                    "start_loc": pointStr,
                }
            )
            .execute()
        ).data

        routeID = outDict[0]["id"]
        routeIDs.append(routeID)
        # print(f"ID: {routeID}")
    return routeIDs


def giveRequestIDRouteID(requestID, routeID):
    print(f"Request ID: {requestID}, Route ID: {routeID}")
    outDict = (
        supabase_client.table("request")
        .update({"route_id": routeID})
        .eq("id", requestID)  # Use .eq() for equality in Supabase
        .execute()  # Execute the query
    )


def getTodayRequests() -> list[Request]:
    # supabase_client.table("route").insert({"thing":"POINT({},{})" })
    for i, row in enumerate(resp):
        # print(row, row["id"])
        # print("\n\n")
        tableRow: TableRequests = TableRequests(
            row["id"],
            geoToLocation(row["pickup"]),
            geoToLocation(row["destination"]),
            timeStampStringToSec(row["arrival"]),
            row["vehicle_type"],
            row["ride_share"],
            row["people_transferred"],
            row["requester"],
            row["pickup_name"],
            row["destination_name"],
            row["pickup_time"],
        )

        # )
        table.append(tableRow)

    today = get_current_day_of_year()
    todaysRequests: list[Request] = []
    for i in table:
        if get_day_of_year_from_epoch(i.arrival) == today:
            todaysRequests.append(
                Request(i.pickup, i.destination, i.arrival - 1737239389, i.id)
            )
    return todaysRequests


# print(getTodayRequests())


# print(len(resp.data))

if __name__ == "__main__":
    print(geoToLocation("0101000000e4326e6aa0f351c0a5bdc11726234540"))
