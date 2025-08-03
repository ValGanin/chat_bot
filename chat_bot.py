import requests 
from bs4 import BeautifulSoup
import pandas as pd 

urls = {
    "ai": "https://abit.itmo.ru/program/master/ai",
    "ai_product": "https://abit.itmo.ru/program/master/ai_product"
}

def fetch_curriculum(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")
    data = []
    for table in tables:
        df = pd.read_html(str(table)) [0]
        data.append(df)
    return data

curriculums = {}
for name, url in url.items():
    curriculums[name] = fetch_curriculum(url)

disciplines = {}
for prog, tables in curriculums.items():
    disciplines[prog] = []
    for table in tables:
        for _, row in table.iterrows():
            if len(row) >= 2:
                disciplines[prog].append({
                    "name": str(row[0]),
                    "desc": str(row[1])
                })

