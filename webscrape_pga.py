import requests
from bs4 import BeautifulSoup
import os

url = "https://www.pgatour.com/stats"

res = requests.get(url)
print(res.status_code)
# print(res.content)

soup = BeautifulSoup(res.content, "html.parser")
with open("stats.xml", "w") as file:
    file.write(soup.prettify())


# Get info from stats page
# <a role="link" class="chakra-linkbox__overlay css-1hnz6hu" href="/player/46046/scottie-scheffler/stats">Scottie Scheffler</a>
# <span class="chakra-text css-nxrnrc">68.131</span>