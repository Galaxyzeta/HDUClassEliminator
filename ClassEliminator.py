from selenium import webdriver
from selenium.webdriver.support.ui import Select
import time
import requests
import base64
import json
from PIL import Image

# Customization
js = json.load(open("config.json",mode="r",encoding="utf-8"))
print(js)
username = js["username"]
password = js["password"]
mode = 0    # mode = 0 ==> 通识选修课
            # mode = 1 ==> 专业选修课
course = js["course"]     # mode = 0 only
apiKey = js["apiKey"]
secretKey = js["secretKey"]
availableTime = js["availableTime"]
teacherName = js["teacherName"]
refresh_rate = js["refresh_rate"]

# Constant
mode1url = "http://jxgl.hdu.edu.cn/xsxjs.aspx?xkkh=CFFC1F35318E7623A1A76FC0EB9D301F04F2C37BC752A6DA17F29A452882A1348D2B62A607D45768&xh="+username
loginUrl = "http://cas.hdu.edu.cn/cas/login?service=http://jxgl.hdu.edu.cn/default.aspx"
table  =  []
threshold = 80
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

def fakeHeader():
    headers = {
        "cookie": None,
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
    }
    return headers


def eliminator():
    # Debug
    # webdriver.Remote._web_element_cls
    # xf_xsqxxxk.aspx?xh=18201125&xm=%u65bd%u660e%u54f2&gnmkdm=N121113

    # Init
    browser = webdriver.Chrome()
    browser.get(loginUrl)

    # Login
    username_elem = browser.find_element_by_css_selector('#un')
    username_elem.send_keys(username)
    password_elem = browser.find_element_by_css_selector('#pd')
    password_elem.send_keys(password)
    click_elem = browser.find_element_by_css_selector('#index_login_btn')
    click_elem.click()
    while not browser.current_url.startswith("http://jxgl.hdu.edu.cn"):
        continue
    
    # Prepare Cookies
    cookiesForRequests = {}
    cookies = browser.get_cookies()
    print(cookies)
    for i in range(len(cookies)):
        cookiesForRequests[cookies[i]['name']] = cookies[i]['value']

    if mode == 0:
        # EnterClassInterface
        main_nav_bar = browser.find_element_by_css_selector('ul.nav>li:nth-child(2)>a')
        main_nav_bar.click()
        sub_nav_bar = browser.find_element_by_css_selector('ul.nav>li:nth-child(2)>ul>li:nth-child(4)>a')
        sub_nav_bar.click()

        # InitElimination
        browser.switch_to.frame("zhuti")
        browser.find_element_by_css_selector("p.search_con>input[name=TextBox1]").send_keys(course) # 课程名
        any_class_left_option:webdriver.Remote._web_element_cls = browser.find_element_by_css_selector('[name=ddl_ywyl]')
        any_class_left_option.click()
        Select(any_class_left_option).select_by_index(0)  # 有 无 课程余量 选择
        Select(browser.find_element_by_css_selector("[name=ddl_kcgs]")).select_by_index(12) # 课程归属 选择 空白

        # StartElimination
        while(True):
            browser.find_element_by_css_selector("p.search_con>input[name=Button2]").click() # 确定
            class_tr = browser.find_elements_by_css_selector("table#kcmcGrid>tbody>tr")
            if len(class_tr)>1:
                # IMPORTANT PART
                # Elimination Available -- Start Elimination !
                for i in range(1, len(class_tr)):
                    class_td = class_tr[i].find_elements_by_css_selector("tr>td")
                    if class_td[5].text in availableTime and class_td[4].text in teacherName:
                        code = getCaptchaCode(cookiesForRequests)
                        class_td[0].find_element_by_css_selector("input").click()       # 选课
                        class_td[1].find_element_by_css_selector("input").click()       # 教材
                        browser.find_element_by_css_selector("span.footbutton input").send_keys(code)
                        browser.find_element_by_css_selector("span.footbutton input[type=submit]").click()
                        print("抢课过程结束，成功与否自行查看")
                        return
                # Elimination Success (if no user mistake...)
                # IMPORTANT PART
            time.sleep(refresh_rate)
    elif mode == 1:
        browser.get(url=mode1url)
        while(True):
            trs = browser.find_elements_by_css_selector("table.formlist>tbody>tr")
            for i in range(1, len(trs)):
                tds = trs[i].find_elements_by_css_selector("tr>td")
                browser.find_element_by_css_selector("table#RadioButtonList1>tbody>tr>td>input").click()
                if int(tds[11].text)>int(tds[14].text) and tds[1].text in teacherName and tds[5].text in availableTime:
                    # IMPORTANT PART
                    # Elimination Available -- Start Elimination !
                    tds[15].find_element_by_css_selector("input").click()
                    code = getCaptchaCode(cookiesForRequests)
                    browser.find_element_by_css_selector("table#RadioButtonList1>tbody>tr>td>input").click()
                    print("1")
                    browser.find_element_by_css_selector("input#txtYz").send_keys(code)
                    print("2")
                    browser.find_element_by_css_selector("input[name=btnSelect]").click()
                    print("抢课过程结束，成功与否自行查看")
                    return
                    # Elimination Success (if no user mistake...)
                    # IMPORTANT PART
            browser.refresh()
            time.sleep(refresh_rate)
    else:
        print("ERROR")

def getAccessToken(apiKey, secretKey):
    url = "https://aip.baidubce.com/oauth/2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": apiKey,
        "client_secret": secretKey
    }
    session = requests.session()
    resp = session.post(url=url, data=data)
    return eval(resp.content.decode("utf-8"))["access_token"]

def getCaptchaCode(cookies):
    resp = requests.get(url = "http://jxgl.hdu.edu.cn/CheckCode.aspx", cookies = cookies)
    fp = open("captcha.gif", mode="wb")
    fp.write(resp.content)
    fp.close()

    im = Image.open("captcha.gif")
    im_conv = Image.new(mode="RGB", size=im.size)
    im_conv.paste(im.crop((0,0,im.size[0], im.size[1])), (0,0,im.size[0], im.size[1]))
    im_conv = im_conv.convert("L")
    im_conv = im_conv.point(lut=table, mode="1")
    im_conv.save("fuck.jpg")

    accessToken = getAccessToken(apiKey, secretKey)
    captchaRecUrl = "https://aip.baidubce.com/rest/2.0/ocr/v1/general?access_token="+accessToken
    
    src = "http://jxgl.hdu.edu.cn/CheckCode.aspx"
    fp = open("fuck.jpg", mode="rb")
    bts = fp.read()
    fp.close()
    header = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "image": base64.b64encode(bts),
        "language_type": "ENG"
    }
    resp = requests.post(url=captchaRecUrl, data=data)
    return eval(resp.content.decode("utf-8"))["words_result"][0]["words"]

if __name__ == "__main__":
    eliminator()