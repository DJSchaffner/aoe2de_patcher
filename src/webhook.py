import sys
import time
import re
import json

import requests
from bs4 import BeautifulSoup
import steam.webapi

import utils

class Webhook:
  # For some reason steamdb allows twitterbot to read all sites (https://steamdb.info/robots.txt)
  # @TODO prevent this from breaking in case steamdb decides to block twitterbot user-agent... avoid detection / rotate user agents / use selenium
  headers = {'User-Agent' : 'Twitterbot/1.0'}

  def query_latest_version(self):
    """Query the latest version number of the tool
    
    Return the latest version number"""
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/version.txt"
    response = self._query_website(url)
    result = float(response.content)

    return result

  def query_patch_change_list(self):
    """Query a list of changed depots for all patches.
    
    Returns a list of patches and their changed depots"""
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/patches.json"
    response = self._query_website(url)
    result = json.loads(response.content)["patches"]

    return result

  def query_manifests(self, depot_id):
    """Query steamdb.info for a list of manifests for a specific depot and return that list.

    Returns a list of manifests
    """
    url = f"https://steamdb.info/depot/{depot_id}/manifests/"
    response = self._query_website(url, headers=self.headers)
    result = []

    soup = BeautifulSoup(response.content, "html.parser")
    div = soup.find("div", {'id' : 'manifests'})
    tbody = div.find("tbody")

    # Prevent Error for depots without history
    if not tbody is None:    
      for tr in tbody.findAll("tr"):
        tds = tr.findAll("td")

        # Convert the text of the element into a date
        date = utils.extract_date(tds[0].text)
        id = tds[2].text

        result.append({ 'date' : date, 'id' : id })

    return result

  def query_patch_list(self, app_id: int, from_date: time.localtime):
    """Query steamdb.info for a list of patches for a specific app id.

    Returns a list of patches
    """
    params = {'appid' : app_id, 'count': 999999}
    result = []
    response = steam.webapi.webapi_request("https://api.steampowered.com/ISteamNews/GetNewsForApp/v1", "GET", None, None, params)

    # @TODO Add check for valid response

    for article in response['appnews']['newsitems']['newsitem']:
      # Search for patches in newsitems (At time of writing patch news have a 5+ digit patch version in the title)
      version_re = re.search(r"^.* (\d{5,})$", article['title'])

      # Only add actual patches from news feed to list (matches regex)
      if not version_re is None:        
        version = int(version_re.group(1))
        date = time.gmtime(article['date'])

        if date > from_date:
          result.append({ 'version': version, 'date': date})

    return result

  def query_filelist(self, version: int, depot_id: int):
    """Query a file list for a certain version and depot it.

    Returns the content of the found file or None if the file could not be found"""
    url = f"https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/{version}/{depot_id}.txt"
    response = self._query_website(url, ignore_success=True)
    result = None

    if self._is_response_successful(response):
      result = response.content.decode("utf-8")

    return result

  def _query_website(self, url: str, headers=None, ignore_success=False):
    response = requests.get(url, headers=headers)

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