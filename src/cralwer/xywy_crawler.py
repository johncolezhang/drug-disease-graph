from lxml import etree
import requests
import json
from tqdm import tqdm
import pandas as pd
import sys
sys.path.insert(0, "src")
import icd_mapping
import Levenshtein
import time
from collections import defaultdict


def get_html(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/51.0.2704.63 Safari/537.36'}
    res = requests.get(url=url, headers=headers)
    html = res.content.decode('gbk')
    return html


def drug_spider(url):
    html = get_html(url)
    selector = etree.HTML(html)
    drugs = [i.replace('\n', '').replace('\t', '').replace(' ', '') for i in
             selector.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')]
    return drugs


def basicinfo_spider(url):
    html = get_html(url)
    selector = etree.HTML(html)
    title = selector.xpath('//title/text()')[0]
    category = selector.xpath('//div[@class="wrap mt10 nav-bar"]/a/text()')
    desc = "".join(selector.xpath('//div[@class="jib-articl-con jib-lh-articl"]/p/text()'))\
        .replace("\n", "").replace("\r", "").strip()
    ps = selector.xpath('//div[@class="mt20 articl-know"]/p')
    infobox = []
    for p in ps:
        info = p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '')\
            .replace('   ', '').replace('\t', '')
        infobox.append(info.strip())

    basic_data = {'category': category, 'name': title.split('็็ฎไป')[0], 'desc': desc, 'attributes': infobox}
    return basic_data


def drug_treat_crawler():
    drug_url = 'http://jib.xywy.com/il_sii/drug/{}.htm'
    basic_url = 'http://jib.xywy.com/il_sii/gaishu/{}.htm'

    disease_dict = {}

    for page in tqdm(range(1, 11000)):
        try:
            drug_data = drug_spider(drug_url.format(page))
            drug_data = list(set([i.split('(')[-1].replace(')', '') for i in drug_data]))
            basic_data = basicinfo_spider(basic_url.format(page))
            disease_name = basic_data["name"]
            disease_dict[disease_name] = {"drug": drug_data, "basic": basic_data}
        except:
            continue

        if page != 0 and page % 100 == 0:
            with open("processed/all_disease_drug_desc.json", "w") as f:
                json.dump(disease_dict, f)


def get_disease_icd10():
    # ๅฏปๅป้ฎ่ฏ็่ฏ็ฉ-็พ็,ๅ่ฏดๆไนฆๆฐๆฎ
    with open("processed/all_disease_drug_desc.json", "r") as f:
        disease_dict = json.load(f)

    xywy_disease_drug_list = []
    for key, value in disease_dict.items():
        if key == "":
            continue

        for val in value["drug"]:
            xywy_disease_drug_list.append([key, val])

    # disease-kb้็ๆฐๆฎ
    with open("processed/disease_drug_list.json", "r") as f:
        disease_drug_list = json.load(f)

    all_disease_drug_list = xywy_disease_drug_list + disease_drug_list
    df_disease_drug = pd.DataFrame(all_disease_drug_list, columns=["disease", "drug"])
    df_disease_drug = df_disease_drug.drop_duplicates()

    # ๆๆnmpa่ฏ
    all_drug_list = get_all_drug()

    df_disease_drug = df_disease_drug[df_disease_drug["drug"].isin(all_drug_list)]
    df_disease_drug.to_csv("processed/current_disease_drug.csv", index=False)

    # ็ฐๆ7599ไธช็พ็
    all_disease_list = list(set(df_disease_drug["disease"].values))

    icd_map = icd_mapping.icdMapping()
    disease_icd_dict = icd_map.disease_dict

    # ็ฐๆ็พ็ไธcmekg็พ็็็ฒพ็กฎๅน้ 4105ไธช
    matched_disease_set = set(all_disease_list) & set(disease_icd_dict.keys())

    # ๅฉไธ็ๆจก็ณๅน้
    no_match_1_list = sorted(list(set(disease_icd_dict.keys()) - matched_disease_set))
    no_match_2_list = sorted(list(set(all_disease_list) - matched_disease_set))

    def str_clean(dis_str):
        return dis_str.replace("โ", "-").replace(" ", "").replace("\n", "").replace("\t", "") \
            .replace("๏ผป", "").replace("๏ผฝ", "").replace("[", "").replace("]", "").lower()

    no_match_2_clean_list = [str_clean(x) for x in no_match_2_list]
    no_match_2_dict = dict(zip(no_match_2_list, no_match_2_clean_list))
    no_match_1_clean_list = [str_clean(x) for x in no_match_1_list]
    no_match_1_dict = dict(zip(no_match_1_list, no_match_1_clean_list))

    # keyๆฏๅทฒๆ็พ็๏ผvalueๆฏcmekg็พ็
    dis_match_dict = {}
    for dis_2, dis_clean_2 in no_match_2_dict.items():
        max_ratio = 0
        max_dis = ""

        for dis_1, dis_clean_1 in no_match_1_dict.items():

            ratio = Levenshtein.ratio(dis_clean_2, dis_clean_1)

            if dis_clean_1 in dis_clean_2 or dis_clean_2 in dis_clean_1:
                ratio += 0.15

            if ratio > max_ratio and ratio > 0.85:
                max_ratio = ratio
                max_dis = dis_1

        if max_dis != "":
            dis_match_dict[dis_2] = max_dis

    for md in matched_disease_set:
        dis_match_dict[md] = md

    # ๅฝๅ็พ็็icd็ผๅท
    cur_dis_icd_dict = {}
    for key, value in dis_match_dict.items():
        cur_dis_icd_dict[key] = disease_icd_dict[value]

    # around 4500 on-promise disease have icd code
    with open("processed/current_disease_icd_dict.json", "w") as f:
        json.dump(cur_dis_icd_dict, f)

    # around 1844 disease
    no_match_icd_disease_list = list(set(disease_icd_dict.keys()) -
                                     matched_disease_set.intersection(set(dis_match_dict.values())))

    # ๅถไฝๆฒกๆmatchๅฐicd code็on-promise disease
    with open("processed/no_match_icd_disease_list.json", "w") as f:
        json.dump(no_match_icd_disease_list, f)


def get_all_drug():
    df_all_nmpa = pd.read_csv("processed/all_nmpa_info.csv", dtype=str).fillna("")
    df_import = pd.read_csv("d:/pgkb_graph/processed/imported_drug.csv", dtype=str).fillna("")
    all_drug_list = list(set(list(df_all_nmpa["name"].values) + list(df_import["drug_name"].values)))
    return all_drug_list


def cmekg_crawler():
    # ้ๅฏนmatchไธๅฐ็็พ็๏ผๅฉ็จcmekgๅทฒๆ็ๆฐๆฎ๏ผๆ็พ็-่ฏ็ฉๅณ็ณปๅฏนๅน้ๅบๆฅใ
    with open("processed/no_match_icd_disease_list.json", "r") as f:
        no_match_icd_disease_list = json.load(f)

    url_template = "https://zstp.pcl.ac.cn:8002/knowledge?name={}&tree_type=็พ็"

    dis_drug_list = []
    dis_icd_list = []
    for nmcd in tqdm(no_match_icd_disease_list):
        req = requests.get(url_template.format(nmcd))
        result_dict = json.loads(req.content)
        treat_node_id = list(filter(lambda x: x["value"] == "่ฏ็ฉๆฒป็", result_dict["link"]))

        if len(treat_node_id) > 0:
            treat_node_id = treat_node_id[0]["target"]
            dis_node_list = list(map(lambda x: x["target"],
                                     list(filter(lambda x: x["source"] == treat_node_id, result_dict["link"]))))

            disease_list = list(map(
                lambda x: x["label"],
                list(filter(lambda x: x["name"] in dis_node_list and "symbol" not in x.keys(), result_dict["node"]))
            ))

            for dl in disease_list:
                dis_drug_list.append([nmcd, dl])

        icd_node_id = list(filter(lambda x: x["value"] == "ICD-10", result_dict["link"]))
        if len(icd_node_id) > 0:
            icd_node_id = icd_node_id[0]["target"]
            icd_node_list = list(map(lambda x: x["target"],
                                     list(filter(lambda x: x["source"] == icd_node_id, result_dict["link"]))))

            icd_list = list(map(
                lambda x: x["label"],
                list(filter(lambda x: x["name"] in icd_node_list, result_dict["node"]))
            ))

            for il in icd_list:
                dis_icd_list.append([nmcd, il])

        time.sleep(0.3)

    with open("processed/cmekg_disease_drug_list.json", "w") as f:
        json.dump(dis_drug_list, f)

    with open("processed/cmekg_disease_icd_list.json", "w") as f:
        json.dump(dis_icd_list, f)


def cmekg_icd_mapping():
    with open("processed/cmekg_disease_icd_list.json", "r") as f:
        dis_icd_list = json.load(f)

    icd_map = icd_mapping.icdMapping()
    icd10_subclass_dict = icd_map.icd10_subclass_dict

    dis_icd_dict = defaultdict(dict)
    for dis, icd in dis_icd_list:
        dis_icd_dict[dis][icd] = icd10_subclass_dict.get(icd, "")

    with open("processed/cmekg_disease_icd_dict.json", "w") as f:
        json.dump(dis_icd_dict, f)


if __name__ == "__main__":
    # drug_treat_crawler()
    # get_disease_icd10()
    # cmekg_crawler()
    cmekg_icd_mapping()


    """
    ่ฏ็ฉicdๅ่ฏ็ฉ-็พ็ๅณ็ณปๅฏน่กฅๅ
    1. ๅ็จbgi graphๅทฒๆ็พ็ๅๅcmekg็พ็ๅๅๅน้๏ผ็ฒพ็กฎๅ็ธไผผๅบฆๅน้๏ผ๏ผ็ปๅน้ๅฐ็็พ็้ไธicd10็ผๅทๅไฟกๆฏใ
    2. ้ๅฏนbgi graphๆฒกๆๅน้ๅฐ็็พ็ๅ๏ผicd10็ผๅทๅ็็ฉบใ
    3. ้ๅฏนcmekgๆฒกๆๅน้ๅฐ็็พ็๏ผๅจcmekgไธญ็ฌ่ซๆฃ็ดข็พ็-่ฏ็ฉๅณ็ณปๅฏน๏ผๅนถไธ่กฅๅๅฐ็ฐๆ็พ็-่ฏ็ฉๅณ็ณปๅฏนไธญใ
    """

    """
    ็็็พ็ๅคๆญ
    ๅบไบicd10็ฌฌไบ็ซ?่ฟ็คไธญๆถๅๅฐ็็พ็๏ผๅฐ็็็ธๅณ็พ็ๆฝๅบๅบๆฅ๏ผๆ?นๆฎ็พ็-่ฏ็ฉๅณ็ณปๅฏน๏ผๅคๆญ่ฏ็ฉๆฏๅฆไธบ็็่ฏ็ฉ๏ผๅนถๆไธ็็่ฏๆ?็ญพใ
    ๆ?นๆฎ็็่ฏๆฒป็้ป่พ๏ผ้ถ็น่ฏ๏ผๅนฟ่ฐฑๆ็็ป่่ฏ็ญ๏ผ๏ผ็ป็็่ฏๆไธๆฒป็้ป่พๆ?็ญพ๏ผ่ฏฅ้จๅๅทฅไฝ้ไฝฟ็จๆๆฌๆฝๅๅ่ฝ๏ผๅจ่ฏ่ฏดๆไนฆไธญๆฃ็ดข้ป่พๆ?็ญพใ
    """
