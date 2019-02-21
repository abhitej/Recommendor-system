# -*- coding: utf-8 -*-
"""
Created on Sat Nov  3 12:24:27 2018

@author: Abhitej Kodali
"""

"""
python script to scrape the results from unitedstateszipcodes and save to a file
"""

from bs4 import BeautifulSoup
import os
import pandas as pd
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time


co = webdriver.ChromeOptions()
#co.add_argument("headless")
prefs={"profile.managed_default_content_settings.images": 2, 'disk-cache-size': 4096 }
co.add_experimental_option('prefs', prefs)

def get_proxies(co=co):
    driver = webdriver.Chrome("chromedriver.exe", options=co)
    driver.get("https://www.us-proxy.org/")

    PROXIES = []
    proxies = driver.find_elements_by_css_selector("tr[role='row']")
    for p in proxies:
        result = p.text.split(" ")

        if result[-1] == "yes":
            PROXIES.append(result[0]+":"+result[1])

    driver.close()
    return PROXIES


ALL_PROXIES = get_proxies()


def proxy_driver(PROXIES, co=co):
    prox = Proxy()
    ua=UserAgent()
    while True:
        if PROXIES:
            pxy = PROXIES[-1]
            break
        else:
            print("--- Proxies used up (%s)" % len(PROXIES))
            PROXIES = get_proxies()    

    prox.proxy_type = ProxyType.MANUAL
    prox.http_proxy = pxy
    #prox.socks_proxy = pxy
    prox.ssl_proxy = pxy

    capabilities = dict(DesiredCapabilities.CHROME)
    capabilities["chrome.page.settings.userAgent"] = (ua.random)
    prox.add_to_capabilities(capabilities)
    service_args=['--ssl-protocol=any','--ignore-ssl-errors=true']
    driver = webdriver.Chrome("chromedriver.exe", options=co, desired_capabilities=capabilities,service_args=service_args)

    return driver


def scrape_results(soup, zipcode):
    corn = BeautifulSoup(soup.page_source, "lxml")
    doc = {'zipcode' : zipcode, 'id' : zipcode[:3]}
    for tab in corn.findAll('table'):
        if "Population Density" in str(tab):
            heads = tab.findAll('th')
            vals = tab.findAll('td', {'class' : 'text-right'})
            for i, head in enumerate(heads):
                doc[head.text] = vals[i].text
        if "Land Area" in str(tab):
            heads = tab.findAll('th')
            vals = tab.findAll('td', {'class' : 'text-right'})
            for i, head in enumerate(heads):
                doc[head.text] = vals[i].text
    return doc


dr = proxy_driver(ALL_PROXIES)
dr.delete_all_cookies()

header = [u'Housing Units', 'zipcode', u'Water Area', u'Median Home Value', u'Median Household Income', 
              u'Population Density', u'Occupied Housing Units', u'Population', 'id', u'Land Area']
    
if os.path.isfile("E:/Cognitive Computing BIA662/Project/scraped_results.csv"):
    data = pd.read_csv("E:/Cognitive Computing BIA662/Project/scraped_results.csv", na_values=0, dtype={'zipcode':str})
    #data = data[(data['Housing Units']>0) | (data['Land Area']>0)]
    zips = data['zipcode'].tolist()
else:
    data = pd.DataFrame(columns=header)

df = pd.read_csv("E:/Cognitive Computing BIA662/Project/zipcode_urls.csv")

while True:
    for url in df['urls']:
        zipcode = url.split("/")[-2]
        if zipcode not in zips:
            try:
                dr.get(url)
                doc = scrape_results(dr, zipcode)
                doc['id'] = zipcode
                if(doc.keys()) == 2:
                    continue
                row = {}
                for h in header: 
                    if h in doc:
                        row[h] = doc[h].replace("$","").replace(",","").replace("n/a","")
                    else:
                        row[h] = "0"
                print(row.values())
                data = data.append(row,ignore_index=True)
                data.to_csv("E:/Cognitive Computing BIA662/Project/scraped_results.csv",index=False)
            #except Exception as E:
            #    print("Exception Occured", E, zipcode)
            #    continue
            except:
                if ALL_PROXIES:
                    new = ALL_PROXIES.pop()
                    # reassign driver if fail to switch proxy
                    dr = proxy_driver(ALL_PROXIES)
                    print("--- Switched proxy to: %s" % new)
                    time.sleep(1)

dr.quit()
