import pandas as pd
import numpy as np
import os
from datetime import datetime
from string import punctuation
from pymongo import MongoClient

def handle_uploaded_file(f, competition_name):
    if "files_for_download" not in os.listdir(os.path.join(os.getcwd(), 'deployer')):
        os.mkdir(os.path.join(os.getcwd(), 'deployer', 'files_for_download'))
    filenames = os.listdir(os.path.join(os.getcwd(), 'deployer', 'files_for_download'))
    
    for filename in filenames:
        file_fullpath = os.path.join(os.getcwd(), 'deployer', 'files_for_download', filename)
        os.remove(file_fullpath)

    xl =pd.ExcelFile(f)

    # 找出四張表: 裁判清單、避裁規則、裁判互避、場次資、
    df_judges = xl.parse("裁判清單")
    df_avoidance = xl.parse("避裁規則")
    df_avoidance_judges = xl.parse("裁判互避")
    df_session = xl.parse("場次資訊")

    # 定義基本資料: 時段、裁判、學校
    all_sessions = list(set(df_session['時段']))
    all_judges = list(df_judges['裁判'])
    all_schools = list(set(np.hstack([list(df_session['學校一']), list(df_session['學校二'])])))

    # 裁判限制式
    df_judges['可排時段'] = df_judges['可排時段'].astype(str).apply(lambda x : x.split(', '))
    df_avoidance['裁判'] = df_avoidance['裁判'].astype(str).apply(lambda x : x.split(', '))

    # 擴充裁判表的訊息(onehot處理): 避裁學校、可工作時段
    def extend_judge_table(row):
        for i in all_sessions:
            row['時段'+ str(i)] = True if str(i) in row['可排時段'] else False
        for sch in all_schools:
            avoid_judges = list(df_avoidance.loc[df_avoidance['學校'] == sch, '裁判'])
            avoid_judges = avoid_judges[0] if avoid_judges != [] else []
            row[sch + "_避"] = True if row['裁判'] in avoid_judges else False
        return row
    df_judges = df_judges.apply(extend_judge_table, axis=1)
    df_judges.drop('可排時段', inplace=True, axis=1)

    # 紀錄裁判已經被排上的時段
    df_judges_arragement = df_judges.copy()
    for i in all_sessions:
        df_judges_arragement['時段'+str(i)+'_已安排'] = False








    def find_a_judge(df_judges_arragement, sess, place, sch1, sch2):
        workable_judges = list(df_judges_arragement\
                            [df_judges_arragement['時段'+str(sess)] == True]\
                            [df_judges_arragement[sch1 + "_避"] == False]\
                            [df_judges_arragement[sch2 + "_避"] == False]\
                            [df_judges_arragement['時段'+str(sess)+'_已安排'] == False]\
                            ['裁判'])
        if len(workable_judges) != 0:
            finded_judge = np.random.choice(workable_judges)
            df_judges_arragement.loc[df_judges_arragement['裁判'] == finded_judge, '時段'+str(sess)+'_已安排'] = place
            return finded_judge
        else:
            return None

    def get_judges_conflict(arranged_judges):
        for idx, row in df_avoidance_judges.iterrows():
            j1_con, j2_con = row['裁判一'], row['裁判二']
            if j1_con in arranged_judges and j2_con in arranged_judges:
    #             print("AAAAAAAAA")
    #             print(arranged_judges)
                return True
        return False
        
    def find_judges(df_judges_arragement, sess, place, sch1, sch2):
        count = 0
        arranged_judges = []
        df_error_left_judges = []
        conflict_judges = []
        while True:
            # 檢查場次及學校避裁衝突
            for i in range(3):
                finded_judge = find_a_judge(df_judges_arragement, sess, place, sch1, sch2)
                arranged_judges.append(finded_judge)
                if finded_judge == None:
                    df_error_left_judges = df_judges_arragement[df_judges_arragement['時段'+str(sess)+'_已安排'] == False]
            
            # 檢查裁判互避衝突
            if not get_judges_conflict(arranged_judges):
                break
            elif count > 100:
                conflict_judges = arranged_judges
            else:
                for judge in arranged_judges:
                    df_judges_arragement.loc[df_judges_arragement['裁判'] == judge, '時段'+str(sess)+'_已安排'] = False
                arranged_judges = [] 
            count += 1
        return arranged_judges, df_error_left_judges, conflict_judges







    # 排裁判上場次表
    for idx, row in df_session.iterrows():
        sess = row['時段']
        place = row['會場']
        sch1 = row['學校一']
        sch2 = row['學校二']
        arranged_judges, df_error_left_judges, conflict_judges = find_judges(df_judges_arragement, sess, place, sch1, sch2)
        df_session.loc[idx, ['裁判一', '裁判二', '裁判三']] = arranged_judges
        # if len(df_error_left_judges) != 0 or len(conflict_judges) != 0:
        #     print(sess, place, sch1, sch2)
        #     print(df_error_left_judges)
        #     print(conflict_judges)
    nowtime = str(datetime.now())
    puns = punctuation + ' '
    for p in puns:
        nowtime = nowtime.replace(p, "")
    filename = competition_name + nowtime + '.csv'
    df_session.to_csv(os.path.join(os.getcwd(), 'deployer', 'files_for_download', filename), index=False)
    num_nan = int((df_session.values.reshape(1, -1)[0] == None).sum())



    # mongodb://<user_name>:<user_password>@ds<xxxxxx>.mlab.com:<xxxxx>/<database_name>
    conn = MongoClient(os.environ.get("MONGO_URL"))
    db = conn.superuniversitycourses
    collection = db.debate_judge_deployment

    insert_data = {
        "盃賽名稱": competition_name,
        "裁判清單": list(df_judges.T.to_dict().values()),
        "避裁規則": list(df_avoidance.T.to_dict().values()),
        "裁判互避": list(df_avoidance_judges.T.to_dict().values()),
        "場次資訊": list(df_session.T.to_dict().values()),
    }

    test_all_judges = ['丁冠羽', '丁啟翔', '丁文凱', '卓祐先', '廖本新', '彭韡', '歐陽正霆', '江運澤', '汪旻寬', '洪惇旻', '翟永誠', '蔡曉松', '蕭靖穎', '藍偉太', '賴永承', '鄭羽軒', '阮崇維', '黃婉儀']
    if all_judges == test_all_judges:
        insert_data['Test'] = True
    else:
        insert_data['Test'] = False
        
    collection.insert_one(insert_data)

    return all_schools, all_judges, df_session.to_html(index=False), num_nan, filename


    
