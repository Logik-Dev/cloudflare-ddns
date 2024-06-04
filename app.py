import os
import logging
import requests


# Logging configuration
logging.basicConfig(
    filename='update-ip.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
)
logging.getLogger().addHandler(logging.StreamHandler())

# errors
ERROR_NO_TOKEN = "CF_TOKEN is not set !"
ERROR_NO_EMAIL = "CF_EMAIL is not set !"
ERROR_NO_DOMAIN = "CF_DOMAIN is not set !"

# environment variables
token = os.environ.get("CF_TOKEN")
email = os.environ.get("CF_EMAIL")
domain = os.environ.get("CF_DOMAIN")

# base api url
CF_BASE_URL = "https://api.cloudflare.com/client/v4/zones"

# log fatal error and exit
def handle_fatal_error(msg):
   logging.critical(msg)
   exit(1)

# cloudflare token must be set
if (token == None):
    handle_fatal_error(ERROR_NO_TOKEN)

# cloudflare email must be set
if (email == None):
    handle_fatal_error(ERROR_NO_EMAIL)

# cloudflare domain must be set
if (domain == None):
    handle_fatal_error(ERROR_NO_DOMAIN)

# get current public ip
current_ip = requests.get('https://checkip.amazonaws.com').text.strip()

# prepare headers
token = "Bearer " + token
headers = {'Authorization': token, 'X-Auth-Email': email}

# handle request
def handle_request(req):
  if(req.status_code >= 400): 
    error_msg = req.json().get("errors")[0].get("message")
    handle_fatal_error("HTTP error with url " + req.url + ", Cause: " + error_msg)
  return req.json()

# get zone
r = requests.get(CF_BASE_URL, headers=headers)
json = handle_request(r)
zone = [zone for zone in json.get('result') if zone.get("name") == domain]

# no zone found
if (len(zone) == 0):
   handle_fatal_error("No zone found")

# get record
zone_id = zone[0].get("id")
records_url = CF_BASE_URL + "/{zone_id}/dns_records".format(zone_id=zone_id)
r = requests.get(records_url, headers=headers)
json = handle_request(r)
record = [rec for rec in json.get('result') if rec.get('name') == domain]

# no record found
if (len(record) == 0):
   handle_fatal_error("No record found")

# zone_id and record_id
record_id = record[0].get('id')
record_ip = record[0].get('content')

# ip is the same skipping update
if (record_ip == current_ip):
   logging.info("Skip record update since current ip matches with record ip: " + record_ip)
   exit(0)

# update ip
data = {'content': current_ip, 'name': domain, 'type': 'A', 'comment': 'Updated by python script'}
patch_ip_url = CF_BASE_URL + "/{zone_id}/dns_records/{record_id}".format(zone_id=zone_id, record_id=record_id)
json = handle_request(requests.put(patch_ip_url, json=data, headers=headers))

logging.info('Domain record successfully updated with ip: ' + current_ip)
exit(0)