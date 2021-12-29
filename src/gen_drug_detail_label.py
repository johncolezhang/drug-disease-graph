import json
from util.py2neo_util import py2NeoUtil
from tqdm import tqdm
from collections import defaultdict
import pymysql


def gen_drug_chemical_detail_label():
    n_util = py2NeoUtil()

    query_template = """
    match (n:drug)
    return n.drug_name as drug_name
    """
    all_drug = n_util.run_cypher(query_template)
    all_drug = [x["drug_name"] for x in all_drug]
    drug_label_dict = {}
    drug_affect_dict = {}

    chemical_label_dict = {}
    chemical_affect_dict = {}

    for drug_name in tqdm(all_drug):
        query_template = """
            match (n:drug)
            where n.drug_name = "{}"
            return n.drug_name as drug_name, n.indication as indication,
            n.component as component, n.in_medical_insurance as in_medical_insurance,
            n.insurance_level as insurance_level, n.insurance_dosage_form as insurance_dosage_form,
            n.insurance_drug_category as insurance_drug_category,
            n.has_fda_warning as has_fda_warning,
            n.adverse_reaction as adverse_reaction, n.attention_notice as attention_notice,
            n.avoid as avoid, n.drug_interaction as drug_interaction, n.dosage as dosage,
            n.older_attention as older_attention, n.children_attention as children_attention
            """.format(drug_name)
        d_result = n_util.run_cypher(query_template)

        if len(d_result) > 0:
            d_result = d_result[0]
        else:
            d_result = dict()

        label_list = []
        insurance_dict = {}
        affect_dict = {}

        for key, value in d_result.items():

            if key in ["in_medical_insurance", "has_fda_warning"]:
                if value and value == "是":
                    value = True
                else:
                    value = False

            if key in ["in_medical_insurance", "insurance_level",
                       "insurance_dosage_form", "insurance_drug_category"]: # insurance keys
                insurance_dict[key] = value
                continue

            if key in ["has_fda_warning"]:
                if d_result[key] == "是":
                    label_list.append("fda_warning")
                    affect_dict["fda_warning"] = {}
                continue

        if "in_medical_insurance" in insurance_dict.keys() and insurance_dict["in_medical_insurance"] and \
           "insurance_level" in insurance_dict.keys() and insurance_dict["insurance_level"] in ["甲", "乙"]:
            if insurance_dict["insurance_level"] == "甲":
                insurance_label = "type_a_national_insurance"
            else:
                insurance_label = "type_b_national_insurance"

            label_list.append(insurance_label)

            affect_dict[insurance_label] = {
                "insurance_dosage_form": insurance_dict.get("insurance_dosage_form", ""),
                "insurance_drug_category": insurance_dict.get("insurance_drug_category", ""),
                "insurance_level": insurance_dict.get("insurance_level", "")
            }

        drug_label_dict[drug_name] = list(set(label_list))
        drug_affect_dict[drug_name] = affect_dict

        # 获取化合物信息
        query_template = """
        match (n:drug {{drug_name: "{drug_name}"}})<-[:chemical_drug_relation]-(m:chemical)
        return n.drug_name as drug_name, m.chemical_name as chemical_name
        """.format(drug_name=drug_name)
        result = n_util.run_cypher(query_template)
        chemical_list = [x["chemical_name"] for x in result]


        for chemical_name in chemical_list:
            if chemical_name in chemical_label_dict.keys():
                continue

            query_template = """
                match (m:chemical)<-[]-(v:variant)
                where m.chemical_name = "{chem_name}"
                return m.chemical_name as chemical_name
                union
                match (m:chemical)<-[]-(dip:diplotype)
                where m.chemical_name = "{chem_name}"
                return m.chemical_name as chemical_name
                union
                match (m:chemical)<-[]-(ge:gene)
                where m.chemical_name = "{chem_name}"
                return m.chemical_name as chemical_name
            """.format(chem_name=chemical_name)
            result = n_util.run_cypher(query_template)

            c_label_list = []
            c_affect_dict = {}

            # label code pgx
            if len(result) > 0:
                is_pgx = True
                c_label_list.append("pgx")
                c_affect_dict["pgx"] = {}
            else:
                is_pgx = False

            # 获取 临床1A/1B标签，研究标签，FDA药物标签，以及获得 影响类型（表型）
            if is_pgx:
                query_template = """
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:drug_label]-(v:variant)
                where r.organization = "FDA"
                return m.chemical_name as chemical_name, v.display as v_name, 
                "drug_label" as relation_type, "variant" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:drug_label]-(dip:diplotype)
                where r.organization = "FDA"
                return m.chemical_name as chemical_name, dip.display as v_name, 
                "drug_label" as relation_type, "diplotype" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:drug_label]-(ge:gene)
                where r.organization = "FDA"
                return m.chemical_name as chemical_name, ge.display as v_name, 
                "drug_label" as relation_type, "gene" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:clinical_annotation]-(v:variant)
                where r.evidence_level =~ "1[A|B]"
                return m.chemical_name as chemical_name, v.display as v_name, 
                "clinical_1A_1B" as relation_type, "variant" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:clinical_annotation]-(dip:diplotype)
                where r.evidence_level =~ "1[A|B]"
                return m.chemical_name as chemical_name, dip.display as v_name, 
                "clinical_1A_1B" as relation_type, "diplotype" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:clinical_annotation]-(ge:gene)
                where r.evidence_level =~ "1[A|B]"
                return m.chemical_name as chemical_name, ge.display as v_name, 
                "clinical_1A_1B" as relation_type, "gene" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:cpic_guideline]-(v:variant)
                where r.CPIC_level = "A" or r.PGKB_evidence_level =~ "1[A|B]"
                return m.chemical_name as chemical_name, v.display as v_name, 
                "clinical_1A_1B" as relation_type, "variant" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:cpic_guideline]-(dip:diplotype)
                where r.CPIC_level = "A" or r.PGKB_evidence_level =~ "1[A|B]"
                return m.chemical_name as chemical_name, dip.display as v_name, 
                "clinical_1A_1B" as relation_type, "diplotype" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:cpic_guideline]-(ge:gene)
                where r.CPIC_level = "A" or r.PGKB_evidence_level =~ "1[A|B]"
                return m.chemical_name as chemical_name, ge.display as v_name, 
                "clinical_1A_1B" as relation_type, "gene" as v_type
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:cn_drug_label]-(ge:gene)
                return m.chemical_name as chemical_name, ge.display as v_name, 
                "cn_drug_label" as relation_type, "gene" as v_type
                """.format(chem_name=chemical_name)
                result = n_util.run_cypher(query_template)

                # label code clinical_1A_1B
                label_1A_1B_list = list(filter(lambda x: x["relation_type"] == "clinical_1A_1B", result))
                if len(label_1A_1B_list) > 0:
                    c_label_list.append("clinical_1A_1B_label")
                    affect_list = list(set(["{}|{}".format(x["v_name"], x["v_type"]) for x in label_1A_1B_list]))
                    c_affect_dict["clinical_1A_1B_label"] = defaultdict(list)
                    for al in affect_list:
                        k, v = al.split("|")
                        c_affect_dict["clinical_1A_1B_label"][v].append(k)


                # label code fda_drug_label
                label_FDA_list = list(filter(lambda x: x["relation_type"] == "drug_label", result))
                if len(label_FDA_list) > 0:
                    c_label_list.append("fda_drug_label")
                    affect_list = list(set(["{}|{}".format(x["v_name"], x["v_type"]) for x in label_FDA_list]))
                    c_affect_dict["fda_drug_label"] = defaultdict(list)
                    for al in affect_list:
                        k, v = al.split("|")
                        c_affect_dict["fda_drug_label"][v].append(k)

                # label code nmpa_drug_label
                label_cn_drug_list = list(filter(lambda x: x["relation_type"] == "cn_drug_label", result))
                if len(label_cn_drug_list) > 0:
                    c_label_list.append("nmpa_drug_label")
                    affect_list = list(set(["{}|{}".format(x["v_name"], x["v_type"]) for x in label_cn_drug_list]))
                    c_affect_dict["nmpa_drug_label"] = defaultdict(list)
                    for al in affect_list:
                        k, v = al.split("|")
                        c_affect_dict["nmpa_drug_label"][v].append(k)

                query_template = """
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:clinical_annotation]-()
                return distinct r.phenotype_category as phenotype_category
                union
                match (m:chemical {{chemical_name: "{chem_name}"}})<-[r:research_annotation]-()
                return distinct r.phenotype_category as phenotype_category
                """.format(chem_name=chemical_name)
                result = n_util.run_cypher(query_template)

                # label_code pc_toxicity, pc_efficacy, pc_dosage, pc_metabolism
                for x in [res["phenotype_category"].lower() for res in result]:
                    if "toxicity" in x:
                        c_label_list.append("pc_toxicity")
                        c_affect_dict["pc_toxicity"] = {}
                    if "efficacy" in x:
                        c_label_list.append("pc_efficacy")
                        c_affect_dict["pc_efficacy"] = {}
                    if "dosage" in x:
                        c_label_list.append("pc_dosage")
                        c_affect_dict["pc_dosage"] = {}
                    if "metabolism" in x:
                        c_label_list.append("pc_metabolism")
                        c_affect_dict["pc_metabolism"] = {}

            chemical_label_dict[chemical_name] = c_label_list
            chemical_affect_dict[chemical_name] = c_affect_dict



    with open("json/all_drug_detail_label.json", 'w', encoding="utf-8") as f:
        json.dump(drug_label_dict, f)

    with open("json/all_drug_detail_affect.json", 'w', encoding="utf-8") as f:
        json.dump(drug_affect_dict, f)

    with open("json/all_chemical_detail_label.json", 'w', encoding="utf-8") as f:
        json.dump(chemical_label_dict, f)

    with open("json/all_chemical_detail_affect.json", 'w', encoding="utf-8") as f:
        json.dump(chemical_affect_dict, f)


def dump_db():
    with open("json/all_drug_detail_label.json", 'r', encoding="utf-8") as f:
        drug_label_dict = json.load(f)

    with open("json/all_drug_detail_affect.json", 'r', encoding="utf-8") as f:
        drug_affect_dict = json.load(f)

    with open("json/all_chemical_detail_label.json", 'r', encoding="utf-8") as f:
        chemical_label_dict = json.load(f)

    with open("json/all_chemical_detail_affect.json", 'r', encoding="utf-8") as f:
        chemical_affect_dict = json.load(f)

    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="demo",
        passwd="demo",
        db="local_bge_open",
        charset='utf8'
    )

    # insert drug label
    for key, value in drug_label_dict.items():
        insert_str = "INSERT INTO graph_drug_detail_label (drug_name, code, affect) values"
        for val in value:
            affect_str = json.dumps(drug_affect_dict[key][val], ensure_ascii=False)
            insert_str += "('{}', '{}', '{}'),".format(key, val, affect_str)

        insert_str = insert_str.strip(", ") + ";"

        if len(value) > 0:
            try:
                # print(insert_str)
                conn.cursor().execute(insert_str)
                conn.commit()
            except Exception as e:
                print(e)
                print(insert_str)


    # insert chemical label
    for key, value in chemical_label_dict.items():
        insert_str = "INSERT INTO graph_chemical_detail_label (chemical_name, code, affect) values"
        for val in value:
            affect_str = json.dumps(chemical_affect_dict[key][val], ensure_ascii=False)
            insert_str += "('{}', '{}', '{}'),".format(key, val, affect_str)

        insert_str = insert_str.strip(", ") + ";"

        if len(value) > 0:
            try:
                # print(insert_str)
                conn.cursor().execute(insert_str)
                conn.commit()
            except Exception as e:
                print(e)
                print(insert_str)


if __name__ == "__main__":
    # gen_drug_chemical_detail_label()
    dump_db()
