import random
from datetime import datetime, timedelta


def generate_random_time_interval(
    count: int = 10,
    startdate: datetime | None = None,
    min_duration: int = 5,
    max_duration: int = 31,
) -> list[str]:
    """
    Generate random time intervals
    Time intervals are provided as string following the STAC requirements
    Example: 2018-02-12T00:00:00Z/2018-03-18T12:31:12Z

    """
    if startdate is None:
        startdate = datetime(2024, 11, 1)

    time_intervals = []
    for i in range(count):
        query_start = startdate + timedelta(days=random.randint(0, 365 - max_duration))
        query_end = query_start + timedelta(
            days=random.randint(min_duration, max_duration)
        )
        time_intervals.append(f"{query_start.isoformat()}Z/{query_end.isoformat()}Z")

    return time_intervals


def generate_random_bbox(
    count: int = 10,
    total_extent: list | None = None,
    width: float = 1.0,
    height: float = 1.0,
) -> list:
    """
    Generate a random set of latlon bounding boxes.
    Per default the bboxes will be created over EU.
    """
    if total_extent is None:
        # Default extent is set to Europe
        total_extent = [-10.0, 35.0, 30.0, 70.0]

    min_lon, min_lat, max_lon, max_lat = total_extent
    bboxes = []
    for i in range(count):
        # Ensure box fits inside the bounds
        lon = random.uniform(min_lon, max_lon - width)
        lat = random.uniform(min_lat, max_lat - height)
        bboxes.append(
            [
                round(lon, 4),
                round(lat, 4),
                round(lon + width, 4),
                round(lat + height, 4),
            ]
        )

    return bboxes
