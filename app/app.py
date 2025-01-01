from default.basic_tor import *
from blackbasta.blackbasta import *
from play.play import *
from rhysida.rhysida import *
from bianlian.bianlian import *
from medusa.medusa import *
from raworld.raworld import *
from cactus.cactus import *
from telegram.telegram import *
from elastic import ELK
import json
import os

def reorder_dict(data):
    desired_order = ["title", "Description", "update_date", "site", "address", "country", "region", "all data", "tel", "link", "images", "times", "timer", "price", "views"]
    reordered = {}
    for key, value in data.items():
        if isinstance(value, dict):
            reordered[key] = {k: value.get(k,"N/A") for k in desired_order}
        else:
            reordered[key] = value

    if len(reordered)==0:
        tmp = {}
        for desired_key in desired_order:
            tmp[desired_key] = "N/A"
        reordered["N/A"]=tmp
                   
    return reordered

def make_output_file(name,result):
    try:
         os.mkdir("/app/OUT")
    except FileExistsError as e:
         pass
    reorder = reorder_dict(result)
    file_path = f"/app/OUT/{name}_result.json"
    with open(file_path, "w") as json_file:
            json.dump(reorder, json_file, indent=4)
    send_file_telegram(file_path)
    return reorder

def process():
    urls = {
        "blackbasta":"http://stniiomyjliimcgkvdszvgen3eaaoz55hreqqx6o77yvmpwt7gklffqd.onion/",
        "play": "http://mbrlkbtq5jonaqkurjwmxftytyn2ethqvbxfu4rgjbkkknndqwae6byd.onion/",
        "rhysida":"http://rhysidafohrhyy2aszi7bm32tnjat5xri65fopcxkdfxhi4tidsg7cad.onion",
        "bianlian": "http://bianlianlbc5an4kgnay3opdemgcryg2kpfcbgczopmm3dnbz3uaunad.onion/",
        "medusa": "http://xfv4jzckytb4g3ckwemcny3ihv4i5p4lqzdpi624cxisu35my5fwi5qd.onion/",
        "raworld" : "http://raworldw32b2qxevn3gp63pvibgixr4v75z62etlptg3u3pmajwra4ad.onion/",
        "cactus":"https://cactusbloguuodvqjmnzlwetjlpj6aggc6iocwhuupb47laukux7ckid.onion/",
    }
    classes = {
        "blackbasta":osint_blackbasta,
        "play":osint_play,
        "rhysida":osint_rhysida,
        "bianlian": osint_bianlian,
        "medusa":osint_medusa,
        "raworld": osint_raworld,
        "cactus":osint_cactus,
    }
    js = ['blackbasta','play','rhysida', 'bianlian', 'medusa', 'raworld']
    tmp = osint_tor_render_js()
    tmp.init_browser()
    for key,value in classes.items():
        osint_class = value(urls[key])
        if key in js:
            osint_class.browser = tmp.browser
            osint_class.page = tmp.page
            result, tmp.browser, tmp.page = osint_class.process()
        else:
             result = osint_class.process()
        send_message(key,make_output_file(key,result))
    tmp.close_browser()
    
    ELK().process()