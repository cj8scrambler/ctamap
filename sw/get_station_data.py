import json
import gtfs_kit as gk

#url="https://www.transitchicago.com/downloads/sch_data/google_transit.zip"
#feed = gk.read_feed(url, dist_units="mi")
feed = gk.read_feed('google_transit.zip', dist_units='mi')

# Generate a list of dicts representing the station data from GTFS.  Each
# Route dictionary contains a list of stations:
# { 'route_id': 'G',
#   [rest of GTFS route data]
#   'stations': [
#     { 'station_id': '40020', # GTFS stop_id with location_type=1
#       [rest of GTFS stop data for station]
#     },
#   ]
# }

stationdata = []

# Only train routes (route_type == 1)
for route in feed.routes[feed.routes.route_type == 1].to_dict('records'):
  route['stations'] = []

  # There are multiple stops at a station, so distill down to stations
  stations = set()
  for stop in feed.get_stops(route_ids=[route['route_id']]).to_dict('records'):
    stations.add(stop['parent_station'])
  for sid in stations:
    sd=feed.stops[feed.stops.stop_id == sid].to_dict('records')[0]
    route['stations'].append(sd)

  stationdata.append(route)

print(json.dumps(stationdata))
