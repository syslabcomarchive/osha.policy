#!/opt/python/python-2.4/bin/python
import sys

print "x"
fh = open(sys.argv[1], 'r')
data = fh.read()
fh.close()

cnt=0
ids = list()
lines = data.split('\n')
for li in lines:
  if li.find('termIdentifier')>-1:
    id = li.replace('<termIdentifier>', '').replace('</termIdentifier>', '').strip()
    if id in ids:
      print "duplicate:", id
      cnt +=1
    ids.append(id)


print len(lines)
print cnt

