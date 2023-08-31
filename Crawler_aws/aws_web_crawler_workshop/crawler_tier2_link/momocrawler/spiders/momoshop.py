import scrapy


class MomoshopSpider(scrapy.Spider):
    name = "momoshop"
    allowed_domains = ["www.momoshop.com.tw"]
    start_urls = ["https://www.momoshop.com.tw/main/Main.jsp"]
    runner = None

    def __init__(self, runner=None, **kwargs):
        self.runner = runner
        super(MomoshopSpider, self).__init__(**kwargs)

    def parse(self, response, **kwargs):
        try:
            print("Starting to parse")
            sub_menus = response.css('.subMenu')
            for sub_menu in sub_menus:
                # Get all tier2 category links
                sub_menu_links = sub_menu.css("#topArea .dul .BTDME a::attr(href)")
                for sub_menu_link in sub_menu_links:
                    link = str(sub_menu_link.get())
                    if link.find("https") != -1 and link.find("category") != -1:
                        try:
                            self.runner.category_links.append(link)
                        except Exception as e:
                            print(f'SeleniumRequest: error > {e}, link: {sub_menu_link.get()}')
            # self.runner.category_links = self.category_links
        except Exception as e:
            print(str(e))
