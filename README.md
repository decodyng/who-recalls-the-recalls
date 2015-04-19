# who-recalls-the-recalls
Good friend of mine needed data on FDA recalls, along with company addresses and text-parsed data from the recall releases. Being of generous spirit and procrastinating mood on that particular Saturday, this happened.

##Dependencies: 
requests, 
BeautifulSoup4,  
pandas, 
dryscrape,

##Output: 
###Data from Aggregated/Archive Page
case_number: FDA recall number 

recall_announcement: Wording of recall announcement on aggregated recall data page 

recall_date

qty_recovered: Amount, in lbs, of product recovered [For closed recalls] Recall type [For open recalls] 

###Data from individual recall page
businessName: Name of business recalling products (scraped via regex from url in "link" field) "Not Found" where regex match failed

beef: Reference made to beef products in recall announcement (binary) 

chicken: Reference made to chicken products in recall announcement (binary)

pork: Reference made to pork products in recall announcement (binary) 

###Data from YellowPages API (term=businessName)
city

state 

street 

zip 

lat 

long 
      
