# from django.db import models
from django.utils import timezone
# Create your models here.

__XAPI_VIDEO_VERBS__ = {
    "Initialized": "http://adlnet.gov/expapi/verbs/initialized",
    "Played": "https://w3id.org/xapi/video/verbs/played",
    "Paused": "https://w3id.org/xapi/video/verbs/paused",
    "Seeked": "https://w3id.org/xapi/video/verbs/seeked",
    "Interacted": "http://adlnet.gov/expapi/verbs/interacted",
    "Completed": "http://adlnet.gov/expapi/verbs/completed",
    "Terminated": "http://adlnet.gov/expapi/verbs/terminated",
}

__XAPI_VIDEO_CONTEXT_EXTENSIONS__ = {
    "session-id": "https://w3id.org/xapi/video/extensions/session-id",
    "cc-subtitle-enabled": "https://w3id.org/xapi/video/extensions/cc-subtitle-enabled",
    "cc-subtitle-lang": "https://w3id.org/xapi/video/extensions/cc-subtitle-lang",
    "frame-rate": "https://w3id.org/xapi/video/extensions/frame-rate",
    "full-screen": "https://w3id.org/xapi/video/extensions/full-screen",
    "quality": "https://w3id.org/xapi/video/extensions/quality",
    "screen-size": "https://w3id.org/xapi/video/extensions/screen-size",
    "video-playback-size": "https://w3id.org/xapi/video/extensions/video-playback-size",
    "speed": "https://w3id.org/xapi/video/extensions/speed",
    "track": "https://w3id.org/xapi/video/extensions/track",
    "user-agent": "https://w3id.org/xapi/video/extensions/user-age",
    "volume": "https://w3id.org/xapi/video/extensions/volume",
    "length": "https://w3id.org/xapi/video/extensions/length",
    "completion-threshold": "https://w3id.org/xapi/video/extensions/completion-threshold"
}


class XAPI_Statement():
    timestamp = ""
    id = ""
    actor = None
    verb = None
    object = None
    result = None
    context = None

    def __init__(self, id: str = "") -> None:
        self.id = id
        self.timestamp = str(timezone.now().isoformat())

    def set_actor(self, name: str) -> None:
        self.actor = XAPI_Actor(name)

    def set_verb(self, app: str, action: str):
        if app == "video":
            self.verb = XAPI_Video_Verb(action)
        else:
            self.verb = XAPI_Verb(action)


class XAPI_Actor():
    objectType = "Agent"
    name = ""
    mbox = ""

    def __init__(self, name: str) -> None:
        self.name = name


class XAPI_Verb():
    id = ""
    display = {}

    def __init__(self, action: str) -> None:
        self.display["en-US"] = action


class XAPI_Video_Verb(XAPI_Verb):
    def __init__(self, action: str) -> None:
        print(action, __XAPI_VIDEO_VERBS__.keys())
        if action in __XAPI_VIDEO_VERBS__.keys() :
            self.id = __XAPI_VIDEO_VERBS__[action]
            super().__init__(action)
        else:
            raise KeyError("Action '%s' not found in video verb" % action)


class XAPI_Object():
    definition = {}
    id = ""
    objectType = ""

    def __init__(self, id: str) -> None:
        self.id = id


class XAPI_Video_Object(XAPI_Object):

    def __init__(self, video) -> None:
        self.objectType = "Activity"
        self.definition["type"] = "https://w3id.org/xapi/video/activity-type/video"
        self.definition["name"][video.main_lang] = video.title
        self.definition["description"][video.main_lang] = video.description
        self.id = video.get_full_url()
        super().__init__()


class XAPI_Result():
    extensions = {}


class XAPI_Context():
    registration = ""
    extensions = {}
    contextActivities = {}
    language = ""
    extensions = {}

    def __init__(self) -> None:
        pass


class XAPI_Video_Context(XAPI_Context):
    def __init__(self) -> None:
        super().__init__()
