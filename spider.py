import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome('F:/data/chromedriver.exe')


def getHtml(url):
    response = requests.get(url)
    return response.text


def getRoute(url):
    html = getHtml(url)
    htmlSoup = BeautifulSoup(html)
    trs = htmlSoup.find(attrs={"class": "pvw_date_contents"}).find("table").find_all("tr")
    route = []
    for day, tr in enumerate(trs):
        cityDiv = tr.find(attrs={"class": "tt3"})
        cities = []
        cityLies = cityDiv.find("ul").find_all("li")
        for cityLi in cityLies:
            cities += [cityLi.find(attrs={"class": "cn"}).text.replace("\n", "").replace(" ", "").replace("\t", "")]
        sitesDiv = tr.find(attrs={"class": "tt5"})
        sites = []
        sitesLies = sitesDiv.find("ul").find_all("li")
        for siteLi in sitesLies:
            sites += [siteLi.find(attrs={"class": "cn"}).text.replace("\n", "").replace(" ", "").replace("\t", "")]
        row = {"day": day, "cities": cities, "sites": sites}
        route += [row]
    return route


def getPlanList(url):
    driver.get(url)
    element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "plan-list")))
    return element.get_attribute('innerHTML')


def getRouteUrlsReadsCopies(url):
    planListSoup = BeautifulSoup(getPlanList(url))
    planLies = planListSoup.find_all("li")
    hrefs = []
    reads = []
    copies = []
    for planLi in planLies:
        hrefs += [('https:' + planLi.find(attrs={"class": "link"}).find("a").attrs['href']).replace("trip", "calendar")]
        spans = planLi.find(attrs={"class": "other-info"}).find_all("span")
        reads += [int(spans[0].text.replace("人浏览", ""))]
        copies += [int(spans[1].text.replace("人复制", ""))]
    return hrefs, reads, copies


def getCost(url):
    costSoup = BeautifulSoup(getHtml(url))
    moneyInfo = costSoup.find(attrs={"class": "moneyInfo fontYaHei"})
    try:
        return [float(moneyInfo.find("strong").text),
                str(moneyInfo.contents[-1]).replace("\n", "").replace("\t", "").replace(" ", "")]
    except Exception:
        return [-1, '']


def runCity(city):
    routesInfo = []
    for i in range(1, 400):
        try:
            hrefs, reads, copies = getRouteUrlsReadsCopies(
                'https://search.qyer.com/qp/?tab=plan&keyword=' + city + '&page=' + str(i))
        except Exception:
            print('Error in getting hrefs')
            continue
        for j, href in enumerate(hrefs):
            try:
                costUrl = href.replace("calendar", "cost")
                cost = getCost(costUrl)
                row = {"read": reads[j], "copy": copies[j], "cost": cost, "route": getRoute(href)}
                print(row)
                routesInfo += [row]
            except Exception:
                print('Error in getting route')
                continue
    data = {"keyword": city, "routesInfo": routesInfo}
    with open(city + ".json", 'w', encoding='utf-8') as file:
        dataD = json.dumps(data, ensure_ascii=False)
        file.write(dataD)


def run():
    cities = ["广州", "杭州", "北京", "长沙", "大连", "西安", "成都", "厦门"]
    for city in cities:
        runCity(city)


if __name__ == '__main__':
    run()
