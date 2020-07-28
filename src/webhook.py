import sys
import requests

class Webhook:
  url_base = "https://steamdb.info/"
  session = requests.Session()
  # Just some user agent because steam db expects one
  headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'}

  def query_patch_list(self, app_id):
    params = {'appid' : app_id}

    response = self.session.get(self.__build_url(self.url_base, "patchnotes/"), params=params, headers=self.headers)

    if response.status_code != 200:
      print(f"Error in query: {response.status_code}")
      sys.exit()

    return response

  def query_patch(self, patch_id):
    response = self.session.get(self.__build_url(self.url_base, f"patchnotes/{patch_id}"), headers=self.headers)

    if response.status_code != 200:
      print(f"Error in query: {response.status_code}")
      sys.exit()

    return response

  def __build_url(self, url_base, page):
    return f"{url_base}{page}"