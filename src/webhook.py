import sys
import time
import re
import json

import requests
from bs4 import BeautifulSoup
import steam.webapi
import cloudscraper

import utils

class Webhook:
  def query_latest_version(self):
    """Query the latest version number of the tool
    
    Return the latest version number"""
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/version.txt"
    response = self._query_website(url)
    result = float(response.content)

    return result

  def query_patches(self):
    """Query a list of all patches.
    
    Returns a list of patches"""
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/patches.json"
    response = self._query_website(url)
    result = json.loads(response.content)["patches"]

    return result

  def query_filelist(self, version: int, depot_id: int):
    """Query a file list for a certain version and depot it.

    Returns the content of the found file or None if the file could not be found"""
    url = f"https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/{version}/{depot_id}.txt"
    response = self._query_website(url, ignore_success=True)
    result = response.content.decode("utf-8")

    return result

  def _query_website(self, url: str, headers=None, ignore_success=False):
    # Doesn't work with cloudflare blocking access
    #response = requests.get(url, headers=headers)

    # Workaround for the cloudflare protection
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url, headers=headers)

    if (not ignore_success) and (not self._is_response_successful(response)):
      self._print_response_error(response)
      sys.exit()

    return response

  def _is_response_successful(self, response: requests.Response):
    """Checks if a response returned successfully.

    Return True/False
    """
    return response.status_code == 200

  def _print_response_error(self, response: requests.Response):
    """Print the according error for a response."""
    print(f"Error in HTML request: {response.status_code} ({response.url})")