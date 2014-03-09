import time
import sys
import datetime
import Queue
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
from threading import Thread
from cgi import parse_qs
from urlparse import urlparse

exitFlag = 0
exitSave = 0
workQueue = Queue.Queue()
outQueue = Queue.Queue()
threads = []
zipcode_filename='zipcodes.txt'
threads_max = 15
timeout = 10
lineups = {}

def get_lineup( href ):
    return parse_qs( urlparse( href ).query )['lineupId'][0]

def get_ch_number( href ):
    return parse_qs( urlparse( href ).query )['channel'][0]

def get_lineups( zipcode ):
    baseurl = 'http://tvlistings.zap2it.com'
    url = baseurl + '/tvlistings/ZBChooseProvider.do?method=getProviders'
    values = {'zipcode' : zipcode}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req, None, timeout)
    html = response.read()
    lineups = []
    ret_value = {}
    soup = BeautifulSoup(html)
    result = soup.findAll('div', {'class': 'zc-provider-list'})
    for div in result:
        links = div.findAll('a')
        for a in links:
            channel_name = a.contents[0].strip().replace('&amp;','&')
            lineups.append( get_lineup( a['href'] ) )
            print channel_name
            lineups.sort()
            ret_value['zipcode'] = zipcode
            ret_value['name'] = channel_name
            ret_value['lineups'] = lineups
    return ret_value

def get_cable_info( lineup ):
    baseurl = "http://tvlistings.zap2it.com/tvlistings/ZCGrid.do?method=decideFwdForLineup&lineupId="
    href = baseurl + lineup
    req_ch= urllib2.Request(href)
    response_ch= urllib2.urlopen(req_ch, None, timeout)
    html_ch= response_ch.read()
    soup_ch= BeautifulSoup(html_ch)
    grid = soup_ch.findAll('div', {'class': 'zc-grid'})
    channels = []
    ret_value = {}
    for grid_info in grid:
        result_ch= grid_info.findAll('table', {'class': 'zc-row '})
        for ch_info in result_ch:
            ch_data = ch_info.findAll('td', {'class': 'zc-st'})
            for ch_item in ch_data:
                ch_spans = ch_item.findAll('span', {'class': 'zc-st-c'})
                for ch_span in ch_spans:
                    ch_link = ch_span.findAll('a', {'class': 'zc-st-a'})
                    for ch_stuff in ch_link:
                        ch_url = ch_stuff['href']
                        ch_number = get_ch_number( ch_url )
                        ch_name   = ch_stuff.contents[0].strip()
                        channels.append( ch_number + "-" + ch_name )
    ret_value['channels'] = channels
    ret_value['lineup'] = lineup
    return ret_value

def process_data():
    while not exitFlag:
        if not workQueue.empty():
            data = workQueue.get()
            lineups = get_lineups( data )
            if lineups:
                outQueue.put( lineups )
            workQueue.task_done()
        time.sleep( 0.001 )

def process_lineups():
    while not exitFlag:
        if not workQueue.empty():
            lineup = workQueue.get()
            #channels = get_cable_info( lineup )
            channels = {'lineup': lineup, 'channels': 'info'}
            if channels:
                outQueue.put( channels )
            workQueue.task_done()
        time.sleep( 0.001 )

def empty_out_queue():
    while not outQueue.empty():
        data = outQueue.get()
        print data['name']
        print data['zipcode']
        for lineup in data['lineups']:
            lineups[ lineup ] = 1
            print lineup

def save_lineups():
    while not exitSave:
        empty_out_queue()
        time.sleep( 0.001 )

def show_progress():
    time_avg=0
    time_delta=time.time()
    speed_avg=1
    smoothing_factor=0.05
    time_avg = 1000
    total=workQueue.unfinished_tasks
    while not exitFlag:
        remaining=workQueue.unfinished_tasks
        current=total-remaining
        percent = current*100/total
        time_delta=time.time()-time_delta
        speed_avg=smoothing_factor*time_delta + (1-smoothing_factor)*speed_avg
        if speed_avg < time_avg:
            time_avg = speed_avg
        time_eta=datetime.timedelta( milliseconds=
                                    (time_avg*remaining*1000) )
        sys.stdout.write("\r%.2f%% estimated %s remaining" %(percent,time_eta))
        sys.stdout.flush()
        time_delta=time.time()
        time.sleep( 0.1 )
    sys.stdout.write("\n")
    sys.stdout.flush()

if __name__ == "__main__":
    zipcodes = open( zipcode_filename ,"rb").readlines()
    for zipcode in zipcodes:
        zipcode = zipcode.strip()
        workQueue.put( zipcode )

    show_thread = Thread(target = show_progress)
    show_thread.start()
    threads.append(show_thread)

    time.sleep( 1 )

    for k in range( threads_max ):
        thread = Thread(target = process_data)
        thread.start()
        threads.append(thread)

    save_thread = Thread(target = save_lineups)
    save_thread.start()
    #threads.append(save_thread)

    while not workQueue.empty():
        time.sleep( 0.1 )
    time.sleep( 0.1 )
    exitFlag = 1
    time.sleep( 0.1 )
    exitSave = 1
    for thread in threads:
        thread.join()
    save_thread.join()

    print "Phase 1 finished"
    print "Starting Phase 2"

    empty_out_queue()

    exit()

    for lineup in lineups:
        workQueue.put( lineup )

    exitFlag = 0

    show_thread = Thread(target = show_progress)
    show_thread.start()
    threads.append(show_thread)

    time.sleep( 1 )

    for k in range( threads_max ):
        thread = Thread(target = process_lineups)
        thread.start()
        threads.append(thread)

    while not workQueue.empty():
        time.sleep( 1 )
    exitFlag = 1

    for thread in threads:
        thread.join()

    print "Phase 2 finished"

    while not outQueue.empty():
        data = outQueue.get()
        print data














    """
    lineups = open('lineups.txt',"rb").readlines()

    for lineup in lineups:
        lineup = lineup.strip()
        print lineup
        get_cable_info( lineup )
        with open("salida.txt", "a") as salida:
            salida.write( info )
    """
