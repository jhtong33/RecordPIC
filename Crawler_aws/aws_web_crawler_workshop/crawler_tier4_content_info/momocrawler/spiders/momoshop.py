import datetime
import hashlib
import json
import os
from scrapy import Selector
from scrapy_selenium import SeleniumRequest
import scrapy
from fake_useragent import UserAgent
import boto3
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

ua = UserAgent()
region = os.getenv('REGION')
s3 = boto3.client('s3', region_name=region)
queue_tier4_content_links = os.getenv('QUEUE_TIER4_CONTENT_LINKS')
s3_crawler_content_folder = os.getenv('S3_CRAWLER_CONTENT_FOLDER')


def hash_function(original_string):
    # Create a hash object using SHA-256 algorithm
    hasher = hashlib.sha256()

    # Convert the input string to bytes (required by hashlib)
    input_bytes = original_string.encode('utf-8')

    # Update the hash object with the input bytes
    hasher.update(input_bytes)

    # Get the hexadecimal representation of the hash value
    return hasher.hexdigest()


class MomoshopSpider(scrapy.Spider):
    name = "momoshop"
    allowed_domains = ["www.momoshop.com.tw"]
    user_agent = ua.random
    runner = None
    category_links = []
    tier = None

    def __init__(self, runner=None, **kwargs):
        self.runner = runner
        super(MomoshopSpider, self).__init__(**kwargs)

    def start_requests(self):
        # Start the initial request to fetch category links
        # print("Starting start_requests")
        if self.runner.target_url == "":
            tier4_content_link = json.loads(self.runner.tier4_content_object['Body'])['tier4_content_link']
        else:
            tier4_content_link = self.runner.target_url
        # print(f'tier4_content_link:{tier4_content_link}')
        # https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=10670127&str_category_code=1501202193&ctype=B&Area=DgrpCategory&sourcePageType=4
        yield SeleniumRequest(url=tier4_content_link,
                              callback=self.parse,
                              wait_time=15,
                              errback=self.error_handle,
                              wait_until=ec.presence_of_element_located((By.XPATH, "//*"))
                              )

    @staticmethod
    def set_all_tier(response):
        # The original class array => ['Home', '家電', '飲水設備', '\n            ', '本月主打', '元山★開館慶下殺']
        tier_array = "|".join(response.css("#bt_2_layout_NAV ul li ::text").getall()).replace(" ", "").replace("\n", "").replace("||", "|").split("|")
        tier_array.pop(0)
        # print(tier_array)
        return tier_array

    def error_handle(self, error):
        print(error)
        self.runner.timeout = True

    def parse(self, response, **kwargs):
        try:
            # Parse the main category page and extract links to individual product pages
            # print(f"Starting to parse")
            selector = Selector(response)
            driver = response.request.meta['driver']
            content_info_tier = self.set_all_tier(response)

            # 品牌名稱
            item_brand = selector.css("#webBrand ::text").get(None)

            # 市售價
            market_price = None

            # 促銷價
            promotional_price = None

            # 品牌名稱
            discounted_price = None

            # 價格列表
            price_list = selector.css(".prdPrice li")

            for price in price_list:
                if price.css("li ::text").get() == '市售價':
                    market_price = int(price.css("li .seoPrice ::text").get().replace(',', ''))
                if price.css("li ::text").get() == '促銷價':
                    promotional_price = int(price.css("li .seoPrice ::text").get().replace(',', ''))
                if price.css("li ::text").get() == '折扣後價格':
                    discounted_price = int(price.css("li .seoPrice ::text").get().replace(',', ''))

            # <span id="osmGoodsName"> <a class="productName" href="/search/searchShop.jsp?keyword=%E6%9E%97%E5%85%A7&amp;brand=%E6%9E%97%E5%85%A7&amp;brandNo=20160808160045893">林內</a> 台爐式內焰二口爐輕量爐架(RTS-N201S原廠安裝)</span>
            # 商品名稱
            item_name = "".join(selector.css("#osmGoodsName ::text").extract()).strip()
            # print(item_name)

            # 活動
            activity = "".join(selector.css(".ineventArea li ::text").extract()).replace(' ', '').replace('\n', '')

            # 商品規格
            item_spec = {}
            for item_spec_attribute in selector.css("#attributesTable tr"):
                item_spec[item_spec_attribute.css("th ::text").get()] = str(item_spec_attribute.css("td ::text").get()).replace(' ', '')

            # 相關類別
            related_category_list = []
            for related_category_elements in selector.css(".related_category dl"):
                if related_category_elements.css("dl::attr(class)").get() != "brandTxt":
                    related_category_list.append("|".join(related_category_elements.css("dd ::text").getall()).replace("\\\\", "\\"))

            # 商品評價
            goods_commend = {
                "count": int(selector.css('.goodsCommendLi span::attr(goodscount)').get("0").replace(",", "")),
                "indicator_average_value": None,
                "goods_commend_info": None,
                "indicator_accurate": None,
                "indicator_shipping": None,
                "indicator_quality": None}

            # Fetch all commends info
            # 商品評論統計
            goods_commend_info = []

            # 評論內容
            review_card_list = []

            # If there's any goods commend then fetch all of them
            if goods_commend["count"] > 0:
                # Send the javascript to click
                js_code = f"document.querySelector('.goodsCommendLi').click();"  # Click the page number
                driver.execute_script(js_code)

                # Wait for the new content to load after the click
                # Adjust the timeout as needed
                wait = WebDriverWait(driver, 15)
                # Wait for goods comment is ready for click
                wait.until(ec.presence_of_element_located((By.XPATH, "//*")))

                # Get the updated page source and extract product links
                updated_content = driver.page_source
                selector = Selector(scrapy.http.HtmlResponse(url=driver.current_url,
                                                             body=updated_content,
                                                             encoding='utf-8'))

                goods_commend_selected = selector.css('.goodsCommendLi.selected').get()
                if goods_commend_selected is not None:

                    goods_commend["indicator_average_value"] = float(selector.css('.indicatorAvgVal::text').get())

                    for indicator in selector.css(".indicator"):
                        if indicator.css(".indicatorTitle::text").get() == "商品品質":
                            goods_commend["indicator_quality"] = float(selector.css('.indicatorNumber::text').get(None))
                        if indicator.css(".indicatorTitle::text").get() == "商品符合":
                            goods_commend["indicator_accurate"] = float(selector.css('.indicatorNumber::text').get(None))
                        if indicator.css(".indicatorTitle::text").get() == "出貨速度":
                            goods_commend["indicator_shipping"] = float(selector.css('.indicatorNumber::text').get(None))

                    for goods_commend_info_attribute in selector.css(".SelectorOption"):
                        goods_commend_info.append("".join(goods_commend_info_attribute.css("::text").getall()))
                    goods_commend["goods_commend_info"] = goods_commend_info

                    # Fetch the all comments in the first page
                    self.fetch_goods_commend(selector, review_card_list)

                    total_pages = int(selector.css('.pageArea dl dt span:not(.totalTxt)::text').getall()[-1].replace("/", ""))
                    if total_pages > 1:  # Has next page
                        # To get the page index attribute
                        page_attrib = next(iter(selector.css('.pageArea li').attrib))

                        for i in range(2, total_pages+1):
                            js_code = f"document.querySelector('.pageArea li[{page_attrib}=\"{i}\"]').click();"  # Click the page number
                            driver.execute_script(js_code)

                            # Get the updated page source and extract product links
                            updated_content = driver.page_source
                            updated_selector = Selector(scrapy.http.HtmlResponse(url=driver.current_url,
                                                                                 body=updated_content,
                                                                                 encoding='utf-8'))
                            # print(f'page:{i}')
                            self.fetch_goods_commend(updated_selector, review_card_list)

            goods_commend["review_card_list"] = review_card_list

            content_info = {'item_brand': item_brand,
                            'item_name': item_name,
                            'market_price': market_price,
                            'promotional_price': promotional_price,
                            'discounted_price': discounted_price,
                            'activity': activity,
                            'data_date': datetime.datetime.now().strftime("%Y%m%d"),
                            'item_url': response.url,
                            'item_spec': item_spec,
                            'related_category_list': related_category_list,
                            'goods_commend_indicator_average_value': goods_commend["indicator_average_value"],
                            'goods_commend_goods_commend_info': goods_commend["goods_commend_info"],
                            'goods_commend_indicator_quality': goods_commend["indicator_quality"],
                            'goods_commend_indicator_accurate': goods_commend["indicator_accurate"],
                            'goods_commend_indicator_shipping': goods_commend["indicator_shipping"],
                            'goods_commend_review_card_list': goods_commend["review_card_list"]
                            }

            # Configure tiers
            for i in range(0, len(content_info_tier)):
                content_info[f'tier{i + 1}'] = content_info_tier[i]

            # Send the result json to s3
            hash_id = hash_function(response.url)
            self.send_to_s3(content_info, hash_id)

        except Exception as e:
            print(str(e))

    @staticmethod
    def fetch_goods_commend(selector: Selector, review_card_list):
        for review_card in selector.css('.reviewCard'):
            review_card_score = review_card.css(".RatingStarGroup::attr(score)").get()
            review_card_spec = "".join(review_card.css(".SpecValue ::text").getall())
            review_card_date = review_card.css(".Info ::text").get()
            review_card_comment = review_card.css(".CommentContainer ::text").get()
            review_card_list.append({
                'review_card_score': review_card_score,
                'review_card_spec': review_card_spec,
                'review_card_date': review_card_date,
                'review_card_comment': review_card_comment
            })

    @staticmethod
    def send_to_s3(message, hash_id):
        # Send the message to S3
        try:
            json_file_name = f'{hash_id}.json'

            # Construct the S3 key including the folder name
            # ex: content/家電
            s3_key = f'content/{message["tier1"]}/{json_file_name}'

            response = s3.put_object(Bucket=s3_crawler_content_folder, Key=s3_key,
                                     Body=json.dumps(message, ensure_ascii=False))
            # check if it's successful
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('send_to_s3 fail')
        except Exception as e:
            print('send_to_s3 Exception')
            print(str(e))
