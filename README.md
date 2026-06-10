# Glasgow Air Quality Monitor

A live air quality dashboard for Glasgow that pulls data from a real UK government monitoring station, translates raw pollution readings into plain English health advice, and updates automatically every three hours.

Live site: [www.glasgowairquality.co.uk](https://www.glasgowairquality.co.uk)

---

## The Problem

Air quality data is publicly available but almost completely inaccessible to ordinary people. The raw numbers mean nothing to someone deciding whether to go for a run or let their kids play outside. This project takes that data and turns it into a single, clear answer.

---

## Why I Built This
Air pollution is one of the most underreported public health issues in the UK. Glasgow consistently ranks among the worst cities in Scotland for air quality, yet the data that exists is buried in government databases full of raw numbers that most people cannot interpret.
I wanted to build something that solves a real problem for real people. A runner deciding whether to train outside. A parent wondering if their child should play in the garden. Someone with asthma trying to plan their day. None of these people should need to understand what 87 µg/m³ of ozone means. They just need a clear answer.
This project takes publicly available pollution data from a UK government monitoring station, runs it through official DEFRA health guidelines, and returns a single plain English verdict with actionable advice. It updates itself automatically every three hours and sends email alerts when conditions become dangerous.
The sustainability angle matters here too. Environmental monitoring is one of the most important applications of cloud infrastructure right now. Councils, public health agencies, and climate-focused organisations are all investing in exactly this kind of real-time data pipeline. This project was built with that context in mind, not just as a technical exercise.
I chose Glasgow specifically because it is a city with a documented air quality problem and a population that deserves better access to information that directly affects their health.

---

## What It Does

- Fetches live pollution readings from Glasgow Townhead, an official UK national monitoring station
- Classifies each pollutant against DEFRA air quality guidelines
- Returns a plain English verdict: Good, Moderate, Poor, or Very Poor
- Displays tailored health advice based on the overall reading
- Sends email alerts automatically when air quality drops to Poor or Very Poor
- Updates itself every three hours without any manual intervention

---

## Architecture

The project runs entirely on AWS with no traditional server infrastructure.

```
OpenAQ API
    |
    v
AWS EventBridge (triggers every 3 hours)
    |
    v
AWS Lambda (Python) -- fetches, classifies, stores
    |           |
    v           v
DynamoDB     AWS SNS (email alerts if Poor or Very Poor)
    |
    v
AWS API Gateway (REST endpoint)
    |
    v
AWS S3 (static site) --> AWS CloudFront (CDN + HTTPS)
    |
    v
www.glasgowairquality.co.uk
```

**Services used:**

- EventBridge: scheduled trigger, runs the pipeline every three hours
- Lambda: serverless Python function, handles all data fetching and processing
- DynamoDB: stores each reading with a date-based partition key for historical tracking
- SNS: publishes email alerts to subscribers when air quality is poor
- API Gateway: HTTP endpoint that the frontend calls to retrieve the latest reading
- S3: hosts the static website
- CloudFront: CDN layer that adds HTTPS and global delivery in front of S3
- ACM: SSL certificate for the custom domain

---

## Data Source

Readings come from Glasgow Townhead (OpenAQ location ID 2574), part of the UK national air quality monitoring network. This station was chosen because it measures all four key pollutants: NO2, PM2.5, PM10, and O3.

The OpenAQ v3 API does not return pollutant names in the latest readings endpoint, only numeric sensor IDs. The sensor-to-pollutant mapping is hardcoded based on a one-time lookup during development.

---

## Classification Standard

Pollutants are classified using the UK DEFRA Daily Air Quality Index thresholds.

| Pollutant | Good | Moderate | Poor | Very Poor |
|-----------|------|----------|------|-----------|
| NO2 (µg/m³) | 0-40 | 41-80 | 81-120 | 120+ |
| PM2.5 (µg/m³) | 0-10 | 11-20 | 21-35 | 35+ |
| PM10 (µg/m³) | 0-20 | 21-40 | 41-50 | 50+ |
| O3 (µg/m³) | 0-60 | 61-100 | 101-140 | 140+ |

The overall rating is determined by the worst individual pollutant reading. One poor pollutant makes the whole reading poor.

---

## Project Structure

```
glasgow-air-quality/
├── lambda_function.py        # main Lambda: fetches, classifies, saves, alerts
├── reader_function.py        # reader Lambda: reads latest result from DynamoDB
├── index.html                # frontend website
└── README.md
```

---

## Local Setup

Clone the repo and install dependencies:

```bash
git clone https://github.com/praise-oguns/glasgow-air-pollution-tracking.git
cd glasgow-air-pollution-tracking
pip install requests
```

Add your OpenAQ API key to the testing block at the bottom of `lambda_function.py`, then run:

```bash
python lambda_function.py
```

---

## Deployment Notes

- Lambda runtime: Python 3.14
- The `requests` library is packaged as a Lambda Layer since it is not included in the default Lambda environment
- The OpenAQ API key is stored as a Lambda environment variable, not in the code
- DynamoDB uses `date` (YYYY-MM-DD) as the partition key
- CloudFront is configured with Origin Access Control so S3 is never exposed directly
- SSL certificate issued via AWS Certificate Manager with DNS validation through GoDaddy

---

## Potential Improvements

- Add a seven-day history chart to the frontend
- Expand coverage to multiple Glasgow monitoring stations
- Add a postcode lookup so users can find their nearest station
- Integrate with the UK Met Office forecast API to show predicted air quality

---

## Built With

Python, AWS Lambda, AWS DynamoDB, AWS S3, AWS CloudFront, AWS EventBridge, AWS SNS, AWS API Gateway, OpenAQ v3 API

Built by Praise Oguns as a cloud portfolio project.
Linkedin: www.linkedin.com/in/praise-oguns
