from default.basic_tor import osint_tor_default
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta

class osint_cactus(osint_tor_default):
    def __init__(self, url):
        super().__init__(url)
        self.totalResults = {}
        self.baseUrl = url

    def request_default_url(self):
        try:
            response = self.session.get(self.url, verify=False)
            self.response = response
        except Exception as e:
            print(f"Error at request_default_url: {e}")
            exit(1)

    def using_bs4(self):
        html = self.response.text
        bsobj = BeautifulSoup(html, 'html.parser')

        for h2 in bsobj.find_all('h2', class_='text-[16px] font-bold leading-6 text-white'):
            parts = re.split(r'\\', h2.text)
            if len(parts) >= 4:
                title = parts[0].strip()
                country = parts[2].strip()
                dataSize = parts[3].strip()
            else:
                continue

            # h2와 연결된 <a> 태그의 href 추출
            parent_a = h2.find_parent('a')
            if not parent_a:
                continue
            href = parent_a['href']
            fullUrl = urljoin(self.baseUrl, href)
            print(f"Processing URL: {fullUrl}")

            # 세부 정보 가져오기
            details = self.details(fullUrl)
            if details[0] is None:
                continue

            formattedDate, dataDescription, address, tel, site, images, comDescription = details

            # 3개월 이상 지난 데이터가 나오면 중단
            date_obj = datetime.strptime(formattedDate, "%Y.%m.%d")
            three_months_ago = datetime.now() - timedelta(days=45)
            if date_obj < three_months_ago:
                print(f"Stopping at old data: {formattedDate}")
                return False  # 중단 신호 반환

            allData = f'size({dataSize}) {dataDescription}'

            # 결과 딕셔너리에 저장
            self.totalResults[title] = {
                'title': title,
                'Description': comDescription,
                'site': site,
                'address': address,
                'country': country,
                'tel': tel,
                'images': images,
                'times': formattedDate,
                'all data': allData
            }

        return True  # 계속 진행 신호 반환

    def details(self, url):
        self.make_tor_session()
        response = self.session.get(url, verify=False)
        new_html = response.text
        newSoup = BeautifulSoup(new_html, 'html.parser')

        # 날짜 추출 및 포맷 변경
        formattedDate = None
        dataDescription = None

        update_element = newSoup.find('mark', class_='marker-yellow')
        if update_element and update_element.find('strong'):
            update_date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', update_element.text)
            if update_date_match:
                date_str = update_date_match.group(1)
                day, month, year = date_str.split('.')
                formattedDate = f"{year}.{month}.{day}"

        # DATA DESCRIPTIONS 추출
        dataDescriptionElement = newSoup.find('mark', string='DATA DESCRIPTIONS:')
        if dataDescriptionElement:
            dataDescription = dataDescriptionElement.find_parent('p').text.split('DATA DESCRIPTIONS:')[-1].strip()

        # Address 추출
        address = None
        addressElement = newSoup.find(string=re.compile(r'Address:'))
        if addressElement:
            address_match = re.search(r'Address:\s*(.*)', addressElement)
            if address_match:
                address = address_match.group(1).strip()

        # Phone Number 추출
        tel = None
        telElement = newSoup.find(string=re.compile(r'Phone Number:'))
        if telElement:
            tel_match = re.search(r'Phone Number:\s*(.*)', telElement)
            if tel_match:
                tel = tel_match.group(1).strip()

        # Website URL 추출
        websiteElement = newSoup.find('a', href=True, string=re.compile(r'https://'))
        site = websiteElement['href'] if websiteElement else None

        # 이미지 추출 (urljoin 사용)
        imageElements = newSoup.find_all('img')
        images = [urljoin(self.baseUrl, img['src']) for img in imageElements if 'src' in img.attrs]

        # Company Description 추출
        markerElement = newSoup.find('mark', class_='marker-yellow')
        comDescription = None
        if markerElement:
            nextP = markerElement.find_next('p')
            if nextP:
                comDescription = nextP.text.strip()

        return formattedDate, dataDescription, address, tel, site, images, comDescription

    def process(self):
        super().process()
        page = 1
        while True:
            self.url = self.baseUrl + f'?page={page}'
            self.request_default_url()
            should_continue = self.using_bs4()
            if not should_continue:
                break
            page += 1

        return self.totalResults