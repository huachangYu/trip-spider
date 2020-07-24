import json
import requests
from bs4 import BeautifulSoup
import os
import warnings

warnings.filterwarnings('ignore')


def getCookies():
    cookies = {}
    cookieStr = "_qyeruid=CgIBAV8P6iVll31sHTl5Ag==; new_uv=1; new_session=1; _guid=R0ec0509-4342-b682-3947-030ff21e5128; __utma=253397513.195052505.1594878502.1594878502.1594878502.1; __utmc=253397513; __utmz=253397513.1594878502.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmt=1; ql_guid=QLdaa645-7814-4922-bcf0-4379d2fbe43b; ql_created_session=1; ql_stt=1594878502495; ql_vts=1; PHPSESSID=d43cc4f8d9bcf3493c85768160e2d120; plan_token=43c5028ed2dfc6640bebd784d597fc2c; source_url=https%3A//www.google.com/; plan_code=V2YJYFFnBz9TYlI9Cm8NOQ; ql_seq=3; __utmb=253397513.6.9.1594878517682"
    for line in cookieStr.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    return cookies


session = requests.session()
requests.utils.add_dict_to_cookiejar(session.cookies, getCookies())


def getSiteListInfo(page):
    response = session.get(
        'https://plan.qyer.com/api/v3/recommend/getpoilist?city_id=11593&range=1&page=' + str(page) + '&type=0')
    return response.json()


def getDetail(poiId):
    response = session.get('https://plan.qyer.com/api/v3/poi/getpoidetail?plan_id=23196237&poi_id=' + str(poiId))
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
                picture_path = 'data-beijing-0716/pics/{}-{}'.format(site['cn_name'], sid)
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
    with open('data-beijing-0716/beijing-sites-0716.json', 'w', encoding='utf-8') as file:
        json.dump(rows, file, ensure_ascii=False)


if __name__ == '__main__':
    city = "beijing"
    run()
