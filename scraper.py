import cStringIO
import re
import scraperwiki 
import string 
import sys 
import vanity 
from datetime import datetime, date, timedelta

pypi_pkg = 'python-ostinato'

# bootstrap code - start
releases = [ 
    {file: 'python-ostinato-0.6b1.tar.gz', date: '2014-07-08'},
    {file: 'python-ostinato-0.6.tar.gz', date: '2014-07-08'},
    {file: 'python-ostinato-0.7.tgz', date: '2015-06-09'},
    {file: 'python-ostinato-0.7.1.tar.gz', date: '2015-06-16'}
]

for r in releases:
    print r[file], r[date]
    scraperwiki.sqlite.save(unique_keys=['Date'], 
            data={'Date': r[date], string.replace(r[file], '.', '_'): 0}, 
            table_name='data')
# bootstrap code - ends

#
# use vanity to get cumulative download count for each version
#

# temporarily redirect stdout and argv before calling vanity
stream = cStringIO.StringIO()
stdout_ = sys.stdout
sys.stdout = stream
argv_ = sys.argv
sys.argv = ['vanity', pypi_pkg]

count = 1
while count <= 3:
    try:
        sys.stderr.write('vanity try %d ...\n' % (count))
        vanity.vanity()
        break
    except Exception as e:
        sys.stderr.write(e)
        count = count + 1
        continue

# restore stdout and stdout
sys.argv = argv_
sys.stdout = stdout_

doc = stream.getvalue()
downloads = re.split('\n', doc)
#print downloads

data = {'Date':date.today(), 'Timestamp':datetime.utcnow()}
for d in downloads:
    d = string.strip(d)
    m = re.match(r'python-ostinato-', d)
    if m == None:
        continue
    dl = re.split(r'[ \t]+', d)
    #print dl
    filename = string.replace(dl[0], '.', '_')
    count = dl[2]
    data[filename] = count
print data

#
# retrieve yesterday's cumulative download count and subtract from today's to get the day's download count
#
diff_data = {}
try:
    last_data_list = scraperwiki.sqlite.select("* from data where Date=(select max(Date) from data where Date < '" + date.today().isoformat() + "')")
    last_data = last_data_list[0]
    print last_data
    diff_data['Date'] = date.today()
    for k,v in data.iteritems():
        if (k == 'Date' or k == 'Timestamp'):
            continue;
        last_v = last_data.get(k, '0')
        if last_v == None:
            last_v = 0
        diff_data[k] = int(v) - int(last_v)
    print diff_data
except Exception as e:
    print str(e) 

#
# save to datastore
#
scraperwiki.sqlite.save(unique_keys=['Date'], data=data) 
if (len(diff_data)):
    scraperwiki.sqlite.save(unique_keys=['Date'], data=diff_data, table_name='downloads')
