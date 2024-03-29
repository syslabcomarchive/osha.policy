## Script (Python) "publications_by_type"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=keywords=[]
##title=returns matching publications ordered by type
##
# This script makes a catalog query for publications on a given area of interest
# and structures the result by publication type
from Products.AdvancedQuery import In, Eq
if keywords==[]:
  keywords = context.REQUEST.get('keywords', [])

pc = context.portal_catalog
if hasattr(pc, 'getZCatalog'):
  pc = pc.getZCatalog()



TQ = Eq('portal_type', 'PublicationFolder') & Eq('review_state', 'published') 
TYPES = pc.evalAdvancedQuery(TQ)

PQ = Eq('portal_type', 'Publication') & In('Subject', keywords) & Eq('review_state', 'published') 
PUBS = pc.evalAdvancedQuery(PQ, (('effective','desc'),) )

PubByPath = {}
PrefixList = []
TypesByPath = {}

for TYPE in TYPES:
  P = TYPE.getPath()
  TypesByPath[P] = TYPE
  if P[-1] != "/":
    P = P+"/"
  PrefixList.append(P)




for PUB in PUBS:
  pubpath = PUB.getPath()
  for P in PrefixList:
    if pubpath.find(P) == 0:
      arr = PubByPath.get(P, [])
      arr.append(PUB)
      PubByPath[P] = arr

return TypesByPath, PubByPath
