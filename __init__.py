from mycroft import MycroftSkill, intent_handler, intent_file_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.util.parse import match_one
from mycroft.audio import wait_while_speaking
import feedparser
import requests

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
        # Create a dictionary of podcast feeds
        podcast_info = [ (self.settings["podcast"+str(i)], self.settings["feed"+str(i)]) for i in range(1, 6)]
        podcast_dicts = dict((p, f) for p,f in podcast_info)
        # Find matching dictionary value and confidence level of match
        match, confidence = match_one(phrase, podcast_dicts)
        # If confident enough of match, return dictionary value
        if confidence > 0.4:
            return (match, CPSMatchLevel.TITLE, {"track": match})
        else:
            return None

    def CPS_start(self, phrase, data):
        """ Starts playback.
            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        # Get url to episode audio file
        phrase, url = self.handle_season_episode(phrase, data)
        # Call playpodcast
        self.play_podcast(phrase, url)

    def handle_season_episode(self, phrase, data):
        # Strip uri of leading and trailing spaces before parsing
        rss_parsed = feedparser.parse(data["track"].strip())
        if 'itunes_season' in rss_parsed.entries[0].keys() and 'itunes_episode' in rss_parsed.entries[0].keys():
            latest_season = int(rss_parsed.entries[0].itunes_season)
            latest_episode = int(rss_parsed.entries[0].itunes_episode)

            # Look for season and episode in phrase
            # (1) latest episode of 'podcast'  >> latest SEASON, latest EPISODE
            # (2) latest season of 'podcast'   >> latest SEASON, first EPISODE
            # (3) 'podcast'                    >> same as (1)
            # (4) episode x of 'podcast'       >> latest SEASON, EPISODE x
            # (5) season y of 'podcast'        >> SEASON y, first EPISODE
            # (6) season y, episode x of 'podcast' >> SEASON y, EPISODE x
            phrase1 = phrase.split()
            try:
                phrase1.index('season')
            except:
                season = latest_season
            else:
                if phrase1[phrase1.index('season')-1] == 'latest':
                    season = latest_season
                else:
                    season = int(phrase1[phrase1.index('season')+1])
            try:
                phrase1.index('episode')
            except:
                try:
                    phrase1.index('season')
                except:
                    episode = latest_episode
                else:
                    episode = 1
            else:
                if  phrase1[phrase1.index('episode')-1] == 'latest':
                    episode = latest_episode
                else:
                    episode = int(phrase1[phrase1.index('episode')+1])

            # Look under first enclosure of correct entry
            # Get the redirected link from enclosure.href
            # Finally, replace 'https' with 'http'
            url = None
            for e in rss_parsed.entries:
                try:
                    e.itunes_season and e.itunes_episode
                except:
                    False
                else:
                    if season == int(e.itunes_season) and episode == int(e.itunes_episode):
                        url = requests.get(e.enclosures[0].href).url.replace('https', 'http', 1)
                        break
        else:
            if 'of ' in phrase:
                phrase = 'the latest episode of '+phrase.split('of ')[1]
            else:
                phrase = 'the latest episode of '+phrase.split('of ')[0]
            url = requests.get(rss_parsed.entries[0].enclosures[0].href).url.replace('https', 'http', 1)
        return phrase, url


    def play_podcast(self, phrase, url):
        if url is not None:
            self.speak_dialog('playing.podcast', {'phrase': phrase})
            wait_while_speaking()
            self.CPS_play(url)
        else:
            self.speak_dialog('cant.find.episode', {'phrase': phrase})

def create_skill():
    return PodcastPlayer()
