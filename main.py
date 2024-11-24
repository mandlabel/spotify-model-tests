import sys
import json
import random
import requests
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Load the Bearer token from the .env file
bearer_token = os.getenv("BEARER_TOKEN")
filename = sys.argv[1]

# Check if Bearer token is loaded
if not bearer_token:
    print("Error: Bearer token is missing in the .env file.")
    exit(1)

# Load the test suite
with open(filename, "r") as file:
    test_suite = json.load(file)

input_list = test_suite["test_suite"]["input_list"]
output_list = test_suite["test_suite"]["output_list"]

# Initialize these variables; they will be updated during the tests
queries = [
    "Michael Jackson", "Taylor Swift", "Drake", "Adele", "Beyoncé",
    "Ed Sheeran", "The Weeknd", "Billie Eilish", "Lady Gaga", "Eminem",
    "Rockstar", "Blinding Lights", "Shape of You", "Rolling in the Deep",
    "Bad Guy", "Uptown Funk", "Shallow", "God's Plan", "Someone Like You",
    "Bohemian Rhapsody"
]
sample_playlist_id = None
sample_track_id = ['spotify:track:27ooJRSmsdwshBQGoUZE3p', 'spotify:track:3RlsVPIIs5KFhLFhxZ4iDF', 'spotify:track:0e7ipj03S05BNilyu5bRzt']

# Map inputs to their corresponding routes in your SUT
input_to_route = {
    "USE_PLAYER_I": {"route": "/player/current", "method": "GET", "check_body": True},
    "FETCH_OWN_PLAYLISTS_I": {"route": "/playlists", "method": "GET", "check_body": True},
    "GET_MY_PROFILE_I": {"route": "/profile", "method": "GET", "check_body": True},
    "CREATE_PLAYLIST_I": {"route": "/playlist", "method": "POST", "check_body": True, "body": {"name": "MBT_Test_Playlist", "description": "Default_Test_Description", "public": False}},
    "MANAGE_PLAYLIST_DATA_I": {"route": "/playlist/{id}", "method": "PUT", "check_body": True, "params": {"id": None}, "body": {"name": "MBT_Test_Playlist_Modified", "description": "New_Test_Description"}},  # No ID initially
    "ADD_NEW_TRACK_TO_PLAYLIST_I": {
        "route": "/playlist/{id}/tracks",
        "method": "POST",
        "check_body": True,
        "params": {"id": None},  # No ID initially
        "body": {"trackUris": ['spotify:track:27ooJRSmsdwshBQGoUZE3p', 'spotify:track:3RlsVPIIs5KFhLFhxZ4iDF', 'spotify:track:0e7ipj03S05BNilyu5bRzt']},  # No tracks initially
    },
    "FETCH_PLAYLIST_I": {"route": "/playlist/{id}/tracks", "method": "GET", "check_body": True, "params": {"id": None}},  # No ID initially
    "REMOVE_TRACK_FROM_PLAYLIST_I": {
        "route": "/playlist/{id}/tracks",
        "method": "DELETE",
        "check_body": True,
        "params": {"id": None},  # No ID initially
        "body": {"trackUris": ['spotify:track:27ooJRSmsdwshBQGoUZE3p']},  # No tracks initially
    },
    "START_PLAYING_I": {"route": "/player/start", "method": "POST", "check_body": True, "body": {"uris": ['spotify:track:27ooJRSmsdwshBQGoUZE3p']}},  # No tracks initially
    "SEARCH_PERFORM_I": {
        "route": "/search",
        "method": "GET",
        "check_body": True,  # Changed to True to check response body
        "params": {"query": random.choice(queries), "types": "track"},
    },
    "STOP_PLAYING_I": {"route": "/player/pause", "method": "POST", "check_body": True},
    "CHANGE_VOLUME_I": {"route": "/player/volume", "method": "POST", "check_body": True, "body": {"volumePercent": 50}},
    "SEEK_TO_POSITION_I": {"route": "/player/seek", "method": "POST", "check_body": True, "body": {"positionMs": 1000}},
}

# Define the base URL for your API
base_url = "http://localhost:3000"

# Helper function to make API requests
def make_request(method, endpoint, data=None, params=None):
    url = base_url + endpoint
    headers = {"Authorization": f"Bearer {bearer_token}"}  # Use the token from .env
    response = None

    # Add parameters to the URL if available
    if params:
        url = url.format(**params)

    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, json=data, headers=headers)

        return response
    except Exception as e:
        print(f"Error making request to {url}: {e}")
        return None

# Function to check the response body based on output keys
def check_response_body(response, output_key):
    try:
        response_body = response.json()

        if output_key == "CREATE_PLAYLIST_O":
            return "message" in response_body and "playlist" in response_body and response_body["message"] == "Playlist created"
        elif output_key == "FETCH_PLAYLIST_O":
            if "playlistId" in response_body and "tracks" in response_body:
                tracks = response_body["tracks"]
                # Check if tracks is a list and each track has the required fields
                return isinstance(tracks, list) and all(
                    "trackName" in track and "artists" in track and "album" in track and "durationMs" in track
                    for track in tracks
                )
            return False
        elif output_key == "REMOVE_TRACK_FROM_PLAYLIST_O":
            return "message" in response_body and response_body["message"] == "Tracks removed from playlist"
        elif output_key == "ADD_NEW_TRACK_TO_PLAYLIST_O":
            return "message" in response_body and response_body["message"] == "Tracks added to playlist"
        elif output_key == "USE_PLAYER_O":
            return "device" in response_body and isinstance(response_body["device"], dict)
        elif output_key == "GET_MY_PROFILE_O":
            return (
                "country" in response_body
                and "display_name" in response_body
                and "email" in response_body
                and "uri" in response_body
            )
        elif output_key == "FETCH_OWN_PLAYLISTS_O":
            return "message" in response_body and "playlists" in response_body and response_body["message"] == "Owned Playlists fetched successfully"
        elif output_key == "MANAGE_PLAYLIST_DATA_O":
            return "message" in response_body and response_body["message"] == "Playlist details updated successfully"
        elif output_key == "SEARCH_PERFORM_O":
            # You might want to add more specific checks here based on your API's response
            return "tracks" in response_body and "items" in response_body["tracks"]
        elif output_key == "SEEK_TO_POSITION_O":
            return "message" in response_body and response_body["message"] == "Seeked to position"
        elif output_key == "CHANGE_VOLUME_O":
            return "message" in response_body and response_body["message"] == "Volume changed"
        elif output_key == "START_PLAYING_O":
            return "message" in response_body and response_body["message"] == "Playback started or resumed"
        elif output_key == "STOP_PLAYING_O":
            return "message" in response_body and response_body["message"] == "Playback paused"
        else:
            return False  # Unknown output key
    except json.JSONDecodeError:
        print("Error: Invalid JSON response")
        return False

# Function to test each route and log outputs
def run_tests():
    total_tests = 0
    successful_tests = 0
    global sample_playlist_id, sample_track_id  # Declare as global to update dynamically

    # Start the timer to measure test execution time
    start_time = time.time()

    # Open a file to write response body outputs
    with open("test_results.txt", "w") as log_file:
        for i, (input_key, output_key) in enumerate(zip(input_list, output_list)):  # Map input to output
            route_info = input_to_route.get(input_key)

            # Construct route, method, and body
            route = route_info["route"]
            method = route_info["method"]
            body = route_info.get("body")
            params = route_info.get("params")

            # Update params and body with dynamic values
            if params and "id" in params:
                params["id"] = sample_playlist_id
            if body and "trackUris" in body:
                body["trackUris"] = sample_track_id 
            if body and "uris" in body:
                body["uris"] = sample_track_id

            # Make the API request 
            response = make_request(method, route, data=body, params=params)

            if response:
                # Check response body if required
                if route_info["check_body"] and not check_response_body(response, output_key):
                    print(f"❌ Test {input_key} -> {output_key}: Failed (Response body does not match expected format)")
                    log_file.write(f"❌ Test {input_key} -> {output_key}: Failed (Response body does not match expected format)\n")
                    try:
                        response_body = response.json()
                        log_file.write(f"Response body: {json.dumps(response_body, indent=2)}\n")
                    except:
                        log_file.write("Response body could not be parsed as JSON.\n")
                    total_tests += 1
                    continue  # Skip to the next test

                if response.status_code in [200, 201]:
                    print(f"✔️ Test {input_key} -> {output_key}: was successful. (OK)")
                    log_file.write(f"✔️ Test {input_key} -> {output_key}: was successful. (OK)\n")
                    successful_tests += 1

                    # Capture the playlist ID dynamically for "CREATE_PLAYLIST_I"
                    if input_key == "CREATE_PLAYLIST_I" and "playlist" in response.json():
                        sample_playlist_id = response.json()["playlist"]["id"]
                        print(f"-> Captured sample_playlist_id: {sample_playlist_id}")
                        log_file.write(f"-> Captured sample_playlist_id: {sample_playlist_id}\n")

                        # Update routes that depend on playlist ID
                        input_to_route["MANAGE_PLAYLIST_DATA_I"]["params"]["id"] = sample_playlist_id
                        input_to_route["ADD_NEW_TRACK_TO_PLAYLIST_I"]["params"]["id"] = sample_playlist_id
                        input_to_route["FETCH_PLAYLIST_I"]["params"]["id"] = sample_playlist_id
                        input_to_route["REMOVE_TRACK_FROM_PLAYLIST_I"]["params"]["id"] = sample_playlist_id

                    # Extract track IDs from "SEARCH_PERFORM_I" and update the track URIs
                    if input_key == "SEARCH_PERFORM_I":
                        search_results = response.json()
                        if "tracks" in search_results and "items" in search_results["tracks"]:
                            items = search_results["tracks"]["items"]
                            sample_track_id = [f"spotify:track:{item['id']}" for item in items[:random.randint(3, 10)]]
                            print(f"-> Captured track URIs from search: {sample_track_id}")
                            log_file.write(f"-> Captured track URIs from search: {sample_track_id}\n")

                            # Update routes that depend on track IDs
                            input_to_route["ADD_NEW_TRACK_TO_PLAYLIST_I"]["body"]["trackUris"] = sample_track_id
                            input_to_route["REMOVE_TRACK_FROM_PLAYLIST_I"]["body"]["trackUris"] = sample_track_id[:1]
                            input_to_route["START_PLAYING_I"]["body"]["uris"] = sample_track_id
                else:
                    print(f"❌ Test {input_key} -> {output_key}: Failed (Expected Status Code: 200, Got: {response.status_code})")
                    log_file.write(f"❌ Test {input_key} -> {output_key}: Failed (Expected Status Code: 200, Got: {response.status_code})\n")
                    try:
                        response_body = response.json()
                        log_file.write(f"Response body: {json.dumps(response_body, indent=2)}\n")
                    except:
                        log_file.write("Response body could not be parsed as JSON.\n")
            else:
                print(f"❌ Test {input_key} -> {output_key}: Failed (No response)")
                log_file.write(f"❌ Test {input_key} -> {output_key}: Failed (No response)\n")

            total_tests += 1
            time.sleep(1)  # Sleep to avoid overwhelming the server

        # End the timer and calculate duration
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)  # Convert to milliseconds

        # Summary
        print(f"\nTest Summary:")
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests} ✔️")
        print(f"Failed Tests: {total_tests - successful_tests} ❌")
        print(f"Execution Time: {duration_ms} ms")

        log_file.write(f"\nTest Summary:\n")
        log_file.write(f"Total Tests: {total_tests}\n")
        log_file.write(f"Successful Tests: {successful_tests} ✔️\n")
        log_file.write(f"Failed Tests: {total_tests - successful_tests} ❌\n")
        log_file.write(f"Execution Time: {duration_ms} ms\n")

# Run the tests
run_tests()