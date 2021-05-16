from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import pywhatkit
import time
import datetime
import requests
import smtplib
import yaml

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.ticker import PercentFormatter

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

#For Google Spreedsheets authorization
scope =["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Crypto-Tracker").sheet1  # Open the spreadhseet

#This plots the graph and saves it
def graph_plot(bit_per_1h):
    data = sheet.get_all_records()  # Get a list of all records

    x=[]
    y=[]

    j=1
    for i in data:
        x.append(j)
        j=j+1
        y.append(i['Price-INR'])
        #print(i['Price-INR'])

    print(x)
    print(y)

    plt.plot(x, y)
    plt.ticklabel_format(style='plain')
    # naming the x axis
    plt.xlabel('Data points')
    # naming the y axis
    plt.ylabel('INR-Rupees')
    
    # giving a title to my graph
    plt.title('Bitcoin graph in INR')
    plt.savefig(r'D:\SEM-4\Python Programming\Mini-Proj\Crypto-Tracker-App\foo.png')
    
    # function to show the plot
    #plt.show()

    #As we got the graph, now email it.
    send_mail_image(bit_per_1h)

    pass

#For getting the available row in google sheets
def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list)+1)

#Send email to the users
def send_mail_image(bit_per_1h):
    # Define these once; use them twice!
    strFrom = 'eyrc.vb.1084@gmail.com'
    #strTo = 'eyrc.vb.1084@gmail.com'


    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    if bit_per_1h<0:
        msgRoot['Subject'] = 'BTC - Bitcoin Alert droped by ' + str(bit_per_1h)
    else:
        msgRoot['Subject'] = 'BTC - Bitcoin Alert increased by ' + str(bit_per_1h)
    msgRoot['From'] = strFrom
    #msgRoot['To'] = strTo
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText('<b>The bitcoin prices are changing.</b><br><img src="cid:image1"><br>To the MOOON!', 'html')
    msgAlternative.attach(msgText)

    # This example assumes the image is in the current directory
    fp = open(r'D:\SEM-4\Python Programming\Mini-Proj\Crypto-Tracker-App\foo.png', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    # Send the email (this example assumes SMTP authentication is required)
    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp.login(os.environ.get('EMAIL_ID'), os.environ.get('EMAIL_ID_PASSWORD'))

    #Get the user email IDS.
    my_file = open(r'D:\SEM-4\Python Programming\Mini-Proj\Crypto-Tracker-App\emails.txt')
    my_file.seek(0)
    words = my_file.read().split()

    #Sent email to the users.
    for i in words:
        smtp.sendmail(os.environ.get('EMAIL_ID'),i,msgRoot.as_string())
        print("Sent ! ")

    smtp.quit()

    pass


#Get the bitcoin value.
def get_bit():
    '''
    - It parses the Google Sheets link from the yaml file.
    - Gets the json data from the API and parses it.
    - Sends the data to the Google Sheets.
    - Sends Email and Whatsapp message.

    Args:
        url_sheets (str) :  Google Sheets API link.
        response (str) :    Gets the data from the CoinMarketCap API.
        bitObj (json)  :    Converts the data into json format.
        
        bit_price (double):     INR value of the bitcoin.
        bit_per_1h (double):    The percentage change in one hour.  
        bit_per_24h(double):    The percentage change in 24 hour.  
        bit_per_7d(double):     The percentage change in 7 days.  
        bit_per_30d(double):    The percentage change in 30 days.

        message (str) : The string of message to be sent.
        param (dictionary) :    The dictionary of key and value pairs to be sent to update the Google Sheets.
        now (tuple) :   It contains time.
        current_hour (int) :    Time in hours.
        current_min  (int) :    Time in minutes.
        threshold_change (int): The variable to assign the change value.  

    '''
    #URL and header files to get the response from the API
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'symbol':'BTC',
        'convert':'INR'
    }
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': os.environ.get('CRYPTO_API_KEY'),
    }
    session = Session()
    session.headers.update(headers)
    

    try:
        response = session.get(url, params=parameters)
        parseData = json.dumps(response.json())
        bitObj = json.loads(parseData)
        bit_price = bitObj['data']['BTC']['quote']['INR']['price']
        bit_per_1h = bitObj['data']['BTC']['quote']['INR']['percent_change_1h']
        bit_per_24h = bitObj['data']['BTC']['quote']['INR']['percent_change_24h']
        bit_per_7d = bitObj['data']['BTC']['quote']['INR']['percent_change_7d']
        bit_per_30d = bitObj['data']['BTC']['quote']['INR']['percent_change_30d']
        
        time = datetime.datetime.now()

        print(bit_price)
        print(bit_per_1h)
        print(bit_per_24h)
        print(bit_per_7d)
        print(bit_per_30d)

        #The message to be send using WhatsApp.
        message = "The price moved by : "+str(bit_per_1h)+" %"

        #Gets us the next available row in sheets
        next_row = int(next_available_row(sheet))

        #Insert the following values in that available row
        #For storing all values in the sheets for graph.
        insertRow = [str(time),bit_price,bit_per_1h,bit_per_24h,bit_per_7d,bit_per_30d]
        sheet.insert_row(insertRow,next_row)


        #Time required to send the WhatsApp message
        now = datetime.datetime.now()
        current_hour = int(now.strftime("%H"))
        current_min = int(now.strftime("%M")) + 2

        #The percent change required to trigger the user.
        threshold_change = 0.1
        
        #just for testing purpose
        graph_plot(bit_per_1h)
        pywhatkit.sendwhatmsg(os.environ.get('PHONE_NUMBER'),message,current_hour,current_min)

        #if the change is more than 0.1 then send email and whatsapp message.
        # if abs(bit_per_1h) > threshold_change:
        #     graph_plot(bit_per_1h)
        #     pywhatkit.sendwhatmsg(os.environ.get('PHONE_NUMBER'),message,current_hour,current_min)
            
            
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

get_bit()

# while(True):
#     get_bit()
#     time.sleep(60*60)