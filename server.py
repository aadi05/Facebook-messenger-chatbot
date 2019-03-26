from flask import Flask, request, jsonify
import random
import requests
import time
from  geopy.geocoders import Nominatim

output_string = ''

app = Flask(__name__)

numbersapi_url = "http://numbersapi.com/"
iss_location_url = "http://api.open-notify.org/iss-now.json"
people_in_space_url = "http://api.open-notify.org/astros.json"
iss_pass_url = "http://api.open-notify.org/iss-pass.json?"

def get_iss_location():

    geo = Nominatim(user_agent="SpaceBot")
    location = requests.get(iss_location_url).json()
    timestamp = location['timestamp']
    timestamp = time.ctime(timestamp)
    latitude = location['iss_position']['latitude']
    longitude = location['iss_position']['longitude']

    try:
        geolocate = geo.reverse(float(latitude),float(longitude))
        if 'error' in geolocate.raw:
            output_string = 'International Space Station is currently over ------- Latitude: '+latitude+', Longitude: '+longitude+', Timestamp: '+timestamp
        else:
            output_string = 'International Space Station is currently over '+str(geolocate.address)+' ------- Latitude: '+latitude+', Longitude: '+longitude+', Timestamp: '+timestamp
    except:
        print('geolocation service timeout')
        
    return output_string

def people_in_space():

    people = requests.get(people_in_space_url).json()
    number_of_people = people['number']
    people_string = ''
    n = 1

    for dic in people['people']:
        people_string = people_string +' ('+ str(n) +')'+ dic['name']
        n = n + 1

    output_string = 'There are '+str(number_of_people)+' people in space right now. Their names are, '+people_string

    return output_string

def iss_passing_over_location(req):

    geolocator = Nominatim(user_agent="SpaceBot")

    try:
        country_name = req.get('queryResult').get('parameters').get('geo-country-code').get('name')
    except:
        country_name = 'India'

    city_name = req.get('queryResult').get('parameters').get('geo-city')

    if country_name == "":
        country_name = "India"
    if city_name == "":
        city_name = "Mumbai"

    location_found = geolocator.geocode(city_name+','+ country_name)
    latitude = location_found.latitude
    longitude = location_found.longitude

    call_url_for_iss_pass = iss_pass_url+'lat='+str(latitude)+'&lon='+str(longitude)
    result_iss_pass = requests.get(call_url_for_iss_pass).json()
    first_pass_time = result_iss_pass['response'][3]['risetime']
    first_pass_duration = round(result_iss_pass['response'][3]['duration']/60, 2)
    first_pass_time = time.ctime(first_pass_time)

    try:
        second_pass_time = result_iss_pass['response'][4]['risetime']
        second_pass_duration = round(result_iss_pass['response'][4]['duration']/60, 2)
        second_pass_time = time.ctime(second_pass_time)
    except IndexError:
        second_pass_time = '(not found)'
        second_pass_duration = '(not found)'

    output_string = 'International space station will pass over your location on '+str(first_pass_time)+' and on '+str(second_pass_time)+' for the duration of '+str(first_pass_duration)+' and '+str(second_pass_duration)+' minutes.'

    return output_string

def location_imagery():
    loc_image = "https://commons.wikimedia.org/wiki/File:What_Is_URL.jpg"
    return loc_image

@app.route('/getFact', methods=['POST'])
def getFact():
    req = request.get_json()
    intent = req.get("queryResult").get("intent").get("displayName")
    number = req.get("queryResult").get("parameters").get("number")
    qtype = req.get("queryResult").get("parameters").get("type")

    if intent == "numbers":
        if qtype =='random':
            qtype = random.choice(['math','trivia','year'])
        qurl = numbersapi_url + str(int(number)) + "/" + qtype + "?json"
        output_string = requests.get(qurl).json()["text"]

    elif intent == 'iss':
        if req.get('queryResult').get('parameters').get('iss_info') == 'position':
            output_string = get_iss_location()

        elif req.get('queryResult').get('parameters').get('iss_info') == 'people':
            output_string = people_in_space()

        elif req.get('queryResult').get('parameters').get('iss_info') == 'all':
            location_of_iss = get_iss_location()
            ppl_in_space = people_in_space()
            output_string = location_of_iss + ' And ' + ppl_in_space[0].lower() + ppl_in_space[1:]

    elif intent == 'location':
        output_string = iss_passing_over_location(req)

    elif intent == 'space_fact':
        with open('facts.txt','r') as f:
            facts_collected = f.readlines()
        random_fact_num = random.randint(0,99)
        output_string = 'Fact: ' + facts_collected[random_fact_num]
        print(output_string)

    else:
        output_string = "Sorry, I couldn't extract the data you wanted."
        
    return jsonify({"fulfillmentText":output_string})

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
