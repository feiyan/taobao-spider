# -*- coding: utf-8 -*-

import json
import os
import glob
import redis
import traceback

PROJECT_ROOT = os.getcwd()
r = redis.StrictRedis()

def parseTaobaoAttr():
    with open(PROJECT_ROOT+'/cate.txt', 'r') as fp, open(PROJECT_ROOT+'/tb_attr.txt', 'w+') as fp_w:
        for line in fp.readlines():
            cate_id, json_str = line.strip().split("\t")
            cates = json.loads(json_str)
            file = PROJECT_ROOT + '/attr/%s.json' % cate_id
            if os.path.getsize(file) >= 10000:
                with open(file, 'r') as fp_attr:
                    # 上一步json.dump的文件被转为bytes类型了，这里使用eval解析
                    # use eval() is dangerous
                    # Python 3.x 的字符编码处处是坑
                    try:
                        arr = json.loads(eval(fp_attr.read()))
                        if 'models' in arr and 'catProp' in arr['models'] and 'dataSource' in arr['models']['catProp']:
                            for row in arr['models']['catProp']['dataSource']:
                                lst = []
                                lst.append('-')
                                lst.append(row['uiType'])
                                lst.append(row['label'])
                                lst.append(str(int(row['required'])))
                                if 'dataSource' in row and len(row['dataSource']) > 0:
                                    lst.append(','.join(list(map(lambda x: x["text"], row['dataSource']))))
                                else:
                                    lst.append('-')
                                fp_w.write("-".join(cates.values())+"\n")
                                fp_w.write("\t".join(lst)+"\n")
                    except Exception:
                        print(cate_id)
                        traceback.print_exc()
                        exit()
                    
    pass

def parseTaobaoCate():
    with open(PROJECT_ROOT+'/cate.txt', 'w+', encoding="utf8") as fp_cate:
        for file in glob.glob(PROJECT_ROOT + '/cate/*.json'):
            with open(file, 'r', encoding="utf8") as fp:
                arr = json.load(fp)
                if arr['data']['dataSource'] is not None:
                    for row in arr['data']['dataSource']:
                        if 'leaf' not in row:
                            continue
                        if row['leaf']:
                            cat_ids = row['idpath']
                            cat_names = row['path']
                            if row['isBrand']:
                                cat_ids = cat_ids[:-1]
                                cat_names = cat_names[:-1]
                            cate_id = int(row['submitId'])
                            cache_key = "cate_%d" % cate_id
                            if not r.get(cache_key):
                                m = {}
                                for i in range(len(cat_ids)):
                                    m[cat_ids[i]] = cat_names[i]
                                fp_cate.write("{}\t{}\n".format(str(cate_id), json.dumps(m)))
                                r.set(cache_key, "1", 120)

if __name__ == '__main__':
    parseTaobaoCate()
    parseTaobaoAttr()
