import requests
from bs4 import BeautifulSoup
import pandas as pd
from googletrans import Translator

translator = Translator()

def get_translation(en_str):
    result = translator.translate(en_str, src="en", dest="zh-CN")
    return result.text

url_template = "https://www.fda.gov/drugs/drug-safety-and-availability/{}-drug-safety-communications"
year_list = list(range(2012, 2022))
url_list = [url_template.format(x) for x in year_list]

warning_str_list = []
warning_link_list = []

for url in url_list:
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    link_list = [i.find("a") for i in soup.findAll('div', role="main")[0].findAll("li")]
    link_list = list(map(lambda x: (x["href"], x.text), link_list))
    link_list = list(filter(lambda x: "/drugs/drug-safety-and-availability/fda-drug-safety-communication-" in x[0],
                            link_list))
    for i in link_list:
        warning_link_list.append(i[0])
        warning_str_list.append(i[1])

warning_str_chn_list = [get_translation(x) for x in warning_str_list]

df_fda_warning = pd.DataFrame({
    "warning": warning_str_list,
    "warning_chn": warning_str_chn_list,
    "link": warning_link_list
}).to_csv("processed/fda_warning.csv", index=False)
