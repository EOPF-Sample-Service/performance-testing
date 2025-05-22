from locust import HttpUser, task, between
import json
import random
from performance_testing.utils import (
    generate_random_bbox,
    generate_random_time_interval,
)
import logging
from locust import events


@events.quitting.add_listener
def _(environment, **kw):
    environment.process_exit_code = 0


class STACUser(HttpUser):
    """STAC User interacting with the STAC API"""

    # Users will wait 1-3 seconds between requests
    wait_time = between(1, 3)

    def on_start(self):
        # generate random bboxes
        self.bboxes = generate_random_bbox()
        self.intervals = generate_random_time_interval()

    @task
    def search_stac(self):
        bbox = random.choice(self.bboxes)
        limit = random.randint(10, 500)
        datetime_string = random.choice(self.intervals)

        payload = {"bbox": bbox, "datetime": datetime_string, "limit": limit}

        headers = {"Content-Type": "application/json"}

        with self.client.post(
            "/search", data=json.dumps(payload), headers=headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                if "features" in response.json():
                    response.success()
                else:
                    response.failure("Missing 'features' in response")
            else:
                response.failure(f"Status code {response.status_code}")
