import sys
import os
import pandas as pd


class LocustExporter:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

        pages_dir = os.path.join(os.path.dirname(self.csv_path), "pages")
        self.prom_metric_file = os.path.join(pages_dir, "metrics")
        # create .nojekyl
        with open(os.path.join(pages_dir, ".nojekyl"), "w") as nojekyl:
            pass

        # remove metric file on existence
        if os.path.exists(self.prom_metric_file):
            os.remove(self.prom_metric_file)

        self._labels = ["type", "name"]
        self._metric_type = "gauge"

    def _format_metric_name(self, name: str) -> str:
        """
        Format metric name according to prometheus best practices
        """
        return (
            name.replace(" ", "_")
            .replace("/s", "_per_second")
            .replace("%", "_percentile")
            .replace(".", "_")
            .lower()
            .replace("count", "count_total")
            .replace("time", "time_seconds")
            .replace("size", "size_bytes")
        )

    def _get_metric_value(self, metric, value):
        if metric.endswith("time_seconds"):
            return value / 1000.0
        return value

    def export(self):
        """
        Export locust stats to prometheus file
        """
        df = pd.read_csv(self.csv_path)

        # iterate over all rows in the df, columns are the metric
        with open(self.prom_metric_file, "a") as promf:
            # write stats
            for _, row in df.iterrows():
                labels_str = ",".join(
                    [
                        '{}="{}"'.format(label, row.get(label.capitalize()))
                        for label in self._labels
                    ]
                )
                row.drop(
                    labels=[label.capitalize() for label in self._labels], inplace=True
                )
                for m in row.index.values:
                    name = self._format_metric_name(m)
                    metric_val = self._get_metric_value(name, row.get(m))
                    content = (
                        f"# HELP {name}\n"
                        f"# TYPE {name} {self._metric_type}\n"
                        f"{name}{{{labels_str}}} {metric_val}\n"
                    )
                    promf.write(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python locust2prometheus.py <path_to_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if csv_path.endswith("_stats.csv"):
        exporter = LocustExporter(csv_path)
        exporter.export()
    else:
        print(
            "Provided file is not supported. Please provide locust.io _stats.csv file."
        )


if __name__ == "__main__":
    main()
