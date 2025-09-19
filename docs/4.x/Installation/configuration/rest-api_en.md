---
layout: default
version: 4.x
lang: en
---

# Using the Rest API

To use, import, and export data to and from your Pod instance, you have two options: via a browser or via the command line.

## Browser

Using your browser, simply go to your Pod’s Rest page: `http(s)://pod.univ.fr/rest` and enter your instance’s root account details.

You will then have access to your instance’s data in JSON format and will be able to post new data.

Feel free to explore this interface to discover all its possibilities.

We recommend restricting access to ‘/rest’ on your instance via your nginx configuration:

```bash
location /rest {
    allow XXX.XXX.X.X/24;
    deny all;
}
```

## Terminal

To manage your Pod instance data from the command line, follow these steps:

### Create an authentication token

In the administration panel, create an authentication token: `http(s)://pod.univ.fr/admin/authtoken/`

> ⚠️ Please note that the token will have the same access rights as the user selected to create it.

You can then use this token in your Curl requests.

For example, this request allows you to retrieve users:

```bash
curl -H ‘Content-Type: application/json’ -H “Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX” -X GET -d “{}” http(s)://pod.univ.fr/rest/users/
```

To learn how to create your queries, feel free to use the web interface via your browser, where you will find a list of editable objects and query examples.

Another example: the following command allows you to create a type called ‘test’:

```bash
curl -H ‘Content-Type: application/json’ -H “Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX” -X POST -d '{
    ‘title’: ‘test’
}' http(s)://pod.univ.fr/rest/types/
```

Executing this command returns the created type:

```bash
    {‘id’:13,‘url’:‘http(s)://pod.univ.fr/rest/types/13/’,‘title’:‘test’,“description”:‘-- sorry, no translation provided --’,‘icon’:null}
```

Finally, you can modify an existing element. For example, you can change the type created above.

The following command changes the title of the type with the identifier 13:

```bash
    curl -H ‘Content-Type: application/json’ -H 'Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX' -X PATCH -d '{
        ‘title’: ‘test new’
    }' http(s)://pod.univ.fr/rest/types/13/
```

This command returns the same information as when creating.

Finally, it is also possible to post (without launching encoding) videos from the command line. Here is an example:

```bash
curl  -H "Content-Type: multipart/form-data" \
    -H 'Authorization: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX' \
    -F "owner=http(s)://pod.univ.fr/rest/users/1/" \
    -F "type=http(s)://pod.univ.fr/rest/types/1/" \
    -F "title=ma video" \
    -F "video=@/Users/test/video.mp4" \
    http(s)://pod.univ.fr/rest/videos/
```

If successful, this command returns all available information related to this video. If you wish to start encoding it, you can use the ‘slug’ or short title information (generated automatically during creation) as a parameter in a second command. Example:

```bash
curl -XGET -H ‘Content-Type: application/json’ \
    -H “Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX” \
    ‘http(s)://pod.univ.fr/rest/launch_encode_view/?slug=id-ma-video’
```

Please note that for object relationships, you must specify the URL rather than the primary key:

```bash
    The HyperlinkedModelSerializer class is similar to the ModelSerializer class except that it uses hyperlinks to represent relationships, rather than primary keys. By default, the serialiser will include a URL field instead of a primary key field.
```

This may be changed in future versions of Pod.

Managing broadcasters from the command line:

Retrieving the list of broadcasters:

```bash
curl  -H ‘Content-Type: application/json’ \
  -H “Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX” \
  -F ‘slug=id-ma-video’ \
  http(s)://pod.univ.fr/rest/broadcasters/
```

The server response will be in this format:

```json
{
"count": 1,
"next": null,
"previous": null,
"results": [
    {
    "id": 5,
    "url": "https://pod.univ.fr/my_streamer/playlist.m3u8",
    "name": "Nom de mon Diffuseur",
    "slug": "nom-de-mon-diffuseur",
    "building": "https://pod.univ.fr/rest/buildings/3/",
    "description": "",
    "poster": null,
    "status": true
    }
]
}
```

Below is an example of updating the ‘status’ parameter of a broadcaster. Using the previous response, we can therefore execute the following command:

```bash
curl --location --request PATCH “https://pod.univ.fr/rest/broadcasters/nom-de-mon-diffuseur/” \
--header “Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX” \
--header “Content-Type: application/json” \
--data-raw “{‘status’ : true}”
```

## DublinCore

Finally, to obtain the DublinCore representation of your videos, simply make a curl request to `/rest/dublincore`.

You can filter your videos using GET parameters added to your URL.

For example, to obtain the DublinCore representation of user 1’s videos, you can run the following command:

```bash
curl -H ‘Content-Type: application/json’ -H “Authorisation: Token XXXXXXXXXXX71922e47ed412eabcbd241XXXXXXX” -X GET http(s)://pod.univ.fr/rest/dublincore/?owner=1
```

This will return XML in DublinCore format.

> Please ensure that you enter the variables `DEFAULT_DC_COVERAGE` and `DEFAULT_DC_RIGHTS` in your configuration file.
