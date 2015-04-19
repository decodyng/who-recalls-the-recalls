import requests
import dryscrape
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import csv

def ytLookup(businessName):

    ##Uses YellowPages api to look up address 
    baseURL = "http://api2.yp.com/listings/v1/search"
    params = {
        "key": "mxz8q66mxc",
        "format": "json",
        "term": businessName,
        "searchloc": "USA"
    }

    r = requests.get(baseURL, params=params)
    # print r.url
    results = r.json()
    out = {}
    if "searchResult" in results:
        if "searchListings" in results["searchResult"]:
            try:
                bestGuess = results["searchResult"]["searchListings"]["searchListing"][0]
            except:
                return out
            out["lat"] = bestGuess["latitude"]
            out["long"] = bestGuess["longitude"]
            out["street"] = bestGuess["street"]
            out["state"] = bestGuess["state"]
            out["city"] = bestGuess["city"]
            out["zip"] = bestGuess["zip"]
    return out


def singleRecallPageParse(url, lookup, preJS, year):
    ## Takes url of individual recall announcement page 
    out = {}
    r = requests.get(url)
    out["businessName"] = "Not Found"
    soup = BeautifulSoup(r.text)

    #Different parsing patterns for pre-Javascript and post-Javascript page formats 
    if preJS:
        body_table = soup.find('div', class_="body")
        body_row = body_table.table.find_all('tr', recursive=False)[-1]
        try:
            body = body_row.find('td', recursive=False).find('table', recursive=False).find('tr', recursive=False).get_text()
        except:
            print "BODY NOT FOUND"
            return out
    else:
        body = soup.find(class_="recall-body").get_text()
    paragraphs = body.split('\n')


    for paragraph in paragraphs:
        match = re.match('.*WASHINGTON, .* \d*, \d{4}.{3}(.*), (?:a|an|the) (.*) (?:establishment|firm|retail store|grocery chain|retailer).*.*', paragraph)
        match2 = re.match('.*WASHINGTON, .* \d*, \d{4}.{3}(.*), (?:a|an|the) (?:establishment|firm|retail store|grocery chain|retailer|importer of record) (?:from|in) (.*).*', paragraph)
        match3 = re.match('.*WASHINGTON, .* \d*, \d{4}.{3}(.*), (?:of) (.*)', paragraph)
        match4 = re.match('.*WASHINGTON, .* \d*, \d{4}.{3}(.*) is recalling', paragraph)
        if match:
            out["businessName"] = match.groups(1)[0]
            break
        elif match2:
            out["businessName"] = match2.groups(1)[0]
            break
        elif match3:
            out["businessName"] = match3.groups(1)[0]
            break
        elif match4:
            out["businessName"] = match4.groups(1)[0]
            break



    out["chicken"] = 0
    out["pork"] = 0
    out["beef"] = 0

    lookupkeys = lookup.keys()
    lookupset = set(lookupkeys)

    ## Uses lookup dictionary of words that correspond to cow/chicken/pork products
    ## Codes as strict binary: word in that group exists or does not. 
    ## Multiple groups can exist on one page 
    for paragraph in paragraphs[2:]:
        nopunc = re.sub(',:;.?!-_=~', '', paragraph)
        paragraphwords = set(el.lower() for el in nopunc.split(' '))
        foundWords = paragraphwords.intersection(lookupset)
        if len(foundWords) > 0:
            for word in foundWords:
                if lookup[word] == "cowproduct":
                    out["beef"] = 1
                elif lookup[word] == "chickenproduct":
                    out["chicken"] = 1
                elif lookup[word] == "porkproduct":
                    out["pork"] = 1
    return out




def fdaRecallParse(url, preJS, current=False):

    ##Uses post-Javascript dryscrape library 
    session = dryscrape.Session()
    session.visit(url)
    response = session.body()
    openSoup = BeautifulSoup(response)
    tableData = []

    if preJS:
        table = openSoup.find('table', class_='BorderTableColor')
        for ind, tr in enumerate(table.find('tbody').find_all('tr')[2:]):
            tableData.append({})
            tds = tr.find_all('td')
            if len(tds) < 3:
                break
            try:
                #having lines this long is bad form, but couldn't figure out an intelligent way around it in this case
                urlStr = "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2010/!ut/p/a1/jZDBCoJAEIafpQdYdlZF9CgLppa7SGS2lxjEdMFUTDz09CmdDKXmNj_fz8cMVTSjqsFRlzjotsF63pV9gwRs5nKIpO_5EArTTx2xZyDtCbguAJfNQJrIA-fgCPPP_sZ48Ksf_SEw-pjHJVUdDhXRzb2lWV_kWNckx2dBsM8rPRarITGAAb1QtdRMIZs1JyuIhAnS-gZW_vABtg_tHufsdQxAh97uDXOwxs4!/"
                tableData[ind]["case_number"] = tds[0].find('a').get_text().split(',')[0]
                tableData[ind]["recall_announcement"] = tds[0].find('a').get_text().split(',')[1]
                tableData[ind]["link"] = urlStr + tds[0].find('a').get('href')


            except AttributeError:
                #Accounts for cases with no link
                tableData[ind]["case_number"] = tds[0].get_text().split(',')[0]
                tableData[ind]["recall_announcement"] = tds[0].get_text().split(',')[1]


            tableData[ind]["recall_date"] = tds[1].get_text()
            tableData[ind]["qty_recovered"] = tds[2].get_text()



    else:
        table = openSoup.find(class_='sortable-table')
        for ind, tr in enumerate(table.find_all('tr')[1:]):
            tableData.append({})
            tds = tr.find_all('td')
            tableData[ind]["recall_announcement"] = re.sub('\n', '', tds[0].find('a').find(class_="display-title").get_text()).lstrip()
            #print row["recall_announcement"]
            tableData[ind]["case_number"] = re.sub('\n', '', tds[0].find('a').find(class_="recall-release").get_text()).lstrip()
            tableData[ind]["recall_date"] = re.sub('\n', '', tds[1].find(class_="recall-date").get_text()).lstrip()
            tableData[ind]["link"] = "http://www.fsis.usda.gov/" + tds[0].find('a').get('href')

            if current:
                # row["recall_distribution"] = re.sub('\n', '', tds[1].find(class_="qty-recalled").get_text()).lstrip()
                tableData[ind]["recall_distribution"] = re.sub('\n', '', tds[2].find(class_="qty-recalled").get_text()).lstrip()
            else:
                tableData[ind]["qty_recovered"]  = re.sub('\n', '', tds[2].find(class_="qty-recalled").get_text()).lstrip()

    return tableData

def saveCSV(toCSV, filename):
    df = pd.DataFrame(toCSV)
    df.to_csv(filename, encoding='utf-8')


def scrapeYear(i, lookup):
    out_file = "data/recalls_" + str(i) + ".csv"
    out_json =  "data/recalls_" + str(i) + ".json"
    url = urlDict[i]
    # print url
    preJS = False
    if i != "current":
        if i < 2013:
            preJS = True

    print i
    recordList = fdaRecallParse(url, preJS=preJS)
    for ind, record in enumerate(recordList):
        print ind
        if "link" not in record:
            continue
        singleURL = record["link"]
        print singleURL
        announce = record["recall_announcement"]
        singleDict = singleRecallPageParse(singleURL, lookup, preJS=preJS, year=i)
        recordList[ind] = dict(record, **singleDict)
        businessName = recordList[ind]["businessName"]
        addressDict = ytLookup(businessName)
        print addressDict
        recordList[ind] = dict(recordList[ind], **addressDict)
        announceMatch = re.match('.* Recalls (.*) (?:That|Due|For|Produced) (.+)', announce)
        if announceMatch:
            recordList[ind]["product_desc"] = announceMatch.groups(1)[0]
            recordList[ind]["recall_reason"] = announceMatch.groups(1)[1]


    with open(out_json, "w") as fp:
        json.dump(recordList, fp)
    saveCSV(recordList, out_file)

if __name__ == "__main__":
    urlDict = {
    2010: "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2010",
    2011: "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2011",
    2012: "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2012",
    2013: "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2013-new",
    2014: "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2014",
    2015: "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/recall-case-archive/recall-case-archive-2015",
    'current': "http://www.fsis.usda.gov/wps/portal/fsis/topics/recalls-and-public-health-alerts/current-recalls-and-alerts"
    }


    archived = {}

    with open("lookup.json") as fp:
        lookup = json.load(fp)

    # current = fdaRecallParse(current, current=True)
    for i in range(2014, 2016):
        scrapeYear(i, lookup)
    scrapeYear('current', lookup)
