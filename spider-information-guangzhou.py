import json
import requests
from bs4 import BeautifulSoup
import os
import warnings

warnings.filterwarnings('ignore')


def getCookies():
    cookies = {}
    cookieStr = "_qyeruid=CgIBAV8NN6CFAkFfTsScAg==; new_uv=1; new_session=1; _guid=R0b40500-b6fb-271d-94af-b68ed13bcab7; PHPSESSID=831fbb4b3dc64d681b6b8ee4d1bda7a3; __utmc=253397513; ql_guid=QL5e39c7-8c94-4c3b-aa5a-a540a666959a; source_url=https%3A//plan.qyer.com/trip/create%3Fvcode%3D4173f4c4a00e50ce547e276f3424af85%26; isnew=1594701754400; __utma=253397513.833478904.1594701746.1594870371.1594879358.12; __utmz=253397513.1594879358.12.3.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmt=1; ql_created_session=1; ql_stt=1594879357772; ql_vts=14; plan_token=2d459a0590bea47508ed6c388690fc30; plan_code=V2YJYFFnBz9TYlI9CmoNOg; ql_seq=3; __utmb=253397513.6.9.1594879374872"
    for line in cookieStr.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    return cookies


session = requests.session()
requests.utils.add_dict_to_cookiejar(session.cookies, getCookies())


def getSiteListInfo(page):
    response = session.get(
        'https://plan.qyer.com/api/v3/recommend/getpoilist?city_id=11808&range=1&page=' + str(page) + '&type=0')
    return response.json()


def getDetail(poiId):
    response = session.get('https://plan.qyer.com/api/v3/poi/getpoidetail?plan_id=23196264&poi_id=' + str(poiId))
    return response.json()


def getHtml(url):
    html = session.get(url)
    return html.text


def getSiteDetailScore(html):
    htmlSoup = BeautifulSoup(html)
    try:
        details = htmlSoup.find(attrs={"class": "compo-detail-info"}).find(attrs={"class": "poi-detail"}).find("p").text
    except Exception:
        details = ''
    try:
        score = float(htmlSoup.find(attrs={"class": "poi-placeinfo clearfix"}).find(attrs={"class": "number"}).text)
    except Exception:
        score = -1
    return details, score


def getComments(poiId):
    comments = []
    for page in range(100):
        url = "https://place.qyer.com/poi.php?action=comment&page={}&poiid={}".format(page, poiId)
        response = session.get(url)
        commentsJson = response.json()
        if len(commentsJson['data']['lists']) == 0:
            return comments
        for comment in commentsJson['data']['lists']:
            row = {'date': comment['date'], 'starlevel': comment['starlevel'], 'content': comment['content']}
            comments += [row]
    return comments


def getPictures(poiId, rootPath):
    if not os.path.exists(rootPath):
        os.makedirs(rootPath)
    url = 'https://place.qyer.com/images.php?action=list&id={}&type=poi&offset=0&limit=40'.format(poiId)
    response = session.get(url)
    try:
        picsList = response.json()['data']['list']
    except Exception:
        return []
    for pic in picsList:
        picUrl = pic['url']
        try:
            picData = session.get(picUrl)
            with open('{}/{}.jpg'.format(rootPath, pic['id']), 'wb') as f:
                f.write(picData.content)
        except Exception:
            continue
    return picsList


def run():
    rows = []
    for page in range(100):
        sites = getSiteListInfo(page)
        if 'data' not in sites.keys():
            break
        for site in sites['data']:
            try:
                sid = site['id']
                detail = getDetail(sid)
                poiUrl = 'https:' + detail['data']['poi_url']
                siteHtml = getHtml(poiUrl)
                detail, score = getSiteDetailScore(siteHtml)
                comments = getComments(sid)
                picture_path = 'data-guangzhou-0716/pics/{}-{}'.format(site['cn_name'], sid)
                pictures = getPictures(sid, picture_path)
                row = {"id": sid, "name": site['cn_name'], "score": score,
                       "average_hours": float(site['average_hours'].replace("小时", "")),
                       "position": {"lat": site["lat"], "lng": site["lng"]}, "detail": detail,
                       'picture_path': picture_path, 'comments': comments}
                print(poiUrl)
                print(row)
                rows += [row]
            except Exception:
                print(poiUrl)
                print('{} error....'.format(site['cn_name']))
                continue
    with open('data-guangzhou-0716/guangzhou-sites-0716.json', 'w', encoding='utf-8') as file:
        json.dump(rows, file, ensure_ascii=False)


if __name__ == '__main__':
    city = "guangzhou"
    run()
