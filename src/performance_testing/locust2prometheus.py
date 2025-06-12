import argparse
import pathlib
from urllib.parse import urlparse
import pandas as pd
import re

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import basic_auth_handler


class LocustExporter:
    def __init__(self, csv_path: str, job_prefix: str):
        """
        Export locust metrics via prometheus pushgateway
        """
        self.csv_path = csv_path
        self.job_prefix = job_prefix

        self._labels = ["type", "name"]

        self.drop_aggregated = True

    def _format_metric_name(self, name: str) -> str:
        """
        Format metric name according to prometheus best practices
        """
        return f"locust_{name.replace(" ", "_")
            .replace("/s", "_per_second")
            .replace("%", "_percentile")
            .replace(".", "_")
            .lower()
            .replace("count", "count_total")
            .replace("time", "time_seconds")
            .replace("size", "size_bytes")}"

    def _get_metric_value(self, metric, value):
        if metric.endswith("time_seconds"):
            return value / 1000.0
        return value

    def push(self, pushgw_url: str, user: str, pwd: str):
        """
        Push locust stats to gateway
        """
        # read stats
        df = pd.read_csv(self.csv_path)

        # authentication function
        def my_auth_handler(url, method, timeout, headers, data):
            return basic_auth_handler(url, method, timeout, headers, data, user, pwd)

        # iterate over all rows in the df, columns are the metric
        # each row represents a group (job) to be pushed
        for _, row in df.iterrows():
            # pushgateway metric registry
            registry = CollectorRegistry()

            row_name = row.get("Name").lstrip("/")
            if self.drop_aggregated and row_name == "Aggregated":
                continue

            job_name = f"{self.job_prefix}_{row_name}"
            label_vals = [row.get(label.capitalize()) for label in self._labels]
            row.drop(
                labels=[label.capitalize() for label in self._labels], inplace=True
            )
            for m in row.index.values:
                name = self._format_metric_name(m)
                # remove stats with a number in the name
                if len(re.findall(r"\d+", name)) > 0:
                    continue
                metric_val = self._get_metric_value(name, row.get(m))
                g = Gauge(
                    name, "", labelnames=["method", "endpoint"], registry=registry
                )
                g.labels(*label_vals).set(metric_val)

            push_to_gateway(
                pushgw_url, job=job_name, registry=registry, handler=my_auth_handler
            )


def valid_url(url):
    parsed = urlparse(url)
    if not all([parsed.scheme in ("http", "https"), parsed.netloc]):
        raise argparse.ArgumentTypeError(f"Invalid URL: {url}")
    return url


def main():
    parser = argparse.ArgumentParser(
        prog="locust2prometheus.py",
        description="Push locust.io metrics to Prometheus via pushgateway",
    )
    parser.add_argument("csv", type=pathlib.Path)
    parser.add_argument(
        "--pushgateway",
        type=valid_url,
        required=True,
        help="URL of the PushGateway to be used.",
    )
    parser.add_argument(
        "--user", required=True, help="Basic Auth username for PushGateway"
    )
    parser.add_argument(
        "--password", required=True, help="Basic Auth password for PushGateway"
    )
    args = parser.parse_args()

    csv_path = args.csv
    if not csv_path.is_file() or not csv_path.name.endswith("_stats.csv"):
        print(
            "Provided file is not supported. Please provide locust.io _stats.csv file."
        )
        return
    exporter = LocustExporter(csv_path, job_prefix="stac_query")
    exporter.push(pushgw_url=args.pushgateway, user=args.user, pwd=args.password)


if __name__ == "__main__":
    main()
