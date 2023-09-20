from bs4 import BeautifulSoup
import imaplib, email, yaml, urllib, time, calendar
from datetime import date
import urllib.request
#############################################################
#This is more of a spaghetti code and is very unoptimized
#This also very specific to what I was trying to do here
#############################################################


#Find emails from <service@litestaff.com> or with header Exquisite Staffing LLC - New jobs available
#have bot find where the the date, call time, and location of the event is in the email and store it
#have bot find where the accept link is in the email
#have a database that stores what has already been accepted
#accept emails as they come in
#check first if there is already is an event booked for that day and time
#      (split into morning and afternoon events)
#if an event is already booked move on the next email



EventList = [] #list of all events
AcceptedEventList = [] #list of all accepted jobs
DeniedEventList = [] #list of all denied jobs
FilledEventList = [] #list of events that could not be booked



class EventInfo:
    def __init__(self,  date, time, afternoon, location, acceptURL, viewed, accepted):
        self.date = date
        self.time = time
        self.afternoon = afternoon
        self.location = location
        self.acceptURL = acceptURL
        self.viewed = viewed
        self.accepted = accepted


# Uses Accept URL link to accept the job offer if not already accepted
def ClickURL(index):
    webUrl  = urllib.request.urlopen(EventList[index].acceptURL)
    #print(EventList[index].acceptURL)
    print ("result code: " + str(webUrl.getcode()))
    WebData = str(webUrl.read())
    #print (WebData)
    FinalLinkIndexEnd = WebData.find("Accept job")
    #print(FinalLinkIndexEnd)
    if FinalLinkIndexEnd != -1:
        FinalLinkIndexStart = WebData.find("href=")+7
        #print(FinalLinkIndexStart)
        FinalLinkURL = WebData[FinalLinkIndexStart:FinalLinkIndexEnd-3]
        #print(FinalLinkURL)
        OpenFinalLink = urllib.request.urlopen(FinalLinkURL)
        print("Job Booked")
        print("result code: " + str(OpenFinalLink.getcode()))
    else:
        print("Already Accepted or No Longer Available")


def FindJobInfo(body_txt):
    # find location, date, and time, and accept link

    EVdateINDEX = body_txt.find("Date:")
    EVlocationINDEX = body_txt.find("Location:")
    EVtimeINDEX = body_txt.find("Calltime:")
    EVjobcodeINDEX = body_txt.find("Job code:")
    AcceptINDEXstart = body_txt.find("<br/><a href='")
    AcceptINDEXend = body_txt.find("'>Accept")

    EVdate = body_txt[EVdateINDEX + 9:EVlocationINDEX - 8]
    EVlocation = body_txt[EVlocationINDEX + 13:EVtimeINDEX - 8]
    EVtime = body_txt[EVtimeINDEX + 13:EVjobcodeINDEX - 12]
    AcceptLink = body_txt[AcceptINDEXstart + 14:AcceptINDEXend]

    SubIndexStart = 5
    DateSubIndexEnd = EVdate.find("'>")
    LocationSubIndexEnd = EVlocation.find("'>")
    TimeSubIndexEnd = EVtime.find("'>")

    EVdateF = EVdate[SubIndexStart:DateSubIndexEnd]
    EVtimeF = EVtime[SubIndexStart:TimeSubIndexEnd]
    EVlocationF = EVlocation[SubIndexStart:LocationSubIndexEnd]

    IsLater = EVtimeF.find("pm")
    IsNoon = True
    if IsLater == -1:
        IsNoon = False

    viewed = False
    accepted = False

    EventList.append(EventInfo(EVdateF, EVtimeF, IsNoon, EVlocationF, AcceptLink, viewed, accepted))



reservedDaysList = ["Wednesday, May 11th", "Friday, May 12th"]
MoreDays = 'y'
def NoWorkDays():
    while MoreDays == 'y':
        DayToReserve = input("Enter day you want to reserve (DoW, Month ddst): ")
        #DayOfWeek = calendar.day_name[DayToReserve.weekday()]
        #DtRFinalFormat = DayOfWeek + DayToReserve[5:4]
        reservedDaysList.append(DayToReserve)

        MoreDays = input("Do you need to reserve more days? (y/n) ")


def Login():
    with open("creds.yaml") as f:
        content = f.read()

    my_creds = yaml.load(content, Loader=yaml.FullLoader)

    #load username and psw from yaml file
    user, psw = my_creds["user"], my_creds["password"]

    #URL for IMAP connection
    imap_url = 'imap.gmail.com'

    #connection with GMAIL using SSL
    my_mail = imaplib.IMAP4_SSL(imap_url)

    #login using credentials
    my_mail.login(user, psw)

    #select inbox to fetch messages
    my_mail.select('Inbox')

    return my_mail

def getEmails(my_mail):

    #define Key and Value for email search
    key = "FROM"
    value = 'service@litestaff.com'
    _, data = my_mail.search(None, key, value) #search for email with a specific key

    mail_id_list = data[0].split()#IDs of all emails that we want to fetch

    msgs = [] #empty list to capture all messages
    #iterate through messages and extract data into msgs list
    for num in mail_id_list:
        typ, data = my_mail.fetch(num, 'RFC822')
        msgs.append(data)

    #extracts data from each email message
    for msg in msgs[::-1]:
        for response_part in msg:
            if type(response_part) is tuple:
                my_msg=email.message_from_bytes((response_part[1]))
                if (my_msg['subject'] != "Exquisite Staffing LLC - New jobs available"):
                    break
                # print("____________________________________________")
                # print("subj:", my_msg['subject'])
                # print("from:", my_msg['from'])
                # print("body:")
                for part in my_msg.walk():
                    #print (part.get_content_type())
                    if  (part.get_content_type()=='text/html') :
                        body_txt = part.get_payload()#.__str__().replace('\n', '').replace('\r', '').replace('=','')
                        #print (body_txt) print each email
                        FindJobInfo(body_txt)

def ScheduleEvents():
    # make it check the most recent 15
    # check the oldest first and accept it
    # check the succeeding one and check if the date is the same
    # if not then book
    # if it is, check location, prioritize 42nd st
    # else, check times, and if they are at different times of days accept
    # to accept click on AcceptURL
    # check if the webpage says already accepted
    # if it does make job as accepted and close page and go to next
    # else click the accept link
    # mark as accepted or skipped
    i = 30

    while i > 0:
        j = i + 1
        i -= 1
        if EventList[i].viewed:
            continue
        while j < 30:
            if (EventList[i].date == EventList[j].date) and \
                    not (EventList[i].afternoon ^ EventList[j].afternoon) \
                    or (EventList[i].date == "Thursday, May 11th") \
                    or (EventList[i].date == "Friday, May 12th"):
                EventList[i].viewed = True
                print(EventList[i].date, EventList[i].time, EventList[i].location, "Denied")
                DeniedEventList.append(EventList[i])
                break
            j += 1
        else:
            EventList[i].viewed = True
            EventList[i].accepted = True
            ClickURL(i)
            print(EventList[i].date, EventList[i].time, EventList[i].location, "Accepted")
            AcceptedEventList.append(EventList[i])

#initial fetch
iteration = 0

# main loop
while(True):

    iteration += 1

    my_mail = Login()
    getEmails(my_mail)

    for obj in EventList:
        print(obj.date, obj.time, obj.afternoon, obj.location, obj.acceptURL, obj.viewed, obj.accepted, sep=' ')

    ScheduleEvents()

    EventList.clear()
    print(iteration)
    time.sleep(900) #wait 15 minutes

    #TODO: have a system to make sure it doesnt book for certain days or integrate it with my schedule
    #TODO: Make the refresh system not clear the entire EventList and instead only clear old events
    #TODO: Iterate though EventList and only try booking events that have been filled up and new events while not booking for events on days that conflict with my schedule