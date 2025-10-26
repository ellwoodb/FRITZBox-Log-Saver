"""
FRITZ!Box Log Saver

A Python application that retrieves event log data from FRITZ!Box devices
and saves it in structured JSON Lines format for use with Promtail and Grafana Loki.
"""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
import yaml

# Configuration constants
LOGIN_SID_ROUTE = "/login_sid.lua?version=2"
DATA_LUA_ENDPOINT = "data.lua"
DEFAULT_TIMEOUT = 30
LOG_SOURCE = "fritzbox"
LOG_COMPONENT = "system"

# Log level classification patterns
ERROR_PATTERNS = [
    "fehler", "error", "gescheitert", "fehlgeschlagen", "failed", "failure", 
    "nicht verfügbar", "unavailable", "timeout", "abgebrochen", "cancelled",
    "unterbrochen", "interrupted", "verbindung getrennt", "disconnected",
    "authentifizierungsfehler", "authentication error", "login failed",
    "anmeldung gescheitert", "verbindungsaufbau fehlgeschlagen",
    "connection failed", "nicht erreichbar", "unreachable"
]

WARNING_PATTERNS = [
    "warnung", "warning", "achtung", "hinweis",
    "timeout", "zeitüberschreitung", "langsam", "slow",
    "schwach", "weak", "instabil", "unstable",
    "überlastet", "overload", "verzögerung", "delay",
    "trennung", "disconnect", "verbindung unterbrochen",
    "zwangstrennung", "zuvorzukommen", "wartung", "maintenance"
]

SUCCESS_PATTERNS = [
    "erfolgreich", "successful", "successfully", "established", "hergestellt",
    "verbunden", "connected", "aktiviert", "activated", "verfügbar", "available",
    "erhalten", "received", "aktualisiert", "updated", "installiert", "installed"
]


class FritzBoxError(Exception):
    """Base exception for FRITZ!Box related errors."""


class AuthenticationError(FritzBoxError):
    """Exception raised for authentication failures."""


class FritzBoxConnectionError(FritzBoxError):
    """Exception raised for connection failures."""


class LoginState:
    def __init__(self, challenge: str, blocktime: int):
        """
        Initializes a LoginState object.

        Parameters:
            challenge (str): The challenge string used for authentication.
            blocktime (int): The time duration for which login is blocked after multiple failed attempts.
        """
        self.challenge = challenge
        self.blocktime = blocktime
        self.is_pbkdf2 = challenge.startswith("2$")


def get_sid(box_url: str, username: str, password: str) -> str:
    """
    Retrieves the session ID (SID) for a given user by performing the login process.

    Parameters:
        box_url: The URL of the login service
        username: The user's username
        password: The user's password

    Returns:
        The session ID (SID) if the login is successful

    Raises:
        FritzBoxConnectionError: If connection to FRITZ!Box fails
        AuthenticationError: If authentication fails
    """
    try:
        state = get_login_state(box_url)
    except Exception as ex:
        raise FritzBoxConnectionError("Failed to get challenge") from ex

    if state.is_pbkdf2:
        print("PBKDF2 supported")
        challenge_response = calculate_pbkdf2_response(
            state.challenge, password)
    else:
        print("Falling back to MD5")
        challenge_response = calculate_md5_response(state.challenge, password)

    if state.blocktime > 0:
        print(f"Waiting for {state.blocktime} seconds...")
        time.sleep(state.blocktime)

    try:
        sid = send_response(box_url, username, challenge_response)
    except Exception as ex:
        raise FritzBoxConnectionError("Failed to login") from ex

    if sid == "0000000000000000":
        raise AuthenticationError("Wrong username or password")

    return sid


def get_login_state(box_url: str) -> LoginState:
    """
    Retrieves the login state from the given box URL.

    Parameters:
        box_url: The URL of the login service

    Returns:
        LoginState object containing challenge and blocktime information

    Raises:
        FritzBoxConnectionError: If unable to retrieve login state
    """
    url = box_url + LOGIN_SID_ROUTE
    try:
        http_response = urllib.request.urlopen(url, timeout=DEFAULT_TIMEOUT)
        xml = ET.fromstring(http_response.read())

        challenge_elem = xml.find("Challenge")
        blocktime_elem = xml.find("BlockTime")

        if challenge_elem is None or challenge_elem.text is None:
            raise FritzBoxConnectionError(
                "Invalid challenge response from FRITZ!Box")

        if blocktime_elem is None or blocktime_elem.text is None:
            raise FritzBoxConnectionError(
                "Invalid blocktime response from FRITZ!Box")

        challenge = challenge_elem.text
        blocktime = int(blocktime_elem.text)

        return LoginState(challenge, blocktime)
    except (urllib.error.URLError, ET.ParseError, ValueError) as ex:
        raise FritzBoxConnectionError(
            f"Failed to retrieve login state: {ex}") from ex


def calculate_pbkdf2_response(challenge: str, password: str) -> str:
    """
    Calculates the PBKDF2 response for the given challenge and password.

    Parameters:
        challenge (str): The challenge string received during login.
        password (str): The user's password.

    Returns:
        str: The PBKDF2 response in the format "salt2$hash2_hex".
    """
    challenge_parts = challenge.split("$")
    # Extract all necessary values encoded into the challenge
    iter1 = int(challenge_parts[1])
    salt1 = bytes.fromhex(challenge_parts[2])
    iter2 = int(challenge_parts[3])
    salt2 = bytes.fromhex(challenge_parts[4])
    # Hash twice, once with static salt...
    hash1 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt1, iter1)
    # Once with dynamic salt.
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, salt2, iter2)
    return f"{challenge_parts[4]}${hash2.hex()}"


def calculate_md5_response(challenge: str, password: str) -> str:
    """
    Calculates the MD5 response for the given challenge and password.

    Parameters:
        challenge (str): The challenge string received during login.
        password (str): The user's password.

    Returns:
        str: The MD5 response in the format "challenge-md5_hex".
    """
    response = challenge + "-" + password
    # the legacy response needs utf_16_le encoding
    response = response.encode("utf_16_le")
    md5_sum = hashlib.md5()
    md5_sum.update(response)
    response = challenge + "-" + md5_sum.hexdigest()
    return response


def send_response(box_url: str, username: str, challenge_response: str) -> str:
    """
    Send the login response and return the session ID (SID).

    Parameters:
        box_url: The URL of the login service
        username: The user's username
        challenge_response: The challenge response generated during login

    Returns:
        The session ID (SID) if the response is successful

    Raises:
        FritzBoxConnectionError: If connection fails
        AuthenticationError: If authentication fails
    """
    post_data_dict = {"username": username, "response": challenge_response}
    post_data = urllib.parse.urlencode(post_data_dict).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = box_url + LOGIN_SID_ROUTE

    try:
        http_request = urllib.request.Request(url, post_data, headers)
        http_response = urllib.request.urlopen(
            http_request, timeout=DEFAULT_TIMEOUT)
        xml = ET.fromstring(http_response.read())

        sid_elem = xml.find("SID")
        if sid_elem is None or sid_elem.text is None:
            raise AuthenticationError("Invalid SID response from FRITZ!Box")

        return sid_elem.text
    except (urllib.error.URLError, ET.ParseError) as ex:
        raise FritzBoxConnectionError(
            f"Failed to send login response: {ex}") from ex


def unix_timestamp_from_strings(date_string: str, time_string: str) -> int:
    """
    Converts the given date and time strings to a Unix timestamp.

    Parameters:
        date_string (str): The date string in the format "dd.mm.yy".
        time_string (str): The time string in the format "HH:MM:SS".

    Returns:
        int: The Unix timestamp representing the provided date and time.
    """
    datetime_string = f"{date_string} {time_string}"
    datetime_obj = datetime.strptime(datetime_string, "%d.%m.%y %H:%M:%S")

    # Get the Unix timestamp
    unix_timestamp = int(datetime_obj.timestamp())

    return unix_timestamp


def get_last_timestamp(file_path: str) -> int:
    """
    Retrieves the last timestamp from a JSON Lines log file.

    Parameters:
        file_path: The path to the log file

    Returns:
        The last timestamp found in the log file or 1 if the file is empty or does not exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    log_entry = json.loads(last_line)
                    return int(log_entry.get("timestamp", 1))
            return 1
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
        return 1


def create_or_append_to_log(file_path: str, data: list) -> None:
    """
    Creates or appends data to a structured log file in JSON Lines format for Promtail.

    Parameters:
        file_path: The path to the log file
        data: A list of dictionaries containing the data to be written
    """
    last_timestamp = get_last_timestamp(file_path)
    new_entries = 0

    with open(file_path, mode='a', encoding='utf-8') as log_file:
        for entry in data:
            if int(entry["timestamp"]) > last_timestamp:
                # Determine log level based on message content
                log_level = determine_log_level(entry["message"])
                
                log_entry = {
                    "timestamp": entry["timestamp"],
                    "level": log_level,
                    "source": LOG_SOURCE,
                    "message": entry["message"],
                    "labels": {
                        "date": entry["date"],
                        "time": entry["time"],
                        "code": entry["code"],
                        "component": LOG_COMPONENT,
                        "severity": log_level
                    }
                }
                log_file.write(json.dumps(
                    log_entry, ensure_ascii=False) + '\n')
                new_entries += 1

    if new_entries > 0:
        print(f"Added {new_entries} new log entries")


def get_fritzbox_event_log(url: str, sid: str, excludes: list) -> list:
    """
    Retrieves the event log data from the FritzBox using the provided session ID (SID).

    Parameters:
        url: The base URL of the FritzBox
        sid: The session ID obtained after successful login
        excludes: List of message patterns to exclude from logs

    Returns:
        A list of dictionaries representing the event log data

    Raises:
        FritzBoxConnectionError: If unable to retrieve logs
    """
    # Construct the data.lua endpoint URL
    if url.endswith("/"):
        data_url = f"{url}{DATA_LUA_ENDPOINT}"
    else:
        if DATA_LUA_ENDPOINT not in url:
            data_url = f"{url}/{DATA_LUA_ENDPOINT}"
        else:
            data_url = url

    request_data = {
        'xhr': 1,
        'sid': sid,
        'lang': 'de',
        'page': 'log',
        'xhrId': 'log',
    }

    try:
        response = requests.post(
            data_url, data=request_data, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as ex:
        raise FritzBoxConnectionError(
            f"Failed to retrieve event log: {ex}") from ex

    if response.status_code == 200:
        # Process the event log data in the response
        event_log_data = response.text
        print(f"Response length: {len(event_log_data)}")
        print(f"Response starts with: {event_log_data[:100]}")

        # Check if response is HTML (error page) or JSON
        if event_log_data.strip().startswith('<!DOCTYPE html>') or event_log_data.strip().startswith('<html'):
            print("ERROR: Received HTML response instead of JSON. This usually means:")
            print("1. The session ID (SID) is invalid or expired")
            print("2. The URL is incorrect")
            print("3. The FritzBox requires additional authentication")
            return []

        try:
            jdata = json.loads(event_log_data)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Response text (first 500 chars): {event_log_data[:500]}")
            return []

        logData = jdata.get("data", {}).get("log", [])
        if not logData:
            print("No log data found in response")
            return []

        csvData = []
        print(f"Processing {len(logData)} log entries...")

        for i, entry in enumerate(list(logData)[::-1]):
            # Check if entry is a dictionary with required fields
            if not isinstance(entry, dict):
                print(f"Skipping non-dict entry {i}: {entry}")
                continue

            # Extract data from dictionary format
            date_str = entry.get('date', '')
            time_str = entry.get('time', '')
            message = entry.get('msg', '')
            entry_id = entry.get('id', '')

            if not all([date_str, time_str, message]):
                print(
                    f"Skipping incomplete entry {i}: missing required fields")
                continue

            if not is_excluded(message, excludes):
                cdata = {
                    "timestamp": unix_timestamp_from_strings(date_str, time_str),
                    "date": date_str,
                    "time": time_str,
                    "message": message,
                    "code": str(entry_id),
                }
                csvData.append(cdata)
            # else:
            #     print(f"Excluded Message: {Message}")

        return csvData
    else:
        print(
            f"Failed to retrieve event log. Status code: {response.status_code}")
        return []


def determine_log_level(message: str) -> str:
    """
    Determines the log level based on the content of the message.

    Parameters:
        message: The log message to analyze

    Returns:
        The appropriate log level: 'error', 'warning', 'info', or 'debug'
    """
    message_lower = message.lower()
    
    # Special cases: planned/preventive actions should be warnings, not errors
    if ("zwangstrennung" in message_lower and "zuvorzukommen" in message_lower) or \
       ("kurz unterbrochen" in message_lower and "zuvorzukommen" in message_lower):
        return "warning"
    
    # Check for error patterns (highest priority)
    for pattern in ERROR_PATTERNS:
        if pattern in message_lower:
            return "error"
    
    # Check for warning patterns (medium priority)
    for pattern in WARNING_PATTERNS:
        if pattern in message_lower:
            return "warning"
    
    # Check for success patterns (info level)
    for pattern in SUCCESS_PATTERNS:
        if pattern in message_lower:
            return "info"
    
    # Check specific FRITZ!Box message patterns
    if any(word in message_lower for word in ["anmeldung", "verbindung"]):
        if any(word in message_lower for word in ["erfolgreich", "successfully"]):
            return "info"
        elif any(word in message_lower for word in ["gescheitert", "failed", "fehlgeschlagen"]):
            return "error"
    
    # Default to info level
    return "info"


def is_excluded(message: str, excludes: list) -> bool:
    """
    Checks if a message is excluded based on a list of exclusion criteria.

    The exclusion criteria can be either strings or lists of strings. For strings,
    the function checks if the item is present in the message. For lists, the function
    checks if all elements in the list are present in the message.

    Parameters:
        message: The message to be checked for exclusion
        excludes: A list of strings or lists of strings representing exclusion criteria

    Returns:
        True if the message is excluded based on any exclusion criteria, False otherwise
    """
    for item in excludes:
        if isinstance(item, str) and item in message:
            return True
        elif isinstance(item, list) and all(part in message for part in item):
            return True
    return False


def load_settings(path: str) -> dict:
    """
    Loads settings from a YAML file and returns them as a dictionary.

    Parameters:
        path: Path to the settings YAML file

    Returns:
        Dictionary containing the settings loaded from the YAML file

    Raises:
        FileNotFoundError: If the settings file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return data if data is not None else {}
    except FileNotFoundError as ex:
        raise FileNotFoundError(f"Settings file not found: {path}") from ex
    except yaml.YAMLError as ex:
        raise yaml.YAMLError(f"Invalid YAML format in {path}: {ex}") from ex


def main() -> None:
    """
    Main entry point for the FRITZ!Box Log Saver application.

    Logs in to a FRITZ!Box device, retrieves the event log data, 
    and saves it to a structured log file in JSON Lines format.
    """
    settings_file = os.path.join(os.path.dirname(sys.argv[0]), "settings.yaml")

    if not os.path.exists(settings_file):
        print("No 'settings.yaml' found")
        example_file = settings_file.replace(
            "settings.yaml", "ex_settings.yaml")
        if os.path.exists(example_file):
            print(
                "Rename the 'ex_settings.yaml' to 'settings.yaml' and fill in your data.")
            print("Then try starting the script again.")
        input("Press enter to exit...")
        sys.exit(1)

    try:
        settings = load_settings(settings_file)

        # Extract configuration with defaults
        url = settings.get("url", "http://fritz.box")
        username = settings.get("username", "")
        password = settings.get("password", "")
        excludes = settings.get("exclude", []) or []
        log_path = settings.get("logpath", "fritzLog.jsonl")

        # Validate required settings
        if not username or not password:
            print("Error: Username and password are required in settings.yaml")
            sys.exit(1)

        print(f"Using username: {username}")
        print(f"Using password: {'*' * len(password)}")
        print(f"Connecting to: {url}")

        # Authenticate and retrieve logs
        sid = get_sid(url, username, password)
        print(f"Successfully authenticated user: {username}")
        print(f"Session ID: {sid}")

        logs = get_fritzbox_event_log(url, sid, excludes)
        if logs:
            create_or_append_to_log(log_path, logs)
            print(
                f"Successfully processed {len(logs)} log entries to {log_path}")
        else:
            print("No log entries found or retrieved")

    except (FritzBoxError, FileNotFoundError, yaml.YAMLError) as ex:
        print(f"Error: {ex}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
