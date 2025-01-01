from default.basic_tor import osint_tor_render_js
from bs4 import BeautifulSoup
from dns_resolver import resolve_ipv4
import time
import re
from requests import *
import requests

class osint_play(osint_tor_render_js):
    def __init__(self, url):
        super().__init__(url)
        self.base_url = url.rstrip("/")  # URL 마지막 슬래시 제거
        self.progress = True
        self.result = {}
    
    def tor_playwright_crawl(self):
        try:
            self.page.goto(self.url, timeout=60000) 
            self.page.wait_for_timeout(5000)
            html = self.page.content()
            response = Response()
            response._content = html.encode('utf-8') 
            response.status_code = 200 
            response.url = self.url 
            response.headers = {"Content-Type": "text/html; charset=utf-8"} 
            self.response = response
        except Exception as e:
            print(f"Error: {e}")

    def using_bs4(self):
        html = self.response.text
        bsobj = BeautifulSoup(html, 'html.parser')
        object_table = bsobj.find_all("th", class_='News')

        for tr in object_table:
            # 제목
            title = tr.contents[0].strip() if tr.contents[0] else 'none'

            # 위치
            location_element = tr.find('i', class_='location')
            location = location_element.next_sibling.strip() if location_element else 'none'

            # 사이트
            site_element = tr.find('i', class_='link')
            site = site_element.next_sibling.strip() if site_element else 'none'

            # topic ip
            onclick_value = tr['onclick'] if 'onclick' in tr.attrs else 'none'  # onclick 속성이 있는 <th> 태그 찾기
  
            if onclick_value:
                # "viewtopic('<post_id>')"에서 <post_id> 추출
                post_id = onclick_value.split("'")[1]  # 작은 따옴표로 분리하여 post_id 추출
                href = f'/topic.php?id={post_id}'  # 완전한 URL 생성
                full_url = self.base_url + href # 링크 추출
                self.url = full_url
                comment, description = self.details()

            # time
            time_element = tr.find('h')
            time = time_element.text.strip() if time_element else 'none'
            
            result = {
                        "title": title,
                        "address": location,
                        "site": site,
                        "Description": description,
                        "all data": comment,
                        "link": full_url,
                        "times": time
            }
            self.result[title]=result

    def details(self):
        self.tor_playwright_crawl()
        new_html = self.response.text
        new_soup = BeautifulSoup(new_html, 'html.parser')

        comment, description = None, None

        description = None
        for elem in new_soup.find_all(string=re.compile(r'information\s*:?', re.IGNORECASE)):
            if 'information' in elem.lower():
                description = elem.split('information:')[-1].strip()
                break

        # comment 추출 (comment: 뒤의 내용)
        comment = None
        for elem in new_soup.find_all(string=re.compile(r'comment\s*:?', re.IGNORECASE)):
            if 'comment' in elem.lower():
                comment = elem.split('comment:')[-1].strip()
                break

        return comment, description

    def next_page(self):
        for page in range(1):  # 페이지 1~2까지만 크롤링
            self.url = self.base_url + f'/index.php?page={page}'  # URL 업데이트
            time.sleep(1)  # 1초 대기
            self.tor_playwright_crawl()  # Tor 브라우저로 크롤링
            self.using_bs4()  # BeautifulSoup으로 데이터 처리

    def remove_char(self, key):
        for char in ['#', ':', '.']:
            key = key.replace(char, '').lower()
        return key.lower()
    
    def get_region_country(self):
        try:
            for key, values in self.result.items():
                ip = resolve_ipv4(values["site"])
                response = requests.get(f"http://ip-api.com/json/{ip[0]}").json()
                values.update({"country":response["country"]})
                values.update({"region":f"{response['city']}, {response['regionName']}, {response['country']}"})
        except Exception as e:
            print(f"Error at get_region_country : {e}")

    def process(self):
        self.go_page()
        try:
            self.next_page()
        finally:
            self.progress = False  # 종료 조건 설정
            self.get_region_country()
        return self.result, self.browser, self.page
