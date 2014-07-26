#!/usr/bin/env python

# stdlib
import argparse
import os

# 3p
import requests

API_KEY = os.environ.get('API_KEY')

# URI Constants
STOP_BASE_URI = 'http://bustime.mta.info/api/siri/stop-monitoring.json?'\
    'key={key}&OperatorRef=MTA&MonitoringRef={monitoring_ref}'\
    '&LineRef={line_ref}'
VEHICLE_BASE_URI = 'http://bustime.mta.info/api/siri/vehicle-monitoring.json?'\
    'key={key}&OperatorRef=MTA&VehicleRef={vehicle_ref}&LineRef={line_ref}'

# Bound the number of "visits" we fetch so that we don't hit the API to hard.
MAX_VISITS = 3

# Stops are hardcoded because there's no API to look this up.
STOPS = [
    ('30th Ave & 36th Street', 550601),
    ('Woodside Ave - 60th Street', 550552)
]

OPERATORS = ('MTA_NYCT', 'MTABC')

def main():
    if not API_KEY:
        print('You must set an API_KEY environment variable.')
        return

    # Generate a user-friendly list of stops for the help message.
    stop_opts = "\n".join(["    %s. %s" % (i+1, s[0])
                    for i, s in enumerate(STOPS)])

    parser = argparse.ArgumentParser(
        description='Use the BusTime API to get information on nearby buses.',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-l', '--bus_line', required=False, default='Q18',
        help='Name of the bus line, e.g. Q18')
    parser.add_argument('-o', '--operator', default='MTABC', required=False,
        help="Name of the bus operator. Options: %s" % ', '.join(OPERATORS))
    parser.add_argument('-s', '--stop', type=int, required=True,
        help="The stop to get data for (by number).\nOptions:\n%s" % stop_opts)
    options = parser.parse_args()

    # Generate a valid API url using the given options.
    stop_id = STOPS[options.stop-1][1]
    line = options.bus_line.upper()
    line_ref = "%s_%s" % (options.operator, line)
    stop_uri = STOP_BASE_URI.format(
            key=API_KEY,
            monitoring_ref=stop_id,
            line_ref=line_ref
        )

    # Fetch data from the API.
    r = requests.get(stop_uri).json()
    service = r['Siri']['ServiceDelivery']

    # If the API key is wrong then the child node is same as vehicles. Weird.
    if 'VehicleMonitoringDelivery' in service:
        print('Invalid MTA API key, please try again.')
        return

    # Error handling.
    stop_monitoring = service['StopMonitoringDelivery'][0]
    if 'ErrorCondition' in stop_monitoring:
        err = stop_monitoring['ErrorCondition']
        print("Error while fetching data: %s" % err['Description'])
        return

    visits = [Visit.from_raw(v) for v in stop_monitoring['MonitoredStopVisit']]
    if len(visits) == 0:
        print('Sorry, no buses are coming right now. '
              'Time for the subway or a cab?')
        return

    for visit in visits[:MAX_VISITS]:
        print_visit(line, visit)


def print_visit(line, visit):
    """ Print out some interesting stats for a visit.
        We'll query for the Vehicle associated with each visit so we can get
        the current stop name. I wish they would just include this...
    """
    vehicle = Vehicle.from_refs(visit.vehicle_ref, visit.line_ref)
    print("There is a {} bus {} stops away at {}."\
        .format(visit.line, visit.stops_away, vehicle.cur_stop))
    if visit.stops_away < 5:
        print("You better get moving!")


class Vehicle(object):
    @classmethod
    def from_refs(cls, vehicle_ref, line_ref):
        """ Fetches vehicle information from the API under-the-hood and returns
            a `Vehicle` instance with user-friendly properties.
        """
        vehicle_uri = VEHICLE_BASE_URI.format(
            key=API_KEY,
            vehicle_ref=vehicle_ref,
            line_ref=line_ref
        )
        r = requests.get(vehicle_uri).json()
        raw_vehicles = r['Siri']['ServiceDelivery']['VehicleMonitoringDelivery']
        if len(raw_vehicles) == 0:
            raise ValueError('No vehicle found for ref={}, line={}'\
                     .format(vehicle_ref, line_ref))
        j = raw_vehicles[0]['VehicleActivity'][0]['MonitoredVehicleJourney']
        call = j['MonitoredCall']
        return Vehicle(j['VehicleRef'], call['StopPointName'])

    def __init__(self, ref, cur_stop):
        """ Always use `from_ref`, never __init__ directly. """
        self.ref = ref
        self.cur_stop = cur_stop


class Visit(object):
    """ A 'visit' in the API represents a bus that's active in a line
        heading to a particular stop.
    """
    @classmethod
    def from_raw(cls, raw_visit):
        j = raw_visit['MonitoredVehicleJourney']
        call = j['MonitoredCall']
        stops_away = call['Extensions']['Distances']['StopsFromCall']
        return Visit(j['PublishedLineName'], j['LineRef'],
                     j['VehicleRef'], stops_away)

    def __init__(self, line, line_ref, vehicle_ref, stops_away):
        """ Always use `from_raw`, never __init__ directly. """
        self.line = line
        self.line_ref = line_ref
        self.vehicle_ref = vehicle_ref
        self.stops_away = stops_away


if __name__ == '__main__':
    main()