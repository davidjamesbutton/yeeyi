import bs4
import copy
import datetime
import requests

URL = "http://www.yeeyi.com/forum/index.php?app=forum&act=display&fid=142"
OUTPUT_FILE = "Results.csv"

# Use 'rsuburb1' for Suburb key
# Use 'page' for page key
PARAMS = {
    "rcity1": 1,    # Melbourne
    "rents1": 5,    # $300 - $500 / week
    "order": 0      # Ad submitted, descending
}

LINES_SUBURBS = {
    "Frankston": [
        "Carrum",
        "Bonbeach",
        "Chelsea",
        "Edithvale",
        "Aspendale",
        "Mordialloc",
        "Parkdale",
        "Mentone",
        "Cheltenham",
        "Highett",
        "Moorabbin",
        "Patterson",
        "Bentleigh",
        "McKinnon",
        "Ormond",
        "Glenhuntly",
        "Caulfield"
    ],
    "Cranbourne": [
        "Springvale",
        "Westall",
        "Clayton",
        "Huntingdale",
        "Oakleigh",
        "Hughesdale",
        "Murrumbeena",
        "Carnegie"
    ]
}

MAX_PAGES = 10
MAX_PRICE = 500
MAX_DAYS_SINCE = 14
MIN_ROOMS = 3
DATE_TODAY = datetime.datetime.now().date()

def search(url, params = None):
    full_url = url
    if params is not None:
        param_keyvalues = list(params.items())
        query_string = "".join(map(lambda p: "&%s=%s" % p, param_keyvalues))
        full_url = url + query_string
    #print("Searching " + full_url)
    response = requests.get(full_url)
    response.raise_for_status()
    #print("Success")
    return response

def get_params(default_params, suburb, page):
    params = copy.copy(default_params)
    params["page"] = page
    params["rsuburb1"] = suburb
    return params

def raw_date_to_date(raw_date):
    date = None
    if "分钟前" in date_raw or "天前" in date_raw or "小时前" in date_raw:
        date = DATE_TODAY
    if "-" in date_raw:
        date = datetime.date(
            int(date_raw[0:4]),
            int(date_raw[5:7]),
            int(date_raw[8:10]))
    return date

file = open(OUTPUT_FILE, "w")
file.write("Last Edited, Price, Rooms, Suburb, Line, URL\n")
for train_line in LINES_SUBURBS.keys():
    print(train_line + " line")
    for suburb in LINES_SUBURBS[train_line]:
        print("\t" + suburb)
        page = 1
        while page < MAX_PAGES:
            params = get_params(PARAMS, suburb, page)
            response = search(URL, params)
            parser = bs4.BeautifulSoup(response.text, "html.parser")
            items = parser.select("div.qtc li")
            if len(items) < 2:
                if len(items[0].select("div")) == 0:
                    break
            if page == 1:
                items = items[1:]
            for item in items:
                num = item.select(".num")[0]
                price, date_raw = map(lambda x : x.getText(), num.select("p"))
                date = raw_date_to_date(date_raw)
                url = item.select(".ptxt h3 a")[0].get("href")
                days_since = (DATE_TODAY - date).days
                if days_since <= MAX_DAYS_SINCE:
                    response2 = search(url)
                    innerParser = bs4.BeautifulSoup(response2.text, "html.parser")
                    rooms = None
                    for row in innerParser.select("#mytable tr"):
                        if row.select("th")[0].getText() == "房屋户型:":
                            rooms = row.select("td")[0].getText()[0]
                    if rooms is None or int(rooms) >= MIN_ROOMS:
                        results_str = '%s, %s, %s, %s, %s,=HYPERLINK("%s")\n' % (date, price, rooms, suburb, train_line, url)
                        file.write(results_str)
                else:
                    page = MAX_PAGES
            page += 1
file.close()