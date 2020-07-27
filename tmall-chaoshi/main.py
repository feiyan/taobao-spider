#!/usr/bin/python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from pyquery import PyQuery as pq
from time import sleep
import math
import os
import json
import random

class TmallChaoshi:

    def __init__(self):
        url = 'https://login.taobao.com/member/login.jhtml'
        self.url = url

        # 动态代理服务器
        proxyHost = "http-dyn.abuyun.com"
        proxyPort = "9020"

        # 代理隧道验证信息
        proxyUser = "user"
        proxyPass = "pass"

        proxy_auth_plugin_path = self.create_proxy_auth_extension(
        proxy_host=proxyHost,
        proxy_port=proxyPort,
        proxy_username=proxyUser,
        proxy_password=proxyPass)

        """
        驱动浏览器
        无需扫描登录时可以开启不加载图片，加快访问速度。
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_extension(proxy_auth_plugin_path)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False) 

        # 启动Selenimu，10秒超时
        self.browser = webdriver.Chrome(executable_path=chromedriver_path, options=options)
        self.wait = WebDriverWait(self.browser, 10)


    """
     - 注意Tmall和Taobao的登录UI还是有不同的。
    """
    def login(self):
        # 打开网页
        self.browser.get(self.url)

        # 自适应等待，点击密码登录选项
        self.browser.implicitly_wait(30)
        self.browser.find_element_by_xpath('//*[@id="J_Quick2Static"]').click()

        # 自适应等待，输入登录账号
        self.browser.implicitly_wait(30)
        self.browser.find_element_by_name('TPL_username').send_keys(username)

        # 自适应等待，输入登录密码
        self.browser.implicitly_wait(30)
        self.browser.find_element_by_name('TPL_password').send_keys(password)

        # 自适应等待，点击确认登录按钮
        self.browser.implicitly_wait(30)
        self.browser.find_element_by_xpath('//*[@id="J_SubmitStatic"]').click()

        # 直到获取到页面TOP左侧淘宝会员昵称才能确定是登录成功
        taobao_name = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.site-nav-bd > ul.site-nav-bd-l > li#J_SiteNavLogin > div.site-nav-menu-hd > div.site-nav-user > a.site-nav-login-info-nick ')))
        
        # 登录成功，输出淘宝昵称
        print(taobao_name.text)

    # 获取天猫商品总共的页数
    def search_toal_page(self):

        # 等待本页面全部天猫商品数据加载完毕，list-bottom为分页区域选择
        good_total = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.list-bottom')))

        # 获取天猫商品总共页数
        number_total = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.mallCrumbs-count > em'))).text
        return math.ceil(int(number_total)/40)


    # 翻页操作
    def next_page(self, page_number):
        # 等待该页面input输入框加载完毕
        input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.pageSkip-jumpto')))

        # 等待该页面的确定按钮加载完毕
        submit = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.pageSkip-search')))

        # 清除里面的数字
        input.clear()

        # 重新输入数字
        input.send_keys(page_number)

        # 强制延迟N秒，防止被识别成机器人
        sleep(2)

        # 点击确定按钮
        submit.click()


    # 模拟向下滑动浏览
    def swipe_down(self):
        second = random.randint(2, 10)
        for i in range(int(second/0.1)):
            js = "var q=document.documentElement.scrollTop=" + str(300+200*i)
            self.browser.execute_script(js)
            sleep(0.1)
        js = "var q=document.documentElement.scrollTop=100000"
        self.browser.execute_script(js)
        sleep(1)


    # 爬取天猫商品数据
    def crawl_good_data(self, arr):
        # 对天猫商品数据进行爬虫
        self.browser.get(arr['url'])
        err1 = self.browser.find_element_by_xpath("//*[@id='content']/div/div[2]").text
        err1 = err1[:5]
        if(err1 == "喵~没找到"):
            print("找不到您要的")
            return
        try:
            self.browser.find_element_by_xpath("//*[@id='J_ComboRec']/div[1]")
            err2 = self.browser.find_element_by_xpath("//*[@id='J_ComboRec']/div[1]").text
            #print(err2)
            
            err2 = err2[:5]

            if(err2 == "我们还为您"):
                print("您要查询的商品书目太少了")
                return
        except:
            print("可以爬取这些信息")
        
        # 获取天猫商品总共的页数
        page_total = self.search_toal_page()

        # 追加逻辑，Tmall的防抓取对翻页查找监听非常严格，建议Page>=5的单独处理。
        if page_total > 4:
            fp3 = open("/home/user/wait_for_handle.txt", mode='a+', encoding="utf8")
            fp3.write(json.dumps(arr)+"\n")
            fp3.close()
            return
        
        # 打印Log
        print(arr["c1"] + "\t" + arr["c2"] + "\t" + arr["c3"] + "\t" + "总共页数" + str(page_total))

        # 遍历所有页数
        for page in range(2, page_total+2):

            # 等待该页面全部商品数据加载完毕
            good_total = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.list-bottom')))

            # 等待该页面input输入框加载完毕
            input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.pageSkip-jumpto')))

            # 获取当前页
            now_page = input.get_attribute('value')
            # print("当前页数" + now_page + ",总共页数" + str(page_total))

            # 获取本页面源代码
            html = self.browser.page_source

            # pq模块解析网页源代码
            doc = pq(html)

            # 存储天猫商品数据
            good_items = doc('#J_ProductList .product').items()

            # 遍历该页的所有商品
            for item in good_items:
                good_title = item.find('.product-title > a').text().replace('\n',"").replace('\r',"")
                good_sold = item.find('.item-sum > strong').text().replace(" ","").replace('\n',"").replace('\r',"")
                good_price = item.find('.ui-price > strong').text().replace(" ", "").replace('\n', "").replace('\r', "")
                fp2.write(arr["c1"] + "\t" + arr["c2"] + "\t" + arr["c3"] + "\t" + now_page + "\t" + good_title + "\t" + good_sold + "\t" + good_price + "\n")

            # 精髓之处，大部分人被检测为机器人就是因为进一步模拟人工操作
            # 模拟人工向下浏览商品，即进行模拟下滑操作，防止被识别出是机器人
            self.swipe_down()

            # 翻页，下一页
            self.next_page(page)

    """
    阿布云动态代理IP，需付费
    """
    def create_proxy_auth_extension(self, proxy_host, proxy_port, proxy_username, proxy_password, scheme='http', plugin_path=None):
        if plugin_path is None:
            plugin_path = r'/dir/{}_{}@http-dyn.abuyun.com_9020.zip'.format(proxy_username, proxy_password)

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Abuyun Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = string.Template(
            """
            var config = {
                mode: "fixed_servers",
                rules: {
                    singleProxy: {
                        scheme: "${scheme}",
                        host: "${host}",
                        port: parseInt(${port})
                    },
                    bypassList: ["foobar.com"]
                }
              };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "${username}",
                        password: "${password}"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
            );
            """
        ).substitute(
            host=proxy_host,
            port=proxy_port,
            username=proxy_username,
            password=proxy_password,
            scheme=scheme,
        )

        with zipfile.ZipFile(plugin_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        return plugin_path

if __name__ == "__main__":

    chromedriver_path = "/usr/bin/chromedriver"
    username = "username"
    password = "you own password"

    tc = TmallChaoshi()
    tc.login()

    # 最终处理完成的数据文件
    fp2 = open("/home/user/data.txt", mode='a+', encoding="utf8")

    # 打开分类数据文件
    fp = open('/home/user/cates.json', 'r', encoding="utf8")

    # 控制频次，逐行执行
    for line in fp.readlines():
        line = line.replace('\n',"").replace('\r',"")
        arr = json.loads(line)
        tc.crawl_good_data(arr)
    
    fp.close()
    fp2.close()
    print("All Done")
