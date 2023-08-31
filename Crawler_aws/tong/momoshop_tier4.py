import hashlib
import json
import threading
import scrapy
from fake_useragent import UserAgent
from scrapy import Selector
from scrapy.http import HtmlResponse
from scrapy_selenium import SeleniumRequest
import os
import boto3
import botocore
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# Initialize the UserAgent and AWS clients
ua = UserAgent()
region = 'ap-northeast-1'
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=500))
s3 = boto3.client('s3', region_name=region, config=botocore.client.Config(max_pool_connections=500))
queue_tier2_links = 'https://sqs.ap-northeast-1.amazonaws.com/407620147666/aws_crawler_tier2_links.fifo'
queue_tier4_links = 'https://sqs.ap-northeast-1.amazonaws.com/407620147666/aws_crawler_tier4_links.fifo'
s3_bucket_name = 'aws-web-crawler-data/PIC_test'
export_to_s3 = 'Off'


# Function to determine the tier based on the URL
def check_tier_by_url(url: str):
    if url.find("DgrpCategory") != -1:
        return "tier4"
    elif url.find("MgrpCategory") != -1:
        return "tier3"
    elif url.find("LgrpCategory") != -1:
        return "tier2"
    else:
        return None


# Function to calculate SHA-256 hash of a string
def hash_function(original_string):
    # Create a hash object using SHA-256 algorithm
    hasher = hashlib.sha256()

    # Convert the input string to bytes (required by hashlib)
    input_bytes = original_string.encode('utf-8')

    # Update the hash object with the input bytes
    hasher.update(input_bytes)

    # Get the hexadecimal representation of the hash value
    return hasher.hexdigest()


# Spider class for crawling momoshop.com.tw
class MomoshopSpider(scrapy.Spider):
    name = "momoshop"
    allowed_domains = ["www.momoshop.com.tw"]
    user_agent = ua.random
    receipt_handle = ""
    target_url = ""
    runner = None

    def __init__(self, url=None, runner=None, **kwargs):
        self.target_url = url
        self.runner = runner
        super(MomoshopSpider, self).__init__(**kwargs)


    # Function to handle errors during parsing
    def error_handle(self, error):
        print(error)
        print(f'Invalid page:{self.target_url}')
        self.runner.timeout = True

    # Entry point for the spider
    def start_requests(self):
        print("Starting queue_tier2_links from start_requests")
        print(f'self.target_url:{self.target_url}')
        yield SeleniumRequest(url=self.target_url,
                              callback=self.parse_tier2,
                              wait_time=15,
                              errback=self.error_handle,
                              wait_until=ec.any_of(ec.presence_of_element_located((By.CLASS_NAME, 'first')),  # Wait for the tier path loaded
                                                   ec.presence_of_element_located((By.ID, 'backgroundContent')),  # Wait for the landing page loaded
                                                   ec.presence_of_element_located((By.CLASS_NAME, "year18Ban"))))  # Wait for the yes18years paged loaded

    # Function to send a message to SQS
    @staticmethod
    def send_to_sqs(message):
        try:
            # print(message['MessageGroupId'])
            response = sqs.send_message(QueueUrl=queue_tier4_links,
                                        MessageGroupId=message['MessageGroupId'],
                                        MessageBody=message['MessageBody'],
                                        MessageDeduplicationId=message['MessageGroupId'])
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))

    # Function to send data to S3
    @staticmethod
    def send_to_s3(m, hash_id):
        try:
            json_file_name = f'{hash_id}.json'
            response = s3.put_object(Bucket=s3_bucket_name, Key=json_file_name, Body=json.dumps(m, ensure_ascii=False))
            # check if it's successful
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))

    # Function to start pushing data to SQS and S3
    def start_to_push(self, current_tier, hash_id, tier_dict, category_link, message_body):
        if current_tier == "tier4":
            print(f'tier4: {tier_dict.get("tier4", "")}')
            message = {'Id': hash_id, 'MessageGroupId': hash_id,
                       'MessageBody': json.dumps({
                           'tier1_category_name': tier_dict["tier1"],
                           'tier2_category_name': tier_dict.get("tier2", ""),
                           'tier3_category_name': tier_dict.get("tier3", ""),
                           'tier4_category_name': tier_dict.get("tier4", ""),
                           'category_link': category_link if category_link.find(
                               "javascript") == -1 else "",
                           'category_type': current_tier}, ensure_ascii=False)}
            self.send_to_sqs(message)
            # self.runner.category_info.append(message_body)

            if export_to_s3 is not None and export_to_s3 == "On":
                self.send_to_s3(message_body, hash_id)

    # Function to parse the tier 2 categories
    def parse_tier2(self, response: HtmlResponse):
        try:
            print("Starting to parse_tier2")

            # Check yes18years page and click it to go to the next page
            if response.url.find("AgeCheck") != -1:
                driver = response.request.meta['driver']

                js_code = "document.querySelector(\".yes18years\").click();"  # Click to the next page
                driver.execute_script(js_code)

                # Wait for the new content to load after the click
                # Adjust the timeout as needed
                wait = WebDriverWait(driver, 15)
                # # Wait for goods comment is ready for click
                wait.until(ec.presence_of_element_located((By.XPATH, "//*")))

                # Get the updated page source and extract product links
                updated_content = driver.page_source
                response = Selector(scrapy.http.HtmlResponse(url=driver.current_url,
                                                             body=updated_content,
                                                             encoding='utf-8'))

            categories = response.css('#bt_category_Content ul li')
            tier_dict = {}
            threads = []
            if len(categories) > 0:
                tier_path = response.css("#bt_2_layout_NAV ul li")
                tier_index = 1
                for tier in tier_path:
                    if tier.css("::attr(class)").get() != 'first':
                        tier_a = tier.css("a").get()
                        if tier_a is not None:
                            tier_dict[f'tier{tier_index}'] = tier.css("a::text").get()
                        else:
                            tier_dict[f'tier{tier_index}'] = tier.css("::text").get()
                        tier_index = tier_index+1
            if "tier1" in tier_dict:
                for category in categories:
                    # self.parse_process(response, category, tier_dict)
                    thread = threading.Thread(target=self.parse_process, args=(category, tier_dict,))
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
        except Exception as e:
            print(e)
        finally:
            self.runner.timeout = False

    # Function to process individual category items
    def parse_process(self, category, tier_dict):

        category_item_a = category.css('a').get()
        category_link = ""
        if category_item_a is not None:
            category_link = category.css('li a::attr(href)').get()

        current_tier = check_tier_by_url(category_link)

        if current_tier == "tier4":
            tier_dict['tier4'] = category.css("a::text").get()
        elif current_tier == "tier3":
            tier_dict['tier3'] = category.css("a::text").get()

        if tier_dict is not None:
            category_link = "https://www.momoshop.com.tw" + category_link if category_link.find("momoshop.com.tw") == -1 else category_link
            message_body = {'tier1_category_name': tier_dict["tier1"],
                            'tier2_category_name': tier_dict.get("tier2", ""),
                            'tier3_category_name': tier_dict.get("tier3", ""),
                            'tier4_category_name': tier_dict.get("tier4", ""),
                            # https://ecm.momoshop.com.tw/category/DgrpCategory.jsp?d_code=1704300019&p_orderType=6&showType=chessboardType&sourcePageType=4
                            'category_link': category_link.replace("ecm.momoshop.com.tw", "www.momoshop.com.tw"),
                            'category_type': current_tier}

            hash_id = hash_function(str(category_link))
            self.start_to_push(current_tier, hash_id, tier_dict, category_link, message_body)