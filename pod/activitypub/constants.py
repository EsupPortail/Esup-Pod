AP_REQUESTS_TIMEOUT = 60
AP_DEFAULT_CONTEXT = [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
    {"RsaSignature2017": "https://w3id.org/security#RsaSignature2017"},
]
AP_PT_VIDEO_CONTEXT = {
    "pt": "https://joinpeertube.org/ns#",
    "sc": "http://schema.org/",
    "Hashtag": "as:Hashtag",
    "uuid": "sc:identifier",
    "category": "sc:category",
    "licence": "sc:license",
    "subtitleLanguage": "sc:subtitleLanguage",
    "sensitive": "as:sensitive",
    "language": "sc:inLanguage",
    "identifier": "sc:identifier",
    "isLiveBroadcast": "sc:isLiveBroadcast",
    "liveSaveReplay": {"@type": "sc:Boolean", "@id": "pt:liveSaveReplay"},
    "permanentLive": {"@type": "sc:Boolean", "@id": "pt:permanentLive"},
    "latencyMode": {"@type": "sc:Number", "@id": "pt:latencyMode"},
    "Infohash": "pt:Infohash",
    "tileWidth": {"@type": "sc:Number", "@id": "pt:tileWidth"},
    "tileHeight": {"@type": "sc:Number", "@id": "pt:tileHeight"},
    "tileDuration": {"@type": "sc:Number", "@id": "pt:tileDuration"},
    "originallyPublishedAt": "sc:datePublished",
    "uploadDate": "sc:uploadDate",
    "hasParts": "sc:hasParts",
    "views": {"@type": "sc:Number", "@id": "pt:views"},
    "state": {"@type": "sc:Number", "@id": "pt:state"},
    "size": {"@type": "sc:Number", "@id": "pt:size"},
    "fps": {"@type": "sc:Number", "@id": "pt:fps"},
    "commentsEnabled": {"@type": "sc:Boolean", "@id": "pt:commentsEnabled"},
    "downloadEnabled": {"@type": "sc:Boolean", "@id": "pt:downloadEnabled"},
    "waitTranscoding": {"@type": "sc:Boolean", "@id": "pt:waitTranscoding"},
    "support": {"@type": "sc:Text", "@id": "pt:support"},
    "likes": {"@id": "as:likes", "@type": "@id"},
    "dislikes": {"@id": "as:dislikes", "@type": "@id"},
    "shares": {"@id": "as:shares", "@type": "@id"},
    "comments": {"@id": "as:comments", "@type": "@id"},
}
AP_PT_CHANNEL_CONTEXT = (
    {
        "pt": "https://joinpeertube.org/ns#",
        "sc": "http://schema.org/",
        "playlists": {"@id": "pt:playlists", "@type": "@id"},
        "support": {"@type": "sc:Text", "@id": "pt:support"},
        "icons": "as:icon",
    },
)
AP_PT_CHAPTERS_CONTEXT = {
    "pt": "https://joinpeertube.org/ns#",
    "sc": "http://schema.org/",
    "name": "sc:name",
    "hasPart": "sc:hasPart",
    "endOffset": "sc:endOffset",
    "startOffset": "sc:startOffset",
}

INSTANCE_ACTOR_ID = "pod"
BASE_HEADERS = {"Accept": "application/activity+json, application/ld+json"}


# https://creativecommons.org/licenses/?lang=en
AP_LICENSE_MAPPING = {
    1: "by",
    2: "by-sa",
    3: "by-nd",
    4: "by-nc",
    5: "by-nc-sa",
    6: "by-nc-nd",
    7: "zero",
}
