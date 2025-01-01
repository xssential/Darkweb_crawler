from default.basic_tor import osint_tor_render_js
from bs4 import BeautifulSoup
from tldextract import extract
from dns_resolver import resolve_ipv4
import requests
import time
import re

class osint_blackbasta(osint_tor_render_js):
    def __init__(self, url):
        super().__init__(url)
        self.progress=True

    def using_bs4(self):
        html = self.response.text
        bsobj = BeautifulSoup(html,'html.parser')
        object_table = bsobj.find_all("div",class_="card")
        for card in object_table:
            title_link = card.find("div",class_="title")
            title = title_link.find('a',class_="blog_name_link").string
            link = title_link.find('a',class_="blog_name_link").get("href")
            data_v_md_lines = card.find_all('p',attrs={"data-v-md-line":True})
            self.progress=card.find("div",class_="progress-title")
            if self.progress==None:
                break
            result = {}
            for p in data_v_md_lines:
                key = "N/A"
                value = "N/A"
                strong = p.find('strong')
                if strong:
                    key = self.remove_char(strong.text)
                strong_tags = p.find_all('strong')
                try:
                    tmp = p["data-v-md-line"]
                    if tmp=="3":
                        key = f"Description"
                        value = p.text
                    else:
                        for strong_tag in strong_tags:
                            strong_tag.decompose()  
                        value = p.text.replace('\n','')
                except Exception as e:
                    pass
                img = p.find_all('img')
                img_links = [self.url+x.get('src') for x in img]
                if "all data size" in key:
                    pattern = r"all data size\s*(.*)" 
                    match = re.search(pattern, key) 
                    if match: 
                        remaining_string = match.group(1)
                        value = f"size({remaining_string})" + value
                    else:
                        value = "size(N/A)" + value
                    key = "all data"
                result.update({key:value})
                result.update({"images":img_links})
                result.pop("N/A",None)
            result.update({"title":title})
            result.update({"link":link})
            self.result.update({result["title"]:result})

    def next_page(self):
        while self.progress!=None:
            time.sleep(1)
            self.tor_playwright_crawl()
            self.using_bs4()
            try:
                next_button = self.page.locator("div.next-page-btn")
                if not next_button or not next_button.is_visible() or next_button.is_disabled():
                    break  
                next_button.click()
                self.page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Error while navigating pages: {e}")
                break

    def remove_char(self,key):
        if '#' in key:
            key=key.replace('#','').lower()
        if ':' in key:
            key=key.replace(':','').lower()
        if '.' in key:
            key=key.replace('.','').lower()
        if key:
            return key.lower()
        else:
            return key
    
    def get_region_country(self):
        try:
            for key, values in self.result.items():
                ip = resolve_ipv4(key)
                response = requests.get(f"http://ip-api.com/json/{ip[0]}").json()
                values.update({"country":response["country"]})
                values.update({"region":f"{response['city']}, {response['regionName']}, {response['country']}"})
        except Exception as e:
            print(f"Error at parse_domain : {e}")

    def process(self):
        self.go_page()
        self.next_page()
        self.get_region_country()
        return self.result, self.browser, self.page
