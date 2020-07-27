import asyncio
from pyppeteer import launch
import random
import time
from retrying import retry
from collections import Counter
import json
import re
import os

PROJECT_ROOT = os.getcwd()

async def get_attr_by_url(page):
    """
    :desc cate.txt可以使用parse.py先生存
    :desc: 使用文件保存Json，同时避免重复请求
    :param page: pyppeteer页面对下
    """
    with open(PROJECT_ROOT+'/cate.txt', 'r') as fp:
        for line in fp:
            cat_id = int(line.strip())
            file = PROJECT_ROOT+'/attr/%d.json' % cat_id
            if os.path.exists(file):
                continue
            else:
                url = "https://item.publish.taobao.com/sell/asyncOpt.htm?optType=taobaoCatProp&catId={}".format(str(cat_id))
                await page.goto(url)
                await page.waitFor(1000)
                pg_source = await page.content()
                with open(file, 'w+') as fp_json:
                    dr = re.compile(r'<[^>]+>', re.S)
                    pg_source = dr.sub('', u""+pg_source)
                    fp_json.write(str(pg_source))

async def get_cat_json(page, pid: int):
    """
    :desc: 使用文件逐个保存页面，避免重复请求
    :desc: 使用递归处理页面请求
    :param page: pyppeteer页面对下
    :param pid: 淘宝后台分类的父级ID
    """
    file = PROJECT_ROOT + '/html/%d.json' % pid

    if not os.path.exists(file):
        url = "https://router.publish.taobao.com/router/asyncOpt.htm?optType=categorySelectChildren&catId={}".format(str(pid))
        await page.waitFor(1000)
        await page.goto(url)
        pg_source = await page.content()
        dr = re.compile(r'<[^>]+>', re.S)
        pg_source = dr.sub('', pg_source)
        cat = json.loads(pg_source)
        if cat is not None:
            with open(file, 'w+') as fp:
                json.dump(cat, fp)
    else:
        fp = open(file, 'r')
        cat = json.load(fp)

    if cat is not None:
        if pid == 0:
            for group in cat['data']['dataSource']:
                for item in group['children']:
                    print(item['id'], item['name'])
                    await get_page_by_url(page, int(item['id']))
        else:
            for item in cat['data']['dataSource']:
                print(item['id'], item['name'])
                if not item['leaf']:
                    await get_page_by_url(page, int(item['id']))

async def taobao_login(username, password, url):
    """
    淘宝登录主程序
    :param username: 用户名
    :param password: 密码
    :param url: 登录网址
    :return: 登录cookies
    """
    # 'headless': False如果想要浏览器隐藏更改False为True
    browser = await launch({'headless': False, 'args': ['--no-sandbox']})
    page = await browser.newPage()
    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36')
    await page.goto(url)

    # 以下为插入中间js，将淘宝会为了检测浏览器而调用的js修改其结果
    await page.evaluate(
        '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
    await page.evaluate('''() =>{ window.navigator.chrome = { runtime: {},  }; }''')
    await page.evaluate('''() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }''')
    await page.evaluate('''() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }''')

    await page.click('a.password-login-tab-item')
    page.mouse
    time.sleep(1)
    # 输入用户名，密码
    await page.type('#fm-login-id', username, {'delay': input_time_random() - 50})   # delay是限制输入的时间
    await page.type('#fm-login-password', password, {'delay': input_time_random()})
    time.sleep(1)
    print("")
    await page.keyboard.press('Enter')
    print("print enter")
    await page.click('form div button')
    await page.waitFor(20)
    await page.waitForNavigation()

    try:
        global error  # 检测是否是账号密码错误
        print("error_1:", error)
        error = await page.Jeval('.error', 'node => node.textContent')
        print("error_2:", error)
    except Exception as e:
        error = None
    finally:
        if error:
            print('确保账户安全重新入输入')
            # 程序退出。
            # loop.close()
            await browser.close()
        else:
            print(page.url)

            await page.goto('https://router.publish.taobao.com/router/publish.htm')
            await page.waitFor(2000)
            return await get_cookie(page)

async def get_page_by_url(page):
    """
    :desc 不关闭浏览器对象的条件下根据URL抓取页面
    :param page:
    :return: Null
    """
    await page.waitFor(2000)
    with open('/Users/admin/Desktop/url.txt', 'r') as fp:
        i = 1
        for line in fp:
            url = line.strip()
            await page.goto(url)
            """
            page.on(
                'dialog',
                lambda dialog: asyncio.ensure_future(close_dialog(dialog))
            )
            """
            pg_source = await page.content()
            with open('/Users/admin/Desktop/html/%d.html' % i, 'w') as f:
                f.write(pg_source)
                f.close()
                i += 1
                print(url)

async def get_page_by_click(page):
    """
    :desc 根据发布选择类目树逐步跳转
    :param page:
    :return: Null
    """
    await page.goto('https://router.publish.taobao.com/router/publish.htm')
    await page.waitFor(2000)
    class1es = await page.xpath(
        '//div[@class="cascade-selection category-lists-wrap"]/div[1]//li[@class="group-item"][position()>1]//li')
    print(len(class1es))
    for class1 in class1es:
        title_str = await (await class1.getProperty('title')).jsonValue()
        print(title_str)

        await class1.click()
        time.sleep(1)
        class2es = await page.xpath(
            '//div[@class="cascade-selection category-lists-wrap"]/div[2]//ul[@class="group-wrap"]/li')
        for class2 in class2es:
            await class2.click()

            time.sleep(1)
            btns = await page.xpath('//button[@class="next-btn next-large next-btn-primary ol-next-button block"][not(@disabled)][1]')
            if str(btns) is not '[]':
                await btns[0].click()
                print('2')

            else:
                class3es = await page.xpath('//div[@class="cascade-selection category-lists-wrap"]/div[3]//ul[@class="group-wrap"]/li')
                for class3 in class3es:
                    btns = await page.xpath('//button[@class="next-btn next-large next-btn-primary ol-next-button block"][not(@disabled)][1]')
                    await btns[0].click()
                    print('3')

async def close_dialog(dialog):
    """
    关闭页面中可能存在的dialog
    """
    await dialog.dismiss()

# 获取登录后cookie
async def get_cookie(page):
    # res = await page.content()
    cookies_list = await page.cookies()
    cookies = ''
    for cookie in cookies_list:
        str_cookie = '{0}={1};'
        str_cookie = str_cookie.format(cookie.get('name'), cookie.get('value'))
        cookies += str_cookie
    # print(cookies)
    return cookies


def retry_if_result_none(result):
    return result is None


@retry(retry_on_result=retry_if_result_none)
async def mouse_slide(page=None):
    await asyncio.sleep(2)
    try:
        # 鼠标移动到滑块，按下，滑动到头（然后延时处理），松开按键
        await page.hover('#nc_1_n1z')  # 不同场景的验证码模块能名字不同。
        await page.mouse.down()
        await page.mouse.move(2000, 0, {'delay': random.randint(1000, 2000)})
        await page.mouse.up()
    except Exception as e:
        print(e, ':验证失败')
        return None, page
    else:
        await asyncio.sleep(2)
        # 判断是否通过
        slider_again = await page.Jeval('.nc-lang-cnt', 'node => node.textContent')
        if slider_again != '验证通过':
            return None, page
        else:
            # await page.screenshot({'path': './headless-slide-result.png'}) # 截图测试
            print('验证通过')
            return 1, page


def input_time_random():
    return random.randint(100, 151)


if __name__ == '__main__':
    username = ''
    password = ''
    url = 'https://login.taobao.com/member/login.jhtml?redirectURL=https%3A%2F%2Fwww.taobao.com%2F'
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(taobao_login(username, password, url))
    loop.run_until_complete(task)
    cookie = task.result()
    print(cookie)
    