import os

# LOG_LEVEL = 'INFO'  # to only display errors
# # LOG_LEVEL = 'ERROR'  # to only display errors
# LOG_FORMAT = '%(levelname)s: %(message)s'
# # LOG_FILE = '/tmp/scrapy_tier2.log'
# DOWNLOAD_TIMEOUT = 20
# RETRY_TIMES = 6
BOT_NAME = "momocrawler"

SPIDER_MODULES = ["momocrawler.spiders"]
NEWSPIDER_MODULE = "momocrawler.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "momocrawler (+http://www.yourdomain.com)"

# Obey robots.txt rules
# ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 5
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "momocrawler.middlewares.MomocrawlerSpiderMiddleware": 543,
#}

# LOG_LEVEL = 'INFO'

# Enable or disable downloader middlewares
# # See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#     # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
#     'momocrawler.middlewares.MomoUserAgentMiddleware': 500,
#     # 'scrapy_selenium.SeleniumMiddleware': 800
# }


# DOWNLOAD_TIMEOUT = 15
# RETRY_TIMES = 3
# RETRY_ENABLED = True
DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800
}

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = '/usr/local/bin/chromedriver'
SELENIUM_DRIVER_ARGUMENTS = [
    "blink-settings=imagesEnabled=false",
    "--disable-dev-shm-usage",
    "--no-zygote",
    "--remote-debugging-port=9222",
    "--headless",
    "--no-sandbox",
    "--disable-gpu",
    "--single-process",
    "--disable-dev-tools",
    "--disable-extensions",  # Disable extensions to use extensionLoadTimeout
    "--disable-extensions-except="  # Add an empty extension list
    "--load-extension=/path/to/your/extension",  # If you want to load a specific extension
    "--extensionLoadTimeout=120000",  # Add the experimental option
    "--pageLoadStrategy=eager"
]
SELENIUM_BROWSER_EXECUTABLE_PATH = os.getenv("CHROME_BROWSER_PATH")
# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "momocrawler.pipelines.MomocrawlerPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = False
# # The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# # The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 7
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
