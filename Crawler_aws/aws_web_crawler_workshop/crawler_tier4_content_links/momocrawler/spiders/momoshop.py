import hashlib
import json
import os
import threading
from scrapy_selenium import SeleniumRequest
import botocore
import scrapy
from fake_useragent import UserAgent
import boto3
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

ua = UserAgent()
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=500))
s3 = boto3.client('s3', region_name=region, config=botocore.client.Config(max_pool_connections=500))
export_to_s3 = os.getenv('EXPORT_TO_S3')
queue_tier4_content_links = os.getenv('QUEUE_TIER4_CONTENT_LINKS')
s3_tier4_content_links = os.getenv('S3_TIER4_CONTENT_LINKS')
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

    def __init__(self, runner=None, **kwargs):
        self.runner = runner
        super(MomoshopSpider, self).__init__(**kwargs)

    def start_requests(self):
        # Start the initial request to fetch category links
        # print("Starting start_requests")
        if self.runner.target_url == "":
            target_url = json.loads(self.runner.tier4_category_object['Body'])['category_link']
        else:
            target_url = self.runner.target_url
        # print(f'target_url:{target_url}')
        yield SeleniumRequest(url=target_url,
                              callback=self.parse,
                              wait_time=20,
                              errback=self.error_handle,
                              wait_until=ec.presence_of_element_located((By.XPATH, "//*")))

    def error_handle(self, failure):
        exception = failure.value
        print(exception)
        if isinstance(exception, UnexpectedAlertPresentException):
            print("Unexpected alert encountered. Handling...")
            # Perform any additional handling you need here
        else:
            self.runner.timeout = True
            print("Other error occurred:", exception)
            # Handle other types of errors here

    def parse(self, response, **kwargs):
        try:
            # Parse the main category page and extract links to individual product pages
            # print(f"Starting to parse")

            driver = response.request.meta['driver']
            threads = []

            tier4_content_links = response.css(".eachGood ::attr(href)").getall()
            if len(tier4_content_links) > 0:
                tier = self.set_all_tier(response)
                self.construct_s3_tier_folder(tier)
                self.start_to_push(tier4_content_links, tier, threads)

                page_element = response.css('.pageArea dl dt span ::text').getall()
                # Some pages have no page count element "頁數1/1"
                if len(page_element) > 0:
                    total_pages = int(response.css('.pageArea dl dt span ::text').getall()[-1].replace("/", ""))

                    # To get the page index attribute
                    page_attrib = ""

                    # response.css('.pageArea a')[1]

                    for key, value in response.css('.pageArea a')[1].attrib.items():
                        try:
                            int(value)
                            page_attrib = key
                        except ValueError:
                            pass

                    if total_pages > 1:
                        for i in range(2, total_pages + 1):
                            # For each page, extract product links
                            # If the number of page is greater than 1 then
                            # For subsequent pages, click on the page number to load new content and extract links
                            js_code = f"document.querySelector('.pageArea a[{page_attrib}=\"{i}\"]').click();"  # Click the page number
                            driver.execute_script(js_code)
                            # print(f'page:{i}')

                            # Wait for the new content to load after the click
                            wait = WebDriverWait(driver, 20)  # Adjust the timeout as needed
                            updated_content_locator = (By.XPATH, "//*")  # Wait for all element loaded
                            wait.until(ec.presence_of_element_located(updated_content_locator))

                            # Get the updated page source and extract product links
                            updated_content = driver.page_source
                            updated_response = scrapy.http.HtmlResponse(url=driver.current_url, body=updated_content,
                                                                        encoding='utf-8')
                            tier4_content_links = updated_response.css(".eachGood ::attr(href)").getall()  # Get all tier4 content urls

                            # Start the threading to push the product links to SQS and/or S3
                            self.start_to_push(tier4_content_links, tier, threads)

            # Wait for all threads to finish before proceeding
            for thread in threads:
                thread.join()
        except Exception as e:
            print(str(e))

    @staticmethod
    def set_all_tier(response):
        # The original class array => ['Home', '家電', '飲水設備', '\n            ', '本月主打', '元山★開館慶下殺']
        tier_array = "|".join(response.css("#bt_2_layout_NAV ul li ::text").getall()).replace(" ", "").replace("\n", "").replace("||", "|").split("|")
        tier_array.pop(0)
        # print(tier_array)
        return tier_array

    @staticmethod
    def construct_s3_tier_folder(tier: []):
        # Construct the base folder path
        base_path = "content"

        # Create the base folder if it doesn't exist
        if base_path:
            s3.put_object(Bucket=s3_crawler_content_folder, Key=f"{base_path}/")

        folder_name = tier[0]
        folder_path = f"{base_path}/{folder_name}"

        # Create the folder if it doesn't exist
        s3.put_object(Bucket=s3_crawler_content_folder, Key=f"{folder_path}/")

        # If you want to set folder with 4 tiers

        # Set the current folder path as the base path for the next iteration
        # base_path = folder_path

        # Construct the folder structure based on the tiers
        # for key, value in tier.items():
        #     folder_name = value.strip('/')
        #     folder_path = f"{base_path}/{folder_name}"
        #
        #     # Create the folder if it doesn't exist
        #     s3.put_object(Bucket=s3_crawler_content_folder, Key=f"{folder_path}/")
        #
        #     # Set the current folder path as the base path for the next iteration
        #     base_path = folder_path

    def start_to_push(self, tier4_content_links, tier, threads):
        # For each product link, create a message and push it to SQS and/or S3
        for tier4_content_link in tier4_content_links:
            tier4_content_link = f'https://www.momoshop.com.tw/{tier4_content_link}'.replace("//", "/")
            hash_id = hash_function(tier4_content_link)
            message = {'Id': hash_id, 'MessageGroupId': hash_id,
                       'MessageBody': json.dumps({'tier4_content_link': tier4_content_link, 'tier': tier}, ensure_ascii=False)}

            thread_sqs = threading.Thread(target=self.send_to_sqs, args=(message,))
            threads.append(thread_sqs)
            thread_sqs.start()

            # self.send_to_sqs(message)

            if export_to_s3 is not None and export_to_s3 == "On":
                message_body = {'hash_id': hash_id, 'page_url': tier4_content_link}
                self.send_to_s3(message_body, hash_id)
                thread_s3 = threading.Thread(target=self.send_to_sqs, args=(message,))
                threads.append(thread_s3)
                thread_s3.start()

    @staticmethod
    def send_to_sqs(message):
        # Send the message to SQS
        try:
            # print(message['MessageGroupId'])

            response = sqs.send_message(QueueUrl=queue_tier4_content_links,
                                        MessageGroupId=message['MessageGroupId'],
                                        MessageBody=message['MessageBody'],
                                        MessageDeduplicationId=message['MessageGroupId'])
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))

    @staticmethod
    def send_to_s3(m, hash_id):
        # Send the message to S3
        try:
            json_file_name = f'{hash_id}.json'
            response = s3.put_object(Bucket=s3_tier4_content_links, Key=json_file_name,
                                     Body=json.dumps(m, ensure_ascii=False))
            # check if it's successful
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))
