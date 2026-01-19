#!/bin/env python
"""
Netgear Plus CLI.

A command-line utility to interact with a Netgear switch. This tool allows users to
perform various operations on a Netgear switch, such as logging in, identifying the
switch model, collecting data, logging out, and checking switch status.

Usage:
    ngp-cli [--password <password>] [options] <command>

Commands:
    login <host>      Log in to the switch and save the cookie for future commands.
    logout            Log out from the switch and delete the saved cookie.
    identify          Identify the switch model.
    status            Display the current status of the switch.
    collect           Collect a full set of data from the switch for testing.
    parse             Parse collected pages and save data to a file.
    save              Save pages retrieved from the switch to a file.
    version           Display the CLI version.

Options:
    --password, -P    Specify the password for the switch. If not provided,
                        the NETGEAR_PLUS_PASSWORD environment variable is used.
    --debug, -d       Enable debug mode for detailed logs.
    --verbose, -v     Enable verbose mode for detailed outputs.
    --filter, -f      Filter output by a specified string.
    --json, -j        Output results in JSON format.
    --path, -p        Specify the path for saving pages or parsed data
                        (default: "pages").

Environment Variables:
    NETGEAR_PLUS_PASSWORD: Password for the switch if --password is not provided.

"""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from sys import stderr
from typing import Any

from py_netgear_plus import (
    LoginFailedError,
    NetgearSwitchConnector,
    SwitchModelNotDetectedError,
)
from py_netgear_plus import (
    __version__ as ngp_version,
)

COOKIE_FILE = Path.home() / ".netgear_plus_cookie"


def save_cookie(
    connector: NetgearSwitchConnector, filename: Path = COOKIE_FILE
) -> bool:
    """Save the authentication cookie and host to a file."""
    with Path(filename).open("w") as f:
        (cookie_name, cookie_content) = connector.get_cookie()
        json.dump(
            {
                "cookie_name": cookie_name,
                "cookie_content": cookie_content,
                "host": connector.host,
            },
            f,
        )
        return True
    return False


def load_cookie(
    connector: NetgearSwitchConnector, filename: Path = COOKIE_FILE
) -> bool:
    """Load the authentication cookie and host from a file."""
    if Path(filename).exists():
        with Path(filename).open("r") as f:
            data = json.load(f)
            connector.set_cookie(data.get("cookie_name"), data.get("cookie_content"))
            connector.host = data.get("host")
            return True
    return False


def get_saved_host() -> str | None:
    """Retrieve the saved host from the cookie file."""
    if Path(COOKIE_FILE).exists():
        with Path(COOKIE_FILE).open("r") as f:
            data = json.load(f)
            return data.get("host")
    return None


def save_switch_infos(path_prefix: str, switch_infos: dict) -> None:
    """Save switch info to file for debugging."""
    if not Path(path_prefix).exists():
        Path(path_prefix).mkdir(parents=True)
    with Path(f"{path_prefix}/switch_infos.json").open("w") as file:
        json.dump(switch_infos, file, indent=4)


def main() -> None:
    """Parse arguments and execute the corresponding command."""
    parser = parse_commandline()
    args = parser.parse_args()

    if args.command == "version":
        version_command()
        return

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        print("Enabling debug mode.", file=stderr)  # noqa: T201

    command_functions = {
        "collect": collect_command,
        "identify": identify_command,
        "login": login_command,
        "logout": logout_command,
        "parse": parse_command,
        "reboot": reboot_command,
        "save": save_command,
        "status": status_command,
        "version": version_command,
    }

    if args.command in command_functions:
        command_chooser(args, command_functions)

    else:
        if args.command:
            print(f"Invalid command: {args.command}\n", file=stderr)  # noqa: T201
        parser.print_help(stderr)


def parse_commandline() -> argparse.ArgumentParser:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Netgear Plus CLI")
    parser.add_argument(
        "--password",
        "-P",
        help="Password for the switch. "
        "Defaults to NETGEAR_PLUS_PASSWORD environment variable (if set).",
        default=os.getenv("NETGEAR_PLUS_PASSWORD"),
    )
    parser.add_argument(
        "--debug",
        "-d",
        help="Enable debug mode",
        action="store_true",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="Be talkative",
        action="store_true",
    )
    parser.add_argument(
        "--filter",
        "-f",
        help="Filter output by the provided string",
        type=str,
        default="",
    )
    parser.add_argument(
        "--json",
        "-j",
        help="Output in JSON format",
        action="store_true",
    )
    parser.add_argument(
        "--path",
        "-p",
        help="Path to save pages and parsed data",
        type=str,
        default="pages",
    )
    subparsers = parser.add_subparsers(dest="command")

    login_parser = subparsers.add_parser(
        "login", help="Login to the switch and save the cookie"
    )
    login_parser.add_argument("host", help="Netgear Switch IP address")

    identify_parser = subparsers.add_parser(
        "identify", help="Identify the switch model"
    )
    identify_parser.add_argument(
        "host", help="Netgear Switch IP address", nargs="?", default=""
    )

    subparsers.add_parser("collect", help="Collect a full set of data for testing")
    subparsers.add_parser("logout", help="Logout from the switch and delete the cookie")
    subparsers.add_parser("parse", help="Parse pages and save data to file")
    subparsers.add_parser("reboot", help="Reboot the switch")
    subparsers.add_parser("save", help="Save pages to file")
    subparsers.add_parser("status", help="Display switch status")
    subparsers.add_parser("version", help="Display CLI version")

    return parser


def command_chooser(
    args: argparse.Namespace, command_functions: dict[str, Any]
) -> None:
    """Choose the appropriate command function based on the command-line arguments."""
    connector = None
    if args.command == "login":
        if not args.password:
            print("Password is required for login.", file=stderr)  # noqa: T201
            return
        connector = NetgearSwitchConnector(args.host, args.password)
    elif args.command == "identify":
        host = args.host or get_saved_host()
        if not host:
            print("Host is required for identify.", file=stderr)  # noqa: T201
            return
        connector = NetgearSwitchConnector(str(host), args.password)
    else:
        saved_host = get_saved_host()
        if not saved_host:
            print("Host not found. Please login first.", file=stderr)  # noqa: T201
            return
        connector = NetgearSwitchConnector(saved_host, args.password)

    try:
        command_functions[args.command](connector, args)
    except LoginFailedError:
        print("Invalid credentials. Please login again.", file=stderr)  # noqa: T201
        if Path.exists(COOKIE_FILE):
            Path(COOKIE_FILE).unlink()


def collect_command(
    connector: NetgearSwitchConnector, args: argparse.Namespace
) -> bool:
    """Save pages to file."""
    if not load_cookie(connector):
        print("Not logged in.", file=stderr)  # noqa: T201
        return False
    model_name = connector.autodetect_model().MODEL_NAME
    n = ["first", "second"]
    for i in range(2):
        if i:
            if args.verbose:
                print("Waiting 10 seconds...", file=stderr)  # noqa: T201
            time.sleep(10)
        path = f"{args.path}/{model_name}/{i}"
        if not Path(path).exists():
            Path(path).mkdir(parents=True, exist_ok=True)
        if args.verbose:
            print(f"Saving {n[i]} set of pages in {path}", file=stderr)  # noqa: T201
        connector.save_pages(path)
    for i in range(2):
        path = f"{args.path}/{model_name}/{i}"
        if args.verbose:
            print(f"Parsing {n[i]} set of pages in {path}", file=stderr)  # noqa: T201
        connector.turn_on_offline_mode(path)
        switch_infos = connector.get_switch_infos()
        switch_infos["switch_ip"] = "192.168.0.1"
        save_switch_infos(path, switch_infos)
    connector.turn_on_online_mode()
    path = f"{args.path}/{model_name}/0"
    if args.verbose:
        print(  # noqa: T201
            f"Logging out to collect autodetect pages.\nSaving in {path}.", file=stderr
        )
    logout_command(connector, args)
    connector.save_autodetect_templates(path)
    return True


def identify_command(
    connector: NetgearSwitchConnector,
    args: argparse.Namespace,
) -> bool:
    """Identify the switch model and print the model name."""
    del args
    try:
        model = connector.autodetect_model()
    except SwitchModelNotDetectedError:
        print("Failed to detect switch model.", file=stderr)  # noqa: T201
        return False
    else:
        print(f"Switch model: {model.MODEL_NAME}")  # noqa: T201
        return True


def login_command(connector: NetgearSwitchConnector, args: argparse.Namespace) -> bool:
    """Attempt to login and save the cookie."""
    try:
        if connector.get_login_cookie() and save_cookie(connector):
            if args.verbose:
                print("Login successful.", file=stderr)  # noqa: T201
            return True
    except LoginFailedError:
        print("Invalid credentials.", file=stderr)  # noqa: T201
    return False


def logout_command(
    connector: NetgearSwitchConnector,
    args: argparse.Namespace,
) -> bool:
    """Logout from the switch and delete the cookie."""
    has_cookie = load_cookie(connector)
    if Path.exists(COOKIE_FILE):
        if args.verbose:
            print("Deleting cookie file...", file=stderr)  # noqa: T201
        Path(COOKIE_FILE).unlink()
    if not has_cookie:
        print("Not logged in.", file=stderr)  # noqa: T201
        return False
    if connector.delete_login_cookie():
        return True
    print("Logout failed.", file=stderr)  # noqa: T201
    return False


def save_command(connector: NetgearSwitchConnector, args: argparse.Namespace) -> bool:
    """Save pages to file."""
    if not load_cookie(connector):
        print("Not logged in.", file=stderr)  # noqa: T201
        return False
    if not Path(args.path).exists():
        Path(args.path).mkdir(parents=True, exist_ok=True)
    if args.verbose:
        print("Saving html pages...", file=stderr)  # noqa: T201
    connector.save_pages(args.path)
    return True


def status_command(connector: NetgearSwitchConnector, args: argparse.Namespace) -> bool:
    """Display switch status."""
    if not load_cookie(connector):
        print("Not logged in.", file=stderr)  # noqa: T201
        return False
    if args.verbose:
        print("Getting switch infos...", file=stderr)  # noqa: T201
    switch_infos = connector.get_switch_infos()
    if args.json:
        print(json.dumps(switch_infos, indent=4))  # noqa: T201
        return True
    max_key_length = max(len(key) for key in switch_infos)
    for key in sorted(switch_infos.keys()):
        if not args.filter or args.filter in key:
            print(f"{key.ljust(max_key_length)}\t{switch_infos[key]}")  # noqa: T201
    return bool(switch_infos)


def parse_command(connector: NetgearSwitchConnector, args: argparse.Namespace) -> bool:
    """Save parsed data to file."""
    if not Path(args.path).exists():
        print(f"Path does not exist: {args.path}", file=stderr)  # noqa: T201
        return False
    if args.verbose:
        print("Parsing html pages...", file=stderr)  # noqa: T201
    connector.turn_on_offline_mode(args.path)
    switch_infos = connector.get_switch_infos()
    switch_infos["switch_ip"] = "192.168.0.1"
    save_switch_infos(args.path, switch_infos)
    return True


def reboot_command(connector: NetgearSwitchConnector, args: argparse.Namespace) -> bool:
    """Save pages to file."""
    if args.verbose:
        print("Rebooting switch...", file=stderr)  # noqa: T201
    if not load_cookie(connector):
        print("Not logged in.", file=stderr)  # noqa: T201
        return False
    connector.autodetect_model()
    connector._get_switch_metadata()  # noqa: SLF001
    if connector.reboot():
        if Path.exists(COOKIE_FILE):
            if args.verbose:
                print("Reboot successful. Deleting cookie file...", file=stderr)  # noqa: T201
            Path(COOKIE_FILE).unlink()
        return True
    if args.verbose:
        print("Reboot failed.", file=stderr)  # noqa: T201
    return False


def version_command() -> bool:
    """Display CLI version."""
    print(f"Netgear Plus CLI version: {ngp_version}")  # noqa: T201
    return True


if __name__ == "__main__":
    main()
