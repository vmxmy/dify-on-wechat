from common.expired_dict import ExpiredDict
from common.log import logger
from config import conf

class Session(object):
    def __init__(self, session_id, system_prompt=None):
        self.session_id = session_id
        if system_prompt is None:
            self.system_prompt = conf().get("character_desc", "")
        else:
            self.system_prompt = system_prompt

    # 重置会话
    def reset(self):
        raise NotImplementedError

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset()

    def add_query(self, query):
        raise NotImplementedError

    def add_reply(self, reply):
        raise NotImplementedError
    
    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        raise NotImplementedError



class SessionManager(object):
    def __init__(self, sessioncls, **session_args):
        if conf().get('expires_in_seconds'):
            sessions = ExpiredDict(conf().get('expires_in_seconds'))
        else:
            sessions = dict()
        self.sessions = sessions
        self.sessioncls = sessioncls
        self.session_args = session_args

    def build_session(self, session_id, system_prompt=None):
        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id, system_prompt, **self.session_args)
        elif system_prompt is not None: # 如果有新的system_prompt，更新并重置session
            self.sessions[session_id].set_system_prompt(system_prompt)
        session = self.sessions[session_id]
        return session
    
    def session_query(self, query, session_id):
        session = self.build_session(session_id)
        session.add_query(query)
        print(session.messages)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug("prompt tokens used={}".format(total_tokens))
        except Exception as e:
            logger.debug("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session

    def session_reply(self, reply, session_id, total_tokens = None):
        session = self.build_session(session_id)
        session.add_reply(reply)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.debug("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session

    def clear_session(self, session_id):
        del(self.sessions[session_id])

    def clear_all_session(self):
        self.sessions.clear()
