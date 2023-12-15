import sys
import json

import requests


class Webhook:
  def query_latest_version(self):
    """Returns the latest version of the patch tool.

    Returns:
        major, minor: The latest version of the patch tool (ex: 2, 0)
    """
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/version.txt"
    response = self._query_website(url)
    major, minor = list(map(int, response.text.split(".")))

    return major, minor

  def query_patches(self):
    """Query a list of all patches.

    Returns:
        list: A list of all documented patches
    """
    url = "https://raw.githubusercontent.com/DJSchaffner/AoE2PatchReverter/master/remote/patches.json"

    response = self._query_website(url)
    result = json.loads(response.content)["patches"]

    return result

  def _query_website(self, url: str, headers: dict = None, ignore_success: bool = False):
    """Query a website with the given headers.

    Args:
        url (str): The url of the website to be queried
        headers (dict, optional): The headers to use. Defaults to None.
        ignore_success (bool, optional): If set to true, check if response is 200 and exit program if it is not. Defaults to False.

    Returns:
        requests.Response: The response of the request
    """

    # Doesn't work with cloudflare blocking access
    response = requests.get(url, headers=headers)

    if (not ignore_success) and (not self._is_response_successful(response)):
      self._print_response_error(response)
      sys.exit()

    return response

  def _is_response_successful(self, response: requests.Response):
    """Checks if a response returned successfully.

    Args:
        response (requests.Response): The response to check

    Returns:
        bool: True if successful (status code 200)
    """
    return response.status_code == 200

  def _print_response_error(self, response: requests.Response):
    """Print the according error for a response.

    Args:
        response (requests.Response): The response containing the error code
    """
    print(f"Error in HTML request: {response.status_code} ({response.url})")
