import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
r = requests.get('https://www.arqrio.com.br/curia/paroquias.php', verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
for a in soup.select('a[data-toggle="collapse"]'):
    print(a.prettify())
    break
