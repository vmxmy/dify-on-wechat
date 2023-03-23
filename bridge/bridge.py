from bridge.context import Context
from bridge.reply import Reply
from common.log import logger
from bot import bot_factory
from common.singleton import singleton
from voice import voice_factory
from config import conf
from common import const


@singleton
class Bridge(object):
    def __init__(self):
        self.btype={
            "chat": "chatGPT",
            "voice_to_text": "openai",
            "text_to_voice": "baidu"
        }
        self.bots={}


    def get_bot(self,typename):
        if self.bots.get(typename) is None:
            logger.info("create bot {} for {}".format(self.btype[typename],typename))
            if typename == "text_to_voice":
                self.bots[typename] = voice_factory.create_voice(self.btype[typename])
            elif typename == "voice_to_text":
                self.bots[typename] = voice_factory.create_voice(self.btype[typename])
            elif typename == "chat":
                self.bots[typename] = bot_factory.create_bot(self.btype[typename])
        return self.bots[typename]
    
    def get_bot_type(self,typename):
        return self.btype[typename]


    def fetch_reply_content(self, query, context : Context) -> Reply:
        bot_type = const.CHATGPT
        model_type = conf().get("model")
        if model_type in ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]:
            bot_type = const.CHATGPT
        elif model_type in ["text-davinci-003"]:
            bot_type = const.OPEN_AI
        return bot_factory.create_bot(bot_type).reply(query, context)


    def fetch_voice_to_text(self, voiceFile) -> Reply:
        return self.get_bot("voice_to_text").voiceToText(voiceFile)

    def fetch_text_to_voice(self, text) -> Reply:
        return self.get_bot("text_to_voice").textToVoice(text)

