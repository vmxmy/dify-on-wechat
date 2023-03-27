
"""
google voice service
"""

import time
import speech_recognition
import pyttsx3
from gtts import gTTS
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice


class GoogleVoice(Voice):
    recognizer = speech_recognition.Recognizer()
    engine = pyttsx3.init()

    def __init__(self):
        # 语速
        self.engine.setProperty('rate', 125)
        # 音量
        self.engine.setProperty('volume', 1.0)
        # 0为男声，1为女声
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)

    def voiceToText(self, voice_file):
        # new_file = voice_file.replace('.mp3', '.wav')
        # subprocess.call('ffmpeg -i ' + voice_file +
        #                 ' -acodec pcm_s16le -ac 1 -ar 16000 ' + new_file, shell=True)
        with speech_recognition.AudioFile(voice_file) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio, language='zh-CN')
            logger.info(
                '[Google] voiceToText text={} voice file name={}'.format(text, voice_file))
            reply = Reply(ReplyType.TEXT, text)
        except speech_recognition.UnknownValueError:
            reply = Reply(ReplyType.ERROR, "抱歉，我听不懂")
        except speech_recognition.RequestError as e:
            reply = Reply(ReplyType.ERROR, "抱歉，无法连接到 Google 语音识别服务；{0}".format(e))
        finally:
            return reply
    def textToVoice(self, text):
        try:
            mp3File = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
            # self.engine.save_to_file(text, textFile)
            # self.engine.runAndWait()
            tts = gTTS(text=text, lang='zh')
            tts.save(mp3File)            
            logger.info(
                '[Google] textToVoice text={} voice file name={}'.format(text, mp3File))
            reply = Reply(ReplyType.VOICE, mp3File)
        except Exception as e:
            reply = Reply(ReplyType.ERROR, str(e))
        finally:
            return reply
