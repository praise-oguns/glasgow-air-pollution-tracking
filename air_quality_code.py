# ============================================================
# GLASGOW AIR QUALITY PROJECT — lambda_function.py
#
# Fetches live air quality data from Glasgow Townhead,
# translates the numbers into plain English ratings,
# and returns a structured result ready for DynamoDB and the website.
# ============================================================

import requests
import json
import os
from datetime import datetime, timezone

# --- Settings ---
# os.environ.get() reads the API key from environment variables instead of
# hardcoding it. This keeps secrets out of your code — important for security
# and required by AWS best practices. We'll set this variable in Lambda later.
LOCATION_ID = 2574  # Glasgow Townhead — covers NO2, O3, PM10, PM2.5

# Sensor IDs are hardcoded because the /latest endpoint doesn't return
# pollutant names — only numeric sensor IDs. Found during our station search.
SENSOR_NAMES = {
    5079312: "NO2",
    5079313: "PM2.5",
    5079314: "O3",
    5079315: "PM10"
}

# --- DEFRA air quality thresholds (µg/m³) ---
# Source: UK Daily Air Quality Index guidelines
THRESHOLDS = {
    "NO2":   {"Good": 40,  "Moderate": 80,  "Poor": 120},
    "PM2.5": {"Good": 10,  "Moderate": 20,  "Poor": 35},
    "PM10":  {"Good": 20,  "Moderate": 40,  "Poor": 50},
    "O3":    {"Good": 60,  "Moderate": 100, "Poor": 140},
}

# --- Advice shown to users on the website ---
ADVICE = {
    "Good":      "Air is clean. Fine for running, walking, and opening windows.",
    "Moderate":  "Acceptable for most. Sensitive people (asthma, elderly) take care.",
    "Poor":      "Avoid heavy outdoor exercise. Keep windows closed.",
    "Very Poor": "Stay indoors if possible. Especially bad for vulnerable people.",
}


def classify(pollutant, value):
    """Converts a raw µg/m³ reading into a band: Good, Moderate, Poor, or Very Poor."""
    limits = THRESHOLDS.get(pollutant)
    if limits is None:
        return "Unknown"
    if value <= limits["Good"]:
        return "Good"
    elif value <= limits["Moderate"]:
        return "Moderate"
    elif value <= limits["Poor"]:
        return "Poor"
    else:
        return "Very Poor"


def overall_rating(readings):
    """Returns the worst rating across all pollutants.
    One bad pollutant makes the whole reading bad — we never average them out."""
    ranking = ["Good", "Moderate", "Poor", "Very Poor"]
    worst = "Good"
    for pollutant, value in readings.items():
        band = classify(pollutant, value)
        if ranking.index(band) > ranking.index(worst):
            worst = band
    return worst



def fetch_glasgow_data():
    """Calls the OpenAQ API and returns a dict of pollutant readings.
    Returns None if the request fails for any reason."""
    url     = f"https://api.openaq.org/v3/locations/{LOCATION_ID}/latest"
    api_key = os.environ.get("OPENAQ_API_KEY")  # read it here, not at startup
    headers = {"X-API-Key": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        # timeout=10 — give up if OpenAQ doesn't respond within 10 seconds
        response.raise_for_status()
        # raise_for_status() throws an error if we get a bad status code
        # like 401 (bad API key) or 500 (server error), so we don't
        # silently return bad data

        readings = {}
        for sensor in response.json()["results"]:
            name = SENSOR_NAMES.get(sensor["sensorsId"])
            if name:
                readings[name] = sensor["value"]

        return readings

    except Exception as e:
        print(f"Error fetching data: {e}")
        # Lambda logs this to AWS CloudWatch so we can debug it later
        return None


def lambda_handler(event, context):
    """
    Entry point for AWS Lambda. Lambda calls this automatically on a schedule.
    'event' and 'context' are injected by AWS — we don't use them here but
    Lambda requires them in the signature.
    """
    print("Fetching Glasgow air quality data...")

    readings = fetch_glasgow_data()

    if readings is None:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to fetch air quality data"})
        }

    rating = overall_rating(readings)

    result = {
        "city":      "Glasgow",
        "station":   "Glasgow Townhead",
        "rating":    rating,
        "advice":    ADVICE[rating],
        "readings":  readings,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }

    print(json.dumps(result, indent=2))

    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }


# ============================================================
# LOCAL TESTING — only runs when you execute this file directly.
# AWS Lambda ignores this block entirely.
# ============================================================
if __name__ == "__main__":
    # Temporarily set the API key for local testing
    os.environ["OPENAQ_API_KEY"] = "edb86102210b25ea2334e714e43249dc5c01a1a6d6cc897872afba04d4718d70"

    response = lambda_handler({}, {})
    print("\nFinal response:")
    print(json.dumps(json.loads(response["body"]), indent=2))