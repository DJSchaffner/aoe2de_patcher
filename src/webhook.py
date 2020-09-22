import sys
import time
import re
import json

import requests
from bs4 import BeautifulSoup
import steam.webapi

import utils

class Webhook:
  # Just some user agent because steam db expects one
  headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'}

  def query_patch_change_list(self):
    """Query a list of changed depots for all patches.
    
    Returns a list of patches and their changed depots"""
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/res/patches.json"
    response = self.__query_website(url)
    result = json.loads(response.content)["patches"]

    return result

  def query_manifests(self, depot_id):
    """Query steamdb.info for a list of manifests for a specific depot and return that list.

    Returns a list of manifests
    """
    url = f"https://steamdb.info/depot/{depot_id}/manifests/"
    response = self.__query_website(url, headers=self.headers)
    result = []

    soup = BeautifulSoup(response.content, "html.parser")
    div = soup.find("div", {'id' : 'manifests'})
    tbody = div.find("tbody")

    # Prevent Error for depots without history
    if not tbody is None:    
      for tr in tbody.findAll("tr"):
        tds = tr.findAll("td")

        date = utils.extract_date(tds[0].text)
        id = tds[2].text

        result.append({ 'date' : date, 'id' : id })

    return result

  def query_patch_list(self, app_id):
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

      # Only add actual patches from news feed to list
      if not version_re is None:        
        version = int(version_re.group(1))
        date = time.localtime(article['date'])

        result.append({ 'version': version, 'date': date})

    return result

  def query_patch(self, patch_id):
    """Query steamdb.info for a specific patch.

    Return a list of changes occured in this patch
    """
    url = f"https://steamdb.info/patchnotes/{patch_id}"
    response = self.__query_website(url, headers=self.headers)
    result = []

    soup = BeautifulSoup(response.content, "html.parser")

    div = soup.find("div", {"class" : "depot-history"})

    inner_divs = div.findAll("div")[1:]

    for depot_div in inner_divs:
      # @TODO Somehow execute the javascript on the page to load the change history
      print(depot_div.text)

    return result

  def __query_website(self, url: str, headers=None):
    response = requests.get(url, headers=headers)

    if not self.__is_response_successful(response):
      self.__print_response_error(response)
      sys.exit()

    return response

  def __is_response_successful(self, response: requests.Response):
    """Checks if a response returned successfully.

    Return True/False
    """

    return response.status_code == 200

  def __print_response_error(self, response: requests.Response):
    """Print the according error for a response."""
    
    print(f"Error in HTML request: {response.status_code}")