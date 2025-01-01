from default.basic_tor import osint_tor_render_js
from bs4 import BeautifulSoup
import re
from requests import *
from urllib.parse import urljoin, quote

class osint_raworld(osint_tor_render_js):
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
            response.encoding = 'utf-8' # 인코딩
            self.response = response
        except Exception as e:
            print(f"Error: {e}")
            
    def using_bs4(self):
        html = self.response.text
        bsobj = BeautifulSoup(html, 'html.parser')
        
        portfolio_items = bsobj.find_all("div", class_="portfolio-content")
        
        for item in portfolio_items:
          link = item.find('a')
          time = "N/A"
          if link:
            title = link.text.strip()
            href = link['href'].strip()
            
            combined_url = urljoin(self.base_url, href)
            full_url = quote(combined_url, safe=":/")
            self.url = full_url
          else:
            # a 태그가 없는 경우만 처리 (날짜만 포함된 div)
            time = item.text.strip() 
          try:
            site, content = self.details()
          except Exception as e:
            print(e)
            pass
          
          result = {
            "title": title,
            "link": full_url,
            "times": time,
            "site": site if site else "N/A",
            "all data": content if content else "N/A"
          }
          self.result[title]=result
          
    def details(self):
      self.tor_playwright_crawl()
      new_html = self.response.text
      newSoup = BeautifulSoup(new_html, 'html.parser')
      site, content = None, None
      
      site_elements = newSoup.find_all("div", class_="black-background")
      for site_element in site_elements:
            if site_element.find('a'):
                try:
                    site = site_element.find('a')['href']
                    break
                except Exception as e:
                    pass

      content_element = newSoup.find('h5', text="Content:")
      if content_element:
          next_div = content_element.find_next('div', class_='black-background') 
          if next_div:
              content = ', '.join(sorted([item.strip() for item in next_div.get_text().splitlines() if item.strip()]))
          else:
              content = 'none'
      else:
          content = 'none'
    
      # 유니코드 이스케이프 처리
      if content != 'none':
          content = bytes(content, 'utf-8').decode('unicode-escape')

      return site, content
    
    def remove_char(self, key):
        for char in ['#', ':', '.']:
            key = key.replace(char, '')
        return key.lower()

    def process(self):
        self.go_page()
        try:
            self.tor_playwright_crawl()
            self.using_bs4()
        except Exception as e:
            print(e)
            pass
        return self.result, self.browser, self.page