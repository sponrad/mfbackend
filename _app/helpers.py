import os, datetime, random, string, urllib, math

def get_lat_long(query):
    query = urllib.quote_plus(query)
    url ="http://dev.virtualearth.net/REST/v1/Locations?query=" + query + "&key=" + BINGKEY
    jsondata = simplejson.loads(urllib.urlopen(url).read())

    #only want one result
    if len(jsondata['resourceSets'][0]['resources']) == 1: 
        return jsondata['resourceSets'][0]['resources'][0]['point']['coordinates']
    else:
        return None

def get_lat_long_city_state_address(query):
    query = urllib.quote_plus(query)
    url ="http://dev.virtualearth.net/REST/v1/Locations?query=" + query + "&key=" + BINGKEY
    jsondata = simplejson.loads(urllib.urlopen(url).read())

    #check results exist, take first result
    if len(jsondata['resourceSets'][0]['resources']) > 0: 
        values = jsondata['resourceSets'][0]['resources'][0]['point']['coordinates']
        values.append(jsondata['resourceSets'][0]['resources'][0]['address']['locality'])  #CITY
        values.append(jsondata['resourceSets'][0]['resources'][0]['address']['adminDistrict'])  #STATE
        values.append(jsondata['resourceSets'][0]['resources'][0]['address']['addressLine']) #ADDRESS
        return values
    else:
        return None

def get_location_string(address = None, city = None, state = None, zipcode = None):
    string = ""
    if address: string = ",".join((string, address))
    if city: string = ",".join((string, city))
    if state: string = ",".join((string, state))
    if zipcode: string = ",".join((string, zipcode))
    return string

def queryfunctionfactory(min_price, max_price, min_sqft, max_sqft):
    #a list generator that will filter
    # [p for p in listings if queryfunction(p.office_sq_ft, p.price)]
    def queryfunction(price, sqft):
        if min_price:
            if price < min_price: return False
        if max_price:
            if price > max_price: return False
        if min_sqft:
            if sqft < min_sqft: return False
        if max_sqft:
            if sqft > max_sqft: return False
        return True
    return queryfunction
