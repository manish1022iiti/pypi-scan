import json

import pandas


def compare(path1, path2):
    d1 = json.load(open(path1, "r"))
    d2 = json.load(open(path2, "r"))

    packages = list(set(list(d1.keys()) + list(d2.keys())))

    data = list()
    for package in packages:
        sq1 = d1.get(package, list())
        sq2 = d2.get(package, list())

        unique1 = list(set(sq1) - set(sq2))
        unique2 = list(set(sq2) - set(sq1))
        common = list(set(sq1).intersection(set(sq2)))

        row = dict()
        row["package"] = package
        row[path1] = ", ".join(unique1)
        row[path2] = ", ".join(unique2)
        row["common"] = ", ".join(common)
        row[f"count_{path1}"] = len(unique1)
        row[f"count_{path2}"] = len(unique2)
        row[f"count_common"] = len(common)

        data.append(row)

    df = pandas.DataFrame(data)
    return df

path1 = "../results/06-Dec-2022-04-48-15-record.json"
path2 = "../../pypi-scan-qt/results/06-Dec-2022-03-50-53-record.json"
df = compare(path1, path2)
df.to_csv("analysis_without_homophones.csv")

