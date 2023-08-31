import hashlib
import os
import threading

import botocore
import scrapy
from fake_useragent import UserAgent
import boto3

ua = UserAgent()

class IOpenMallSpider(scrapy.Spider):
    name = "iopenmall" # modify
    allowed_domains = ["mall.iopenmall.tw/iopen/"] # modify
    start_urls = ["https://mall.iopenmall.tw/iopen/"] # modify
    user_agent = ua.random
    runner = None
    category_links = []

    def __init__(self, runner=None, **kwargs):
        self.runner = runner
        super(IOpenMallSpider , self).__init__(**kwargs) # modify
        
    #modify all parse 
    def parse(self, response, **kwargs):
        try:
            print("Starting to parse") 
            first_menus = response.css('.top_menu_list') 
            for fir_menu in first_menus:
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
                        
                        if link.find("https") != -1 and link.find("store_product_sort") != -1:
                            try:
                                self.category_links.append({'tier1':fir_menu_text, # add on 08/30
                                                           'tier2':sub_menus_text, # add on 08/30
                                                           'tier3':text, # add on 08/30
                                                           'link': link})

                            except Exception as e:
                                print(f'SeleniumRequest: error > {e}, link: {sub_menu_link.get()}')
                                
            self.runner.category_links = self.category_links

            # self.send_category_links_to_sqs(self.category_links)
        except Exception as e:
            print()
            print(str(e))