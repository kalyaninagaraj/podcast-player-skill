from mycroft import MycroftSkill, intent_handler, intent_file_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.util.parse import match_one
from datetime import datetime, timedelta
import feedparser
import requests

"""podcast_dict = {
    'revisionist history': 'https://feeds.megaphone.fm/revisionisthistory',
    'planet money': 'https://www.npr.org/rss/podcast.php?id=510289',
    'wait wait': 'https://www.npr.org/rss/podcast.php?id=344098539',
    'seen unseed': 'http://seenunseen.ivm.libsynpro.com',
    'ny times daily': 'https://rss.art19.com/the-daily',
    'intelligence squared': 'https://rss.acast.com/intelligencesquared'
    'all india radio regional': 'http://newsonair.nic.in/Regional_Audio_rss.aspx',
    'all india radio national': 'http://newsonair.nic.in/NSD_Audio_rss.aspx'
}
"""

class PodcastPlayer(CommonPlaySkill):
    #def __init__(self):
    #    MycroftSkill.__init__(self)

    def CPS_match_query_phrase(self, phrase):
        """ This method responds whether the skill can play the input phrase.
            The method is invoked by the PlayBackControlSkill.
            Returns: tuple (matched phrase(str),
                            match level(CPSMatchLevel),
                            optional data(dict))
                     or None if no match was found.
        """
        # Form a dictionary of podcast feeds
        podcast_info = [ (self.settings["podcast"+str(i)], self.settings["feed"+str(i)]) for i in range(1, 6)]
        podcast_dicts = dict((p, f) for p,f in podcast_info)
        # Get match and confidence
        match, confidence = match_one(phrase, podcast_dicts)
        # If the confidence is high enough return a match
        if confidence > 0.8:
            return (match, CPSMatchLevel.TITLE, {"track": match})
        else:
            return None

    def CPS_start(self, phrase, data):
        """ Starts playback.
            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        rss_parsed = feedparser.parse(data["track"].strip()) # strip uri of leading and trailing spaces before parsing
        if 'all india radio' not in phrase:
            encl = rss_parsed.entries[0].enclosures[0] # first enclosure of first entry (item)
            self.speak_dialog('playing.podcast', {'podcast_title': phrase})
            link = requests.get(encl.href) # find the redirected url from encl.href
        else:
            dt_now = datetime.now()
            bd = timedelta(hours=24)
            if 'regional' in phrase:
                for e in rss_parsed.entries:
                    if 'Pune-Marathi' in e.title:
                        bt = datetime.strptime(e.published+e.bulletintime, "%b %d, %Y%H%M")
                        if bd > dt_now - bt:
                            bd = dt_now - bt
                            link = requests.get(e.enclosures[0].href)
                            break
            elif 'national' in phrase:
                for e in rss_parsed.entries:
                    if e.author == 'English' and (('Morning' in e.title) or ('Midday'in e.title) or ('Nine'in e.title)):
                        bt = datetime.strptime(e.published+e.bulletintime, "%b %d, %Y%H%M")
                        if bd > dt_now - bt:
                            bd = dt_now - bt
                            link = requests.get(e.enclosures[0].href)
                            break
            self.speak('Playing the latest news bulletin from All India Radio')
        url = link.url.replace('https', 'http', 1) # replace https with http in red_url.url
        self.CPS_play(url)


def create_skill():
    return PodcastPlayer()
