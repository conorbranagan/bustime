# MTA BusTime Status

Just a basic script to show you where nearby buses are. There are only a couple stops that I care about hardcoded at the moment but maybe eventually this could parse all of the GTFS data.

**Example usage:** `API_KEY=YOUR_API_KEY ./bus_status.py -l Q18 -s 1`

**Full details:**

```bash
usage: bus_status.py [-h] [-l BUS_LINE] [-o OPERATOR] -s STOP

Use the BusTime API to get information on nearby buses.

optional arguments:
  -h, --help            show this help message and exit
  -l BUS_LINE, --bus_line BUS_LINE
                        Name of the bus line, e.g. Q18
  -o OPERATOR, --operator OPERATOR
                        Name of the bus operator. Options: MTA_NYCT, MTABC
  -s STOP, --stop STOP  The stop to get data for (by number).
                        Options:
                            1. 30th Ave & 36th Street
                            2. Woodside Ave - 60th Street
```

