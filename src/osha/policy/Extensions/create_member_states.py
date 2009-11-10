import logging 
import types

import Acquisition
from OFS.event import ObjectClonedEvent

from zope import component
from zope.event import notify
from zope.lifecycleevent import ObjectCopiedEvent

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.constants import CONTEXT_CATEGORY

from plone.app.portlets import portlets 
from plone.app.portlets.utils import assignment_mapping_from_key

from Products.CMFCore.utils import getToolByName

from p4a.subtyper.interfaces import ISubtyper
from osha.theme import portlets as osha_portlets

log = logging.getLogger('osha.policy/Extensions/create_member_states.py')


COUNTRY_LANGS = {'romania': [('en', u'English'), ('ro', u'Romanian')],
                'united-kingdom': [('en', u'English')],
                'estonia': [('en', u'English'), ('et', u'Estonian')],
                'austria': [('de', u'German')],
                'greece': [('en', u'English'), ('el', u'Greek')],
                'hungary': [('en', u'English'), ('hu', u'Hungarian')],
                'cyprus': [('en', u'English'), ('el', u'Greek')],
                'turkey': [('en', u'English'), ('tr', u'Turkish')],
                'eu-us': [('en', u'English')],
                'mecklenburg-vorpommern': [('de', u'German')],
                'italy': [('en', u'English'), ('it', u'Italian')],
                'portugal': [('en', u'English'), ('pt', u'Portuguese')],
                'lithuania': [('en', u'English'), ('lt', u'Lithuanian')],
                'malta': [('en', u'English')],
                'france': [('fr', u'French')],
                'slovakia': [('en', u'English'), ('sk', u'Slovak')],
                'ireland': [('en', u'English')],
                'thueringen': [('de', u'German')],
                'norway': [('en', u'English'), ('no', u'Norwegian')],
                'luxemburg': [('fr', u'French')],
                'sachsen-anhalt': [('de', u'German')],
                'korea': [('en', u'English'), ('ko', u'Korean')],
                'slovenia': [('en', u'English'), ('sl', u'Slovenian')],
                'germany': [('en', u'English'), ('de', u'German')],
                'bayern': [('de', u'German')],
                'rheinland-pfalz': [('de', u'German')],
                'spain': [('en', u'English'), ('es', u'Spanish')],
                'netherlands': [('nl', u'Dutch'), ('en', u'English')],
                'denmark': [('da', u'Danish'), ('en', u'English')],
                'poland': [('en', u'English'), ('pl', u'Polish')],
                'finland': [('en', u'English'), ('fi', u'Finnish'), ('sv', u'Swedish')],
                'sweden': [('en', u'English')],
                'latvia': [('en', u'English'), ('lv', u'Latvian')],
                'croatia': [('hr', u'Croatian'), ('en', u'English')],
                'uems': [('en', u'English')],
                'switzerland': [('en', u'English'), ('fr', u'French'), ('de', u'German'), ('it', u'Italian')],
                'czech-republic': [('cs', u'Czech'), ('en', u'English')],
                'bulgaria': [('bg', u'Bulgarian'), ('en', u'English')]
                }

MEMBER_STATES = [
    "Bulgaria",
    "Czech Republic",
    "Denmark",
    "Germany",
    "Estonia",
    "Ireland",
    "Greece",
    "Spain",
    "France",
    "Italy",
    "Cyprus",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Hungary",
    "Malta",
    "Netherlands",
    "Austria",
    "Poland",
    "Portugal",
    "Romania",
    "Slovenia",
    "Slovakia",
    "Finland",
    "Sweden",
    "United Kingdom",
    "Iceland",
    "Liechtenstein",
    "Norway",
    "Switzerland",
    "Croatia",
    "The former Yugoslav Republic of Macedonia",
    "Turkey",
    "Albania",
    "Bosnia and Herzegovina",
    "Kosovo under UNSCR 1244/99",
    "Montenegro",
    "Serbia",
    ]


# Unless already present use English(?)
not_present_on_current_site = [
    'luxembourg',
    'iceland',
    'liechtenstein',
    'the-former-yugoslav-republic-of-macedonia',
    'albania',
    'bosnia-and-herzegovina',
    'kosovo-under-unscr-1244/99',
    'montenegro',
    'serbia'
    ]

def run(self):
    """ """
    member_states = self.unrestrictedTraverse('oshnetwork/member-states')
    for country_name in MEMBER_STATES:
        country_folder = _create_country_folder(member_states, country_name)   
        if country_folder is None:
            continue

        _add_language_tool(country_folder, country_name)
        _add_news_folder(country_folder)
        _add_events_folder(country_folder)
        _add_index_html_page(country_folder, country_name)
        _add_portlets(country_folder)

    return 'Finished!'


def _create_country_folder(member_states, country_name):
    log.info('_create_country_folder for %s' % country_name)
    sid = country_name.lower().replace(' ', '-').replace('/', '-')
    try:
        id = member_states.invokeFactory('Folder', sid, title=country_name)
    except BadRequest:
        log.info('Country folder %s already exists!' % country_name)
        return 
        
    country_folder = member_states._getOb(id)
    subtyper = component.getUtility(ISubtyper)
    subtyper.change_type(country_folder, 'slc.subsite.FolderSubsite')
    return country_folder


def _add_language_tool(country_folder, country_name):
    log.info('_add_language_tool for %s' % country_name)
    tool = getToolByName(country_folder, 'portal_languages')
    newob = tool._getCopy(tool)
    newob._setId(tool.id)
    notify(ObjectCopiedEvent(newob, tool))

    country_folder._setOb(tool.id, newob)
    country_folder._objects = country_folder._objects+(dict(meta_type=tool.meta_type, id=tool.id),)

    ltool = country_folder._getOb(tool.id)
    ltool.wl_clearLocks()
    ltool._postCopy(country_folder, op=0)
    ltool.manage_afterClone(ltool)
    notify(ObjectClonedEvent(ltool))

    name = country_name.lower().replace(' ', '-')
    if COUNTRY_LANGS.has_key(name):
        languages = [l[0] for l in COUNTRY_LANGS[name]]
    else:
        languages = ['en']

    if languages:
        if isinstance(languages, tuple):
            languages = list(languages)
        elif isinstance(languages, types.StringType) or isinstance(languages, types.UnicodeType):
            languages = [languages]

        ltool.supported_langs = languages


def _add_news_folder(country_folder):
    log.info('_add_news_folder')
    id = country_folder.invokeFactory('Folder', 'news', title='News')
    news = country_folder._getOb(id)
    _add_news_topic(news)


def _add_events_folder(country_folder):
    log.info('_add_events_folder')
    id = country_folder.invokeFactory('Folder', 'events', title='Events')
    events = country_folder._getOb(id)
    _add_events_topic(events)


def _add_index_html_page(country_folder, country_name):
    log.info('_add_index_html_page for %s' % country_name)
    id = country_folder.invokeFactory('Document', 'index_html', title=country_name)
    page = country_folder._getOb(id)
    
    page.manage_addProperty('layout', '@@oshnetwork-member-view', 'string')
    subtyper = component.getUtility(ISubtyper)
    subtyper.change_type(page, 'annotatedlinks')


def _add_portlets(page):
    log.info('_add_portlets')
    path = "/".join(page.getPhysicalPath()) 
    oshabelow = assignment_mapping_from_key(page, 'osha.belowcontent.portlets', CONTEXT_CATEGORY, path)

    oshabelow[u'news'] = portlets.news.Assignment()
    oshabelow[u'events'] = portlets.events.Assignment()

    rightcolumn_manager = component.getUtility(
                    IPortletManager, 
                    name=u'plone.rightcolumn', 
                    context=page
                    )

    rightcolumn = component.getMultiAdapter(
                            (page, rightcolumn_manager), 
                            IPortletAssignmentMapping, context=page
                            )

    rightcolumn[u'activities'] = osha_portlets.image.Assignment(
                                                            header=u"Agency's Activities",
                                                            image="/en/campaigns/hw2008/campaign/banner/hwp_en.swf",
                                                            )

    rightcolumn[u'links'] = osha_portlets.network_member_links.Assignment()


def _add_news_topic(news):
    log.info('_add_news_topic')
    id = news.invokeFactory('Topic', 'front-page')
    news_topic = news._getOb(id)

    # Add the Topic criteria
    effective_date = news_topic.addCriterion('effective', 'ATFriendlyDateCriteria')
    effective_date.setValue(0) # Set date reference to now

    expiration_date = news_topic.addCriterion('expires', 'ATFriendlyDateCriteria')
    expiration_date.setValue(0) # Set date reference to now

    state = news_topic.addCriterion('review_state', 'ATSimpleStringCriterion')
    state.setValue('published') 

    location = news_topic.addCriterion('path', 'ATRelativePathCriterion')
    location.setRelativePath('..') 

    item_type = news_topic.addCriterion('portal_type', 'ATSimpleStringCriterion')
    item_type.setValue('News Item')


def _add_events_topic(events):
    log.info('_add_events_topic')
    id = events.invokeFactory('Topic', 'front-page')
    events_topic = events._getOb(id)

    # Add the Topic criteria
    item_type = events_topic.addCriterion('portal_type', 'ATSimpleStringCriterion')
    item_type.setValue('Event')

    state = events_topic.addCriterion('review_state', 'ATSimpleStringCriterion')
    state.setValue('published')

    effective_date = events_topic.addCriterion('effective', 'ATFriendlyDateCriteria')
    effective_date.setValue(0) # Set date reference to now

    expiration_date = events_topic.addCriterion('expires', 'ATFriendlyDateCriteria')
    expiration_date.setValue(0) # Set date reference to now

    location = events_topic.addCriterion('path', 'ATRelativePathCriterion')
    location.setRelativePath('..') 


    
