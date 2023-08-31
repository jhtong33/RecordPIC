import hashlib
import os
import threading

import botocore
import scrapy
from fake_useragent import UserAgent
import boto3

ua = UserAgent()
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=50))
queue_tier2_links = os.getenv('QUEUE_TIER2_LINKS')


class IOpenmallSpider(scrapy.Spider):
    name = "iopenmall"
    allowed_domains = ["mall.iopenmall.tw/iopen/"]
    start_urls = ["https://mall.iopenmall.tw/iopen/"]
    user_agent = ua.random
    runner = None
    category_links = []

    def __init__(self, runner=None, **kwargs):
        self.runner = runner
        super(IOpenmallSpider, self).__init__(**kwargs)

    def parse(self, response, **kwargs):
        try:
            print("Starting to parse")
            first_menus = response.css('.top_menu_list')
            for fir_menu in first_menus[0:1]:
                fir_menu_text = fir_menu.css('a::text').get()
                sub_menus = fir_menu.css("ul > li.top_menu_sec_sort > div:nth-child(n)")
                for sub_menu in sub_menus:
                    sub_menus_text = sub_menu.css("a::text").get()
                    sub_menus_link = sub_menu.css("a::attr(href)").get()
                    sub_menus_link = f"https://mall.iopenmall.tw{sub_menus_link.rsplit('..')[1]}"
                    # print(sub_menus_text, sub_menus_link)
                    tir_menus = sub_menu.css(".top_menu_thi")
                    tir_menu_texts = tir_menus.css("a::text").getall()
                    tir_menu_links = tir_menus.css("a::attr(href)").getall()           

                    for text, link in zip(tir_menu_texts, tir_menu_links):
                        link = f"https://mall.iopenmall.tw{link.rsplit('..')[1]}"
                        print(text, link)
                        
                        if link.find("https") != -1 and link.find("store_product_sort") != -1:
                            try:
                                self.category_links.append(link)

                            except Exception as e:
                                print(f'SeleniumRequest: error > {e}, link: {sub_menu_link.get()}')
            self.runner.category_links = self.category_links
            # self.send_category_links_to_sqs(self.category_links)
        except Exception as e:
            print()
            print(str(e))

    @staticmethod
    def send_to_sqs(message):
        response = sqs.send_message(QueueUrl=queue_tier2_links, MessageGroupId=message['MessageGroupId'],
                                    MessageBody=message['MessageBody'], MessageDeduplicationId=message['MessageGroupId'])
        # check if it's successful
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            print('Fail')

    def send_category_links_to_sqs(self, links):
        try:
            print("Starting to send to SQS")
            threads = []
            for link in links:
                hash_id = hash_function(link)
                message = {'Id': hash_id, 'MessageGroupId': hash_id,
                           'MessageBody': link}
                thread = threading.Thread(target=self.send_to_sqs, args=(message,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # if messages:  # Check if there are any remaining messages in the list
            #     self.send_to_sqs(messages)
        except Exception as e:
            print(str(e))


def hash_function(original_string):
    # Create a hash object using SHA-256 algorithm
    hasher = hashlib.sha256()

    # Convert the input string to bytes (required by hashlib)
    input_bytes = original_string.encode('utf-8')

    # Update the hash object with the input bytes
    hasher.update(input_bytes)

    # Get the hexadecimal representation of the hash value
    return hasher.hexdigest()