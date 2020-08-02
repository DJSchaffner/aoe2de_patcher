import sys
import datetime
import re

import requests
from bs4 import BeautifulSoup

import utils

class Webhook:
  # Url to be requested
  url_base = "https://steamdb.info/"

  # Just some user agent because steam db expects one
  headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'}

  def query_manifests(self, depot_id):
    """Query steamdb.info for a list of manifests for a specific depot and return that list.

    Returns a list of manifests
    """
    response = requests.get(self.__build_url(self.url_base, f"depot/{depot_id}/manifests/"), headers=self.headers)
    result = []

    if self.__is_response_successful(response):
      self.__print_response_error(response)
      sys.exit()

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

    params = {'appid' : app_id}
    result = []

    response = requests.get(self.__build_url(self.url_base, "patchnotes/"), params=params, headers=self.headers)

    if self.__is_response_successful(response):
      self.__print_response_error(response)
      sys.exit()

    soup = BeautifulSoup(response.content, "html.parser")
    tbody = soup.find("tbody")
    
    for tr in tbody.findAll("tr"):
      tds = tr.findAll("td")

      date = utils.extract_date(tds[0].text)
      version_re = re.search(r"\d+", tds[1].text.strip('\n'))
      id = tds[4].text

      date_str = date.strftime("%d/%m/%Y")
      
      # Only store patches with official patch number and title
      if not version_re is None:
        result.append({ 'title' : f"{version_re.group(0)} - {date_str}", 'date' : date, 'id' : id })

    return result

  def query_patch(self, patch_id):
    """Query steamdb.info for a specific patch.

    Return a list of changes occured in this patch
    """

    response = requests.get(self.__build_url(self.url_base, f"patchnotes/{patch_id}"), headers=self.headers)
    result = []

    if self.__is_response_successful(response):
      self.__print_response_error(response)
      sys.exit()

    soup = BeautifulSoup(response.content, "html.parser")

    div = soup.find("div", {"class" : "depot-history"})

    inner_divs = div.findAll("div")[1:]

    for depot_div in inner_divs:
      # @TODO Somehow execute the javascript on the page to load the change history
      print(depot_div.text)

    return result

  def __build_url(self, url_base, page):
    """Construct a url from a base page and the rest.

    Return the constructed url
    """

    return f"{url_base}{page}"

  def __is_response_successful(self, response: requests.Response):
    """Checks if a response returned successfully.

    Return True/False
    """

    return response.status_code != 200

  def __print_response_error(self, response: requests.Response):
    """Print the according error for a response."""
    
    print(f"Error in HTML request: {response.status_code}")