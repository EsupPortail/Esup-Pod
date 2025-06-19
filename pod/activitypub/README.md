# ActivityPub implementation

Pod implements a minimal set of ActivityPub that allows video sharing between Pod instances.
The ActivityPub implementation is also compatible with [PeerTube](https://joinpeertube.org).

## Federation

Here is what happens when two instances, say *Node A* and *Node B* (being either Pod or PeerTube) federate with each other, in a one way federation.

Users are represented by ActivityPub `Person` objects.
Channels are represented by ActivityPub `Group` objects.
The meta account of an instance (being a special account listing all the videos of an instance) is represented by an ActivityPub `Application` object.

### Federation

Federating to another instance means asking the other instance to send notifications for new events, such as a video publication.

- An administrator asks for Node A to federate with Node B
- Node A reaches the [NodeInfo](https://github.com/jhass/nodeinfo/blob/main/PROTOCOL.md) endpoint (`/.well-known/nodeinfo`) on Node B and discover the root application endpoint URL.
- Node A reaches the root application endpoint (for Pod this is `/ap/`) and get the `inbox` URL.
- Node A sends a `Create` activity for a `Follow` object on the Node B root application `inbox`.
- Node B reads the Node A root application endpoint URL in the `Follow` objects, reaches this endpoint and get the Node A root application `inbox` URL.
- Node B creates a `Follower` objects and stores it locally
- Node B sends a `Accept` activity for the `Follower` object on Node A root application enpdoint.
- Later, Node A can send to Node B a `Undo` activity for the `Follow` object to de-federate.

### Video discovery

The video discovery step consists in browsing all the published video of another instance to index them locally.

- Node A reaches the Node B root application `outbox`.
- Node A browse the pages of the `outbox` and look for `Announce` objects about `Videos`
- Node A reaches the `Video` endpoints and store locally the information about the videos.

### Video creation and update sharing

#### Creation

- A user of Node B publishes a `Video`
- Node B sends a `Create` activity for a `Video` on the `inbox` of all its `Followers`, including Node A.
  The owner of the `Create` object is the user who has published it, who is represented by a `Person` object.
- Node B sends several `Announce` activites on the `inbox` of all its `Followers`, including Node A, with the ID of the new video.
  The owners of the `Announce` objects are the user channel, represented by a `Group` object, and the instance global account, represented by an `Application` object.
- Node A reads the information about the new `Video` on Node B video endpoint.

#### Edition

- A user of Node B edits a `Video`
- Node B sends a `Update` activity on the `inbox` of all its `Followers`, including Node A with the ID of the new video, containing the details of the `Video`.

#### Deletion

- A user of Node B deletes a `Video`
- Node B sends a `Delete` activity on the `inbox` of all its `Followers`, including Node A with the ID of the new video.

## Implementation

The ActivityPub implementation tries to replicate the network messages of PeerTube.
There may be things that could have been done differently while still following the ActivityPub specs, but changing the network exchanges would require checking if the PeerTube compatibility is not broken.
This is due to PeerTube having a few undocumented behaviors that are not exactly part of the AP specs.

To achieve compatibility with PeerTube, Pod implements two specifications to sign ActivityPub exchanges.

- [Signing HTTP Messages, draft 12](https://datatracker.ietf.org/doc/html/draft-cavage-http-signatures-12).
  This specification is replaced by [RFC9421](https://www.rfc-editor.org/rfc/rfc9421.html) but PeerTube does not implement the finale spec,
  and instead lurks on the writing of the [ActivityPub and HTTP Signatures](https://swicg.github.io/activitypub-http-signature/) spec, that is also still a draft.
  See the [related discussion](https://framacolibri.org/t/rfc9421-replaces-the-signing-http-messages-draft/20911/2).
  This spec describe how to sign ActivityPub payload with HTTP headers.
- [Linked Data Signatures 1.0](https://web.archive.org/web/20170717200644/https://w3c-dvcg.github.io/ld-signatures/) draft.
  This specification is replaced by [Verifiable Credential Data Integrity](https://w3c.github.io/vc-data-integrity/) but PeerTube does not implement the finale spec.
  This spec describe how to sign ActivityPub payload by adding fields in the payload.

The state of the specification support in PeerTube is similar to [Mastodon](https://docs.joinmastodon.org/spec/security/), and is probably a mean to keep the two software compatible with each other.

## Limitations

### Usability

As it was out of the scope of the first ActivityPub sprint, those features are missing:

- There is no way to follow an individual user or an individual channel. Pod can only subscribe to other instances meta accounts.
- The other way is broken too. A PeerTube user cannot follow an individual Pod user or channel, and won't be notified for new events.
- The video metadata which is not fitting the PeerTube ActivityPub format (such as cursus, discipline etc.) are not synchronized between instances.

### Technical

- PeerTube instance will only be able to index Pod videos if the thumbnails are in JPEG format.
  png thumbnails are not supported at the moment (but that may come in the future
  [more details here](https://framacolibri.org/t/comments-and-suggestions-on-the-peertube-activitypub-implementation/21215)).
  In the meantime, pod fakes the mime-type of all thumbnails to be JPEG, even when they actually are PNGs.
- PeerTube requires that all videos belong to a channel.
  As a workaround, Pod creates a fake channel for every user, which lists all the videos they own.

## Configuration

The ActivityPub feature is disabled by default, and can be enabled with using the ``USE_ACTIVITYPUB`` configuration parameter.

A RSA keypair is needed for ActivityPub to work, and passed as
`ACTIVITYPUB_PUBLIC_KEY` and `ACTIVITYPUB_PRIVATE_KEY` configuration settings.
They can be generated from a python console:

```python
from Crypto.PublicKey import RSA

activitypub_key = RSA.generate(2048)

# Generate the private key
# Add the content of this command in 'pod/custom/settings_local.py'
# in a variable named ACTIVITYPUB_PRIVATE_KEY
with open("pod/activitypub/ap.key", "w") as fd:
    fd.write(activitypub_key.export_key().decode())

# Generate the public key
# Add the content of this command in 'pod/custom/settings_local.py'
# in a variable named ACTIVITYPUB_PUBLIC_KEY
with open("pod/activitypub/ap.pub", "w") as fd:
    fd.write(activitypub_key.publickey().export_key().decode())
```

The federation also needs celery to be configured with `ACTIVITYPUB_CELERY_BROKER_URL`.

Here is a sample working activitypub `pod/custom/settings_local.py`:

```python
USE_ACTIVITYPUB = True
ACTIVITYPUB_CELERY_BROKER_URL = "redis://redis.localhost:6379/5"

with open("pod/activitypub/ap.key") as fd:
    ACTIVITYPUB_PRIVATE_KEY = fd.read()

with open("pod/activitypub/ap.pub") as fd:
    ACTIVITYPUB_PUBLIC_KEY = fd.read()
```

## Development

The `DOCKER_ENV` environment var should be set to `full` so a peertube instance and a ActivityPub celery worker are launched.
Then peertube is available at http://peertube.localhost:9000.

### Federate PeerTube with Pod

- Sign in with the `root` account
- Go to [Main menu > Administration > Federation](http://peertube.localhost:9000/admin/follows/following-list) > Follow
- Open the *Follow* modal and type `pod.localhost:8000`

### Federate Pod with PeerTube

- Sign in with `admin`
- Go to the [Administration pannel > Followings](http://pod.localhost:8000/admin/activitypub/following/) > Add following
- Type `http://peertube.localhost:9000` in *Object* and save
- On the [Followings list](http://pod.localhost:8000/admin/activitypub/following/) select the new object, and select `Send the federation request` in the action list, refresh.
- If the status is *Following request accepted* then select the object again, and choose `Reindex instance videos` in the action list.

## Shortcuts

### Manual AP request

```shell
curl -H "Accept: application/activity+json, application/ld+json" -s "http://peertube.localhost:9000/accounts/peertube" | jq
```

### Unit tests

```shell
python manage.py test --settings=pod.main.test_settings pod.activitypub.tests
```
