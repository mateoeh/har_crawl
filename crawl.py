#!/usr/bin/env python3

from dataclasses import dataclass, field
import json
import sys
from typing import Iterable, Dict
import os


@dataclass
class Request:
    headers: dict
    params: dict
    body: dict


@dataclass
class Response:
    headers: dict
    content: dict


@dataclass(frozen=True, order=True)
class Endpoint:
    method: str
    url: str
    request: Request = field(compare=False, hash=False)
    response: Response = field(compare=False, hash=False)

    def __hash__(self):
        return hash(
            (
                self.method,
                self.url,
                *tuple(self.request.params.keys()),
                *tuple(self.request.body.keys()),
            )
        )


def get_url(req, start) -> str:
    url = req["url"][start:]
    idx = url.find("?")
    if idx != -1:
        url = url[:idx]
    if url[-1] != "/":
        url = url + "/"
    return url


def get_headers(req) -> Dict:
    headers = {}
    for header in req["headers"]:
        headers[header["name"]] = header["value"]
    return headers


def get_params(req) -> Dict:
    url = req["url"]
    idx = url.find("?")
    if idx == -1:
        return {}
    else:
        param_str = url[idx + 1 :]
    params = {}
    for pv in param_str.split("&"):
        try:
            param, value = pv.split("=")
        except ValueError:  # Not enough values
            param = pv.split("=")[0]
            value = ""
        params[param] = value
    return params


def get_body(req) -> Dict:
    try:
        return json.loads(req["postData"]["text"])
    except KeyError:
        return {}


def get_content(res) -> Dict:
    try:
        return json.loads(res["content"]["text"])
    except KeyError:
        return {}


def get_endpoints(file, base: str) -> Iterable[Endpoint]:
    data = json.load(file)
    endpoints = set()
    start = len(base)
    for entry in data["log"]["entries"]:
        req = entry["request"]
        res = entry["response"]
        if req["method"] == "OPTIONS":
            continue
        if req["url"].startswith(base):
            req_obj = Request(get_headers(req), get_params(req), get_body(req))
            res_obj = Response(get_headers(res), get_content(res))
            endpoints.add(
                Endpoint(req["method"], get_url(req, start), req_obj, res_obj)
            )
    return endpoints


def write_table(f, dict, key_name, value_name):
    f.write(f"{key_name} | {value_name}\n")
    f.write(":----- | :----\n")
    for key, value in dict.items():
        f.write(f"`{key}` | <code>{value}</code>\n")
    f.write("\n")


def write_request(f, endpoint):
    f.write("## Request\n\n")

    f.write("<details>\n")
    f.write("<summary>Headers</summary>\n\n")
    write_table(f, endpoint.request.headers, "Header", "Value")
    f.write("</details>\n")

    f.write("### Parameters\n\n")
    if len(endpoint.request.params) > 0:
        write_table(f, endpoint.request.params, "Parameter", "Value")
    else:
        f.write("| None |\n")
        f.write("| :--- |\n\n")

    if endpoint.method == "POST":
        f.write("### Body\n\n")
        if len(endpoint.request.body) > 0:
            write_table(f, endpoint.request.body, "Parameter", "Value")
        else:
            f.write("| None |\n")
            f.write("| :--- |\n\n")


def write_response(f, endpoint):
    f.write("## Response\n\n")

    f.write("<details>\n")
    f.write("<summary>Headers</summary>\n\n")
    write_table(f, endpoint.response.headers, "Header", "Value")
    f.write("</details>\n")

    f.write("### Content\n\n")
    f.write("```\n")
    f.write(json.dumps(endpoint.response.content, indent=4, sort_keys=True))
    f.write("\n```\n")


def write_md(base, endpoints, out_dir):
    if out_dir[-1] == "/":
        out_dir = out_dir[:-1]
    os.makedirs(out_dir, exist_ok=True)
    with open(out_dir + "/index.md", "w") as f:
        f.write(f"## `{base}`\n\n")
    i = -1
    for endpoint in sorted(endpoints):
        i += 1
        dir = out_dir + endpoint.url
        os.makedirs(dir, exist_ok=True)

        # Add endpoint to index
        with open(out_dir + "/index.md", "a") as f:
            f.write(
                f"- [`{endpoint.method} {endpoint.url}`]"
                f"({endpoint.url[1:]}{endpoint.method}_{i}.html)\n"
            )

        with open(f"{dir}{endpoint.method}_{i}.md", "w") as f:
            depth = endpoint.url.count("/") - 1
            f.write(f"[Back to index]({'../'*depth + 'index.html'})\n\n")
            f.write(f"## `{endpoint.method} {endpoint.url}`\n\n")
            write_request(f, endpoint)
            write_response(f, endpoint)


def main():
    if len(sys.argv) != 4:
        print("Usage: ./crawl.py <HAR file> <API base URL> <output dir>")
        sys.exit(1)

    har = sys.argv[1]
    base = sys.argv[2]
    out_dir = sys.argv[3]
    with open(har) as f:
        endpoints = get_endpoints(f, base)

    for endpoint in sorted(endpoints):
        print(f"{endpoint.method} {endpoint.url}")

    write_md(base, endpoints, out_dir)


if __name__ == "__main__":
    main()
