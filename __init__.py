from mycroft import MycroftSkill, intent_file_handler


class PodcastPlayer(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('player.podcast.intent')
    def handle_player_podcast(self, message):
        podcast_title = ''

        self.speak_dialog('player.podcast', data={
            'podcast_title': podcast_title
        })


def create_skill():
    return PodcastPlayer()

