from default.basic_tor import *
from .zoom import *
from .medianblur import *
from .openclose import *
from .invertimage import *

class osint_medusa(osint_tor_render_js):
    def __init__(self, url=None):
        super().__init__(url)
        self.progress = True

    def re_captcha(self):
        self.go_page()
        try:
            self.page.eval_on_selector("#captcha-reload", "element => element.style.display = 'none'")
            captcha_div = self.page.locator("div.captcha-image-wrapper")
            captcha_div.screenshot(path="/app/images/tmp.png")
            median()
            zoom()
            temp()
            captcha_text = image()
            return captcha_text
        
        except Exception as e:
            print(e)
            return ""

    def using_bs4(self):
        html = self.page.content()
        bsobj = BeautifulSoup(html, 'html.parser')
        companies = bsobj.find_all("div", class_="card")

        for company in companies:
            try:
                title = company.find("h3", class_="card-title").get_text(strip=True)
                description = company.find("div", class_="card-body").find("p").get_text(strip=True)
                price_tag = company.find("div", class_="product__price-tag price-tag-warning")
                price = price_tag.find("p", class_="product__price-tag-price").get_text(strip=True) if price_tag else "N/A"
                countdown = company.find("ul", id="counter-list")
                if countdown:
                    time_elements = countdown.find_all("span")
                    time_units = ["D", "H", "M", "S"]
                    timer = " ".join(f"{elem.get_text(strip=True)}{unit}" for elem, unit in zip(time_elements, time_units))
                else:
                    timer = "N/A"
                updated_tag = company.find("div", class_="date-updated")
                update_date = updated_tag.find("span", class_="text-muted").get_text(strip=True) if updated_tag else "N/A"
                views_tag = company.find("div", class_="number-view")
                views = views_tag.find("span", class_="text-muted").get_text(strip=True) if views_tag else "N/A"

                result = {
                    "title": title,
                    "Description": description,
                    "price": price,
                    "timer": timer,
                    "update_date": update_date,
                    "views": views
                }
                self.result[title] = result
            except Exception as e:
                print(f"Error extracting data: {e}")

    def init_the_browser(self):
        self.init_browser()

    def captcha(self):
        self.go_page()
        try:
            self.page.eval_on_selector("#captcha-reload", "element => element.style.display = 'none'")
            captcha_div = self.page.locator("div.captcha-image-wrapper")
            captcha_div.screenshot(path="/app/images/tmp.png")
            median()
            zoom()
            temp()
            captcha_text = image().replace('\n','').replace(' ','')
            print(len(captcha_text))
            while len(captcha_text)!=7:
                captcha_text = self.re_captcha().replace('\n','').replace(' ','')
                print(captcha_text)
                print(len(captcha_text))
            self.page.fill('input[name="captcha"]', captcha_text)
            self.page.click('button.captcha-card-button')
            self.page.wait_for_load_state('networkidle', timeout=10000)  # 네트워크 요청이 없는 상태로 최대 10초 대기

            # 리다이렉트된 페이지 URL 출력
            redirected_url = self.page.url
            print(f"Redirected to: {redirected_url}")

            # 리다이렉트된 페이지의 내용 확인 (선택)
            self.captcha()
            
        except Exception as e:
            self.using_bs4()

    def process(self):
        while True:
            try:
                self.captcha()
                break
            except Exception as e:
                print(e)
                pass

        return self.result, self.browser, self.page