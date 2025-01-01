import cloudscraper
from playwright.sync_api import sync_playwright
from requests_tor import RequestsTor
from requests.models import Response
from tldextract import extract
from bs4 import BeautifulSoup
import time

class osint_tor_default:
    def __init__(self,url):
        self.session=None
        self.is_cloudflare=None
        self.scraper=None
        self.tor_ip=None
        self.domain=None
        self.response=None
        self.suffix = None
        self.nameserver=[]
        self.url = url

    def make_tor_session(self):
        try:
            self.session = RequestsTor(tor_ports=(9050,),tor_cport=9051)
        except Exception as e:
            print(f"Error at make_tor_session : {e}")
            exit(1)

    def make_cloudflare_scraper(self):
        try:
            self.scraper = cloudscraper.create_scraper(sess=self.session)
        except Exception as e:
            print(f"Error at make_cloudflare_scraper : {e}")
            exit(1)

    def check_dns_nameserver(self):
        if self.suffix != 'onion':
            api_url = f"https://cloudflare-dns.com/dns-query?name={self.domain}&type=NS"
            headers = {"Accept": "application/dns-json"}
            try:
                response = self.session.get(api_url,headers=headers)
                answers = response.json()["Answer"]
                for answer in answers:
                    self.nameserver.append(answer["data"])
                if len(self.nameserver)!=0:
                    self.is_cloudflare=True
                if self.is_cloudflare:
                    self.make_cloudflare_scraper()
            except Exception as e:
                print(f"Error at check_dns_nameserver: {e}")
                exit(1)
        else:
            pass

    def check_tor_ip(self):
        url = "https://httpbin.org/ip"
        try:
            response = self.session.get(url)
            self.tor_ip=response.json()['origin']
        except Exception as e:
            print(f"Error at check_tor_ip : {e}")
            exit(1)

    def parse_domain(self):
        try:
            extracted = extract(self.url)
            self.domain = extracted.domain+"."+extracted.suffix
            self.suffix = extracted.suffix
        except Exception as e:
            print(f"Error at parse_domain : {e}")
            exit(1)

    def request_default_url(self):
        try:
            if self.is_cloudflare:
                response = self.scraper.get(self.url)
            else:
                response = self.session.get(self.url)
            self.response = response
        except Exception as e:
            print(f"Error at request_default_url : {e}")
            exit(1)

    def using_bs4(self):
        #example code
        html = self.response.text
        bsobj = BeautifulSoup(html,'html.parser')
        table_titles = bsobj.find_all("span",class_="subject_new")
        for table_title in table_titles:
            link = table_title.find("a").get('href')
            title = table_title.find("span").string
            print(f"link : {link}")
            print(f"title : {title}")
    
    def process(self):
        self.make_tor_session()
        self.check_tor_ip()
        self.parse_domain()
        self.check_dns_nameserver()
        self.request_default_url() 
        self.using_bs4()
        
class osint_tor_render_js:
    def __init__(self,url=None):
        self.url=url
        self.response = None
        self.result = {}
        self.browser=None
        self.page=None

    def init_browser(self):
        self.browser = sync_playwright().start().firefox.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:9050"}
        )
        self.page = self.browser.new_page()

    def go_page(self):
        self.page.goto(self.url, timeout=180000) 
        self.page.wait_for_timeout(6000)

    def close_browser(self):
        if self.browser:
            self.browser.close()
            time.sleep(10)

    def tor_playwright_crawl(self):
        try:
            html = self.page.content()
            response = Response()
            response._content = html.encode('utf-8') 
            response.status_code = 200 
            response.url = self.url 
            response.headers = {"Content-Type": "text/html; charset=utf-8"} 
            self.response = response
        except Exception as e:
            print(f"Error: {e}")

    def parse_domain(self):
        try:
            extracted = extract(self.url)
            return extracted.domain+"."+extracted.suffix
        except Exception as e:
            print(f"Error at parse_domain : {e}")
            exit(1)
        return None

    def process(self):
        self.tor_playwright_crawl()

                