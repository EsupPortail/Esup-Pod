---
layout: default
version: 4.x
lang: en
---

# Setting up authentication with Shibboleth

> ⚠️ Documentation to be tested on Pod v4.

Federated authentication with Shibboleth makes it possible to open access to your Pod instance to anyone with an account in a Shibboleth federation. For example, [the Education and Research Federation of Renater](services.renater.fr).

> In practice, once authentication has been requested in the application, the user will be redirected to a WayF-type service (Identity Provider discovery) where they can choose their home institution. They will then be redirected to their institution’s authentication system and finally back to the Pod application where they will be logged in with their account.

## Installing a Shibboleth SP (Service Provider)

To set up authentication with Shibboleth, it is necessary to install a Service Provider. Each “Shibboleth-enabled” application must have its own SP. Note that you also need to have an Identity Provider (IdP) in your institution beforehand. If you don’t already have one, a tutorial is available on the Renater website to set one up.

To install a Shibboleth SP, you can follow the documentation:

* [Renater tutorial for installing SP version 3 (up to chapters 5 or 6)](https://services.renater.fr/federation/documentation/guides-installation/sp3/chap01)
* [Shibboleth Wiki — Installation (in English)](https://wiki.shibboleth.net/confluence/display/SP3/Installation)

In order to use the Education and Research Federation, your service must be registered in it. The entire procedure is detailed in the Renater tutorial. It is recommended to first register your service in the Test Federation, which allows you to test your SP and ensure that everything works correctly.

## Web Server Configuration

Shibboleth is designed to work with Apache2, which is the recommended method. However, since Pod v2 uses Nginx with uWSGI, some configuration adjustments are necessary.

The final goal is to have an Apache2 server in front that (thanks to `mod_shib`) communicates with Shibboleth and provides login/logout routes to the authentication service. It will also allow access to the application using a ReverseProxy.

This is just one possible setup — you are not required to configure communication between Shibboleth and your application in this way. For example, you may [install Shibboleth on the Nginx side](https://wiki.shibboleth.net), or run your Pod instance using Apache’s mod_wsgi without using Nginx at all. These methods have not been tested in this context and are more complex to implement — it’s up to you to choose the one that best fits your needs.

### Step 1: Nginx Configuration

First, you need to change the port on which Nginx runs (since Apache will be in front). In the `server` block of the `pod_nginx.conf` file, change the listening port. In this example, port 8080 is used (but you may choose another). You also need to enable the `proxy_pass_request_header` option to allow proper transmission of headers between Apache and Nginx. You should also enable `underscores_in_headers`.

```bash
server {
    listen 8080;
    proxy_pass_request_headers on;
    underscores_in_headers on;
    ...
}
````

### Step 2: Apache2 Configuration

On the Apache (or httpd) side, configure a `VirtualHost` (or modify the default `VirtualHost`), or edit the `httpd.conf` if you are using httpd.

Depending on whether you are using HTTP or the full version of Apache, make sure to load the modules `mod_shib`, `mod_ssl` (if needed), `mod_proxy`, and `mod_proxy_http` for the following directives to work.

Example:

```bash
<Location />
    ProxyPass https://127.0.0.1:8080/
    ProxyPassReverse http://127.0.0.1:8080/
    AuthType shibboleth
    Require shibboleth
    ShibUseHeaders On
</Location>

<Location /shib/secure>
    # Test route that can be removed later
    ProxyPass !
    AuthType shibboleth
    ShibRequestSetting requireSession 1
    Require shib-session
</Location>

<Location /shib/Shibboleth.sso>
    ProxyPass !
    SetHandler shib
</Location>
```

If you need to use `mod_ssl` with HTTPS exchanges, you may need to use these options (or at least some of them) in addition:

```bash
SSLProxyEngine On
SSLProxyVerify none
SSLProxyCheckPeerCN off
SSLProxyCheckPeerName off
SSLProxyCheckPeerExpire off
ProxyRequests Off
ProxyPreserveHost On
```

> ⚠️ Also make sure to test your Shibboleth installation by visiting `/shib/secure`: this is a test route that lets you verify that your SP is working properly.

### Step 3: Pod Configuration

To enable authentication with Shibboleth in Pod, you need to set 5 settings:

```bash
USE_SHIB = True  # Enables Shibboleth authentication in the login page
SHIB_NAME = "Test Federation"  # Specifies the name of the identity federation to be displayed
SHIBBOLETH_ATTRIBUTE_MAP = {
    "HTTP_REMOTE_USER": (True, "username"),
    "HTTP_DISPLAYNAME": (True, "first_name"),
    "HTTP_DISPLAYNAME": (True, "last_name"),
    "HTTP_MAIL": (False, "email"),
}
REMOTE_USER_HEADER = "HTTP_REMOTE_USER"  # Header name to identify the logged-in user
SHIB_URL = "https://univ-lr.fr/shib/Shibboleth.sso/Login"
SHIB_LOGOUT_URL = "https://univ-lr.fr/shib/Shibboleth.sso/Logout"
```

Also make sure to add Shibboleth authentication to the `AUTH_TYPE` attribute:

```bash
AUTH_TYPE = (('local', ('local')), ('CAS', 'CAS'), ('Shibboleth', 'Shibboleth'))
```

Once Pod is configured, Shibboleth authentication will appear on the login page:

![Shibboleth Authentication](shibboleth_screens/shibboleth1.png)

> 💡 It is entirely possible to have different authentication methods coexist: you can enable CAS, Shibboleth, and local authentication at the same time.

> At this point, Shibboleth authentication should work correctly for Pod. If errors persist, check the Shibboleth-SP logs (`/var/log/shibboleth`) or the IdP side to find the source.

> If you encounter a *502 Bad Request* error, check the size of the returned headers. Consider reducing the `attribute-map.xml` file or increasing the `max_vars` value in the uWSGI configuration (default is 64) to match the number of received headers.
