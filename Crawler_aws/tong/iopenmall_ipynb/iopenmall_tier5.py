import hashlib
import json
import threading
import scrapy
from fake_useragent import UserAgent
from scrapy_selenium import SeleniumRequest
import os
import boto3
import botocore
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

ua = UserAgent()
# region = os.getenv('REGION')
# sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=500))
# s3 = boto3.client('s3', region_name=region, config=botocore.client.Config(max_pool_connections=500))
queue_tier2_links = os.getenv('QUEUE_TIER2_LINKS')
queue_tier4_links = os.getenv('QUEUE_TIER4_LINKS')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')
export_to_s3 = os.getenv('EXPORT_TO_S3')

#modify this function 
def check_tier(tier_dict: dict):
    if "tier5" in tier_dict:
        return "tier5"
    elif "tier4" in tier_dict:
        return "tier4"
    elif "tier3" in tier_dict:
        return "tier3"
    elif "tier2" in tier_dict:
        return "tier2"
    else:
        return "tier1"


def hash_function(original_string):
    # Create a hash object using SHA-256 algorithm
    hasher = hashlib.sha256()

    # Convert the input string to bytes (required by hashlib)
    input_bytes = original_string.encode('utf-8')

    # Update the hash object with the input bytes
    hasher.update(input_bytes)

    # Get the hexadecimal representation of the hash value
    return hasher.hexdigest()


class IOpenMallSpider(scrapy.Spider):
    name = "iopenmall" # modify
    allowed_domains = ["mall.iopenmall.tw/iopen/"] # modify
    start_urls = "https://mall.iopenmall.tw/iopen/" # modify
    user_agent = ua.random
    receipt_handle = ""
    target_url = ""
    runner = None

    def __init__(self, url=None, runner=None, **kwargs):
        self.target_url = url
        self.runner = runner
        self.tier1 = self.runner.tier1 # add 
        self.tier2 = self.runner.tier2 # add 
        self.tier3 = self.runner.tier3 # add 
        super(IOpenMallSpider, self).__init__(**kwargs) # modify

    def error_handle(self, error):
        print(error)
        print(f'Invalid page: {self.target_url}')
        self.runner.timeout = True

    def start_requests(self):
        print("Starting queue_tier3_links from start_requests")
        print(f'self.target_url: {self.target_url}')
        headers = {"Host": urlparse(self.target_url).netloc,
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,zh-CN;q=0.6,ja;q=0.5',
                   'Sec-Fetch-Dest': 'document',
                   'Sec-Fetch-Mode': 'navigate',
                   'Sec-Fetch-Site': 'none',
                   'Upgrade-Insecure-Requests': '1',
                   "Referer": "https://mall.iopenmall.tw/iopen/",
                   "User-Agent": ua.random}
        yield SeleniumRequest(url=self.target_url,
                              headers=headers,
                              callback=self.parse_tier3,
                              wait_time=15,
                              errback=self.error_handle,
                              wait_until=ec.any_of(ec.presence_of_element_located((By.CLASS_NAME, 'first')),
                                                   ec.presence_of_element_located((By.ID, 'backgroundContent'))))

    @staticmethod
    def send_to_sqs(message):
        try:
            print(message['MessageGroupId'])
            response = sqs.send_message(QueueUrl=queue_tier4_links,
                                        MessageGroupId=message['MessageGroupId'],
                                        MessageBody=message['MessageBody'],
                                        MessageDeduplicationId=message['MessageGroupId'])
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))

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

    # modify all function 
    def start_to_push(self, current_tier, hash_id, tier_dict, category_link, message_body):
        if current_tier == "tier4":
            print(f'tier4: {tier_dict.get("tier4", "")}')
            message = {'Id': hash_id, 'MessageGroupId': hash_id,
                       'MessageBody': json.dumps({
                           'tier1_category_name': tier_dict["tier1"],
                           'tier2_category_name': tier_dict.get("tier2", ""),
                           'tier3_category_name': tier_dict.get("tier3", ""),
                           'tier4_category_name': tier_dict.get("tier4", ""),
                           'category_link': category_link if not None else "",
                           'category_type': current_tier}, ensure_ascii=False)}
        elif current_tier == "tier5":
            print(f'tier5: {tier_dict.get("tier5", "")}')
            message = {'Id': hash_id, 'MessageGroupId': hash_id,
                       'MessageBody': json.dumps({
                           'tier1_category_name': tier_dict["tier1"],
                           'tier2_category_name': tier_dict.get("tier2", ""),
                           'tier3_category_name': tier_dict.get("tier3", ""),
                           'tier4_category_name': tier_dict.get("tier4", ""),
                           'tier5_category_name': tier_dict.get("tier5", ""),
                           'category_link': category_link if not None else "",
                           'category_type': current_tier}, ensure_ascii=False)}    
        print(message)
        # thread_sqs = threading.Thread(target=self.send_to_sqs, args=(message,))
        # threads.append(thread_sqs)
        # thread_sqs.start()
        #
        # self.send_to_sqs(message)
        # self.runner.category_info.append(message_body)

        # if export_to_s3 is not None and export_to_s3 == "On":
            # self.send_to_s3(message_body, hash_id)
            # thread_s3 = threading.Thread(target=self.send_to_s3, args=(message_body, hash_id))
            # threads.append(thread_s3)
            # thread_s3.start()
        #
        # for thread in threads:
        #     thread.join()
        
        
    # modify all function 
    def parse_tier3(self, response):
        try:
            print("Starting to parse_tier3")
            first_menu_text = self.tier1
            sec_menu_text = self.tier2
            tri_menu_text = self.tier3
            print(first_menu_text, sec_menu_text, tri_menu_text)
            tri_menu_text = response.css('div.it913-default div span::text').get()
            for_menus = response.css('#mp-pusher div.FOR_MAIN div.clearfix div div.it913-default ul li')
            threads = []


            if len(for_menus) > 0:
                for for_menu in for_menus:
                    for_text = for_menu.css('div a::text').get()
                    for_link = for_menu.css('div a::attr(href)').get()
                    print(for_text, for_link)
                    tier_dict = {}
                    fif_menus = for_menu.css('ul > li')
                    if len(fif_menus) > 0: 
                        for fif_menu in fif_menus:
                            fif_text = fif_menu.css('div a::text').get()
                            fif_link = fif_menu.css('div a::attr(href)').get()
                            
                            link = f"https://mall.iopenmall.tw/iopen/{fif_link}"
                            print(fif_text, link)
                            tier_dict['tier5'] = fif_text
                            tier_dict['tier4'] = for_text     
                            tier_dict['tier3'] = tri_menu_text  
                            tier_dict['tier2'] = sec_menu_text
                            tier_dict['tier1'] = first_menu_text
                            
                            self.parse_process(tier_dict, link)
                            thread = threading.Thread(target=self.parse_process, args=(tier_dict, link))
                            threads.append(thread)
                            thread.start()

                    else:
                        tier_dict['tier4'] = for_text     
                        tier_dict['tier3'] = tri_menu_text  
                        tier_dict['tier2'] = sec_menu_text
                        tier_dict['tier1'] = first_menu_text
                        link = f"https://mall.iopenmall.tw/iopen/{for_link}"
                        
                        self.parse_process(tier_dict, link)
                        # thread = threading.Thread(target=self.parse_process, args=(tier_dict, link))
                        # threads.append(thread)
                        # thread.start()

                for thread in threads:
                    thread.join()
        except Exception as e:
            print(e)
        finally:
            self.runner.timeout = False
            
    # Function to process individual category items
    def parse_process(self, tier_dict, category_link):

        current_tier = check_tier(tier_dict)

        if tier_dict is not None and current_tier == "tier4":
            message_body = {'tier1_category_name': tier_dict.get("tier1", ""),
                            'tier2_category_name': tier_dict.get("tier2", ""),
                            'tier3_category_name': tier_dict.get("tier3", ""),
                            'tier4_category_name': tier_dict.get("tier4", ""),
                            'category_link': category_link,
                            'category_type': current_tier}

        elif tier_dict is not None and current_tier == "tier5":
            message_body = {'tier1_category_name': tier_dict.get("tier1", ""),
                            'tier2_category_name': tier_dict.get("tier2", ""),
                            'tier3_category_name': tier_dict.get("tier3", ""),
                            'tier4_category_name': tier_dict.get("tier4", ""),
                            'tier5_category_name': tier_dict.get("tier5", ""),
                            'category_link': category_link,
                            'category_type': current_tier}

        hash_id = hash_function(str(category_link))
        self.start_to_push(current_tier, hash_id, tier_dict, category_link, message_body)        
