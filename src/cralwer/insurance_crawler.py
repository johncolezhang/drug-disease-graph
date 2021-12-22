import json
import time

import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import fnmatch
import os


def parse_info(browser):
    page_content = browser.page_source
    soup = BeautifulSoup(page_content, 'html.parser')
    current_page = soup.find_all("button", {"class": "current"})[0].text
    drug_list = []
    for sc in soup.find_all("div", {"class": "search-content"}):
        title = sc.find_all("p", {"class": "li-title"})[0].text
        header_list = []
        info_list = []
        for detail in sc.find_all("p", {"class": "li-detail"}):
            header = detail.find("span", {"class": "detail-title"})
            header_list.append(header.text)

            info = detail.find("span", {"class": "detail-content"})
            info_list.append(info.text)

        info_dict = dict(zip(header_list, info_list))

        drug_dict = {"drug_name": title}
        drug_dict.update(info_dict)
        drug_list.append(drug_dict)

    with open("page/drug_{}.json".format(current_page), 'w', encoding="utf-8") as f:
        json.dump(drug_list, f)

    click_name = browser.find_element_by_xpath('//button[text()="下一页"]')
    click_name.click()
    time.sleep(1.5)



def info_crawl():
    browser = webdriver.Chrome(executable_path="chromedriver.exe")

    browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })

    url = "http://bmfw.www.gov.cn/ybypmlcx/index.html"
    browser.get(url)
    time.sleep(5)

    for i in range(240):
        try:
            parse_info(browser)
        except:
            parse_info(browser)


def parse_insurance():
    file_list = os.listdir("page")
    en_drug_list = fnmatch.filter(file_list, "drug_*.json")
    cn_drug_list = fnmatch.filter(file_list, "cn_drug_*.json")

    drug_name_list = []
    drug_dose_list = []
    drug_category_list = []
    drug_standard_list = []
    drug_expiry_list = []
    drug_remark_list = []

    for dl in en_drug_list:
        with open(os.path.join("page", dl), "r") as f:
            d_list = json.load(f)

            for value in d_list:
                drug_name_list.append(value["drug_name"])
                drug_dose_list.append(value["剂型："])
                drug_category_list.append(value["报销类别："])
                drug_standard_list.append(value["医保支付标准："])
                drug_expiry_list.append(value["协议有效期："])
                drug_remark_list.append(value["备注："])

    pd.DataFrame({
        "药名": drug_name_list,
        "剂型": drug_dose_list,
        "报销类别": drug_category_list,
        "医保支付标准": drug_standard_list,
        "协议有效期": drug_expiry_list,
        "备注": drug_remark_list
    }).to_csv("../../processed/西药医保.csv", index=False)

    drug_name_list = []
    drug_category_list = []
    drug_standard_list = []
    drug_expiry_list = []
    drug_remark_list = []

    for dl in cn_drug_list:
        with open(os.path.join("page", dl), "r") as f:
            d_list = json.load(f)

            for value in d_list:
                drug_name_list.append(value["drug_name"])
                drug_category_list.append(value["报销类别："])
                drug_standard_list.append(value["医保支付标准："])
                drug_expiry_list.append(value["协议有效期："])
                drug_remark_list.append(value["备注："])

    pd.DataFrame({
        "药名": drug_name_list,
        "报销类别": drug_category_list,
        "医保支付标准": drug_standard_list,
        "协议有效期": drug_expiry_list,
        "备注": drug_remark_list
    }).to_csv("../../processed/中成药医保.csv", index=False)

if __name__ == "__main__":
    # info_crawl()
    parse_insurance()