---
layout: default
version: 4.x
lang: en
---

# Configuring access groups

## Concept of access groups

Prior to version 2.8 of Pod, there was only one type of group in Pod, which could be created and edited in the ‘Authentication and Groups’ category of the Administration section.

Pod now divides things into two types of groups:

- **Groups**, still based on the old model, whose purpose is to give a group of people similar access rights on the platform.
- **AccessGroups**, whose purpose is to give access to content on the platform (videos, ability to upload videos to channels, share folders, etc.).

## Effective configuration of access groups

For CAS, the `USER_CAS_MAPPING_ATTRIBUTES` setting now has a ‘groups’ attribute.

For LDAP, the `USER_LDAP_MAPPING_ATTRIBUTES` setting also has a ‘groups’ attribute.

Feel free to consult the default values for these parameters.

This attribute, combined with the `CREATE_GROUP_FROM_GROUPS` setting, allows you to automatically create groups that will be entered in the specified field. If the `CREATE_GROUP_FROM_GROUPS` setting is not enabled, only an automatic association with existing groups will be made, but none will be created.

> ⚠️ Warning: from now on, all groups entered in the ‘affiliations’ field will also be created as AccessGroups, with the only difference being that if the `CREATE_GROUP_FROM_AFFILIATION` setting is disabled, no association will be made, even if the groups already exist in the application.

## Importing groups via a file

It is possible to import access groups using a command included in Pod and a JSON file that you must provide.

The file must be formatted as follows:

```bash
[
{
    ‘code_name’: ‘mygroup1’,
    ‘display_name’: ‘My group 1j’,
    ‘users_to_add’: [],
    ‘users_to_remove’: [‘admin’]
},
{
    ‘code_name’ : ‘mygroup2’,
    ‘display_name’ : ‘My group 2’,
    ‘users_to_add’ : [“login1”,‘login2’],
    ‘users_to_remove’ : [“login3”,‘login4’]
},
...
]
```

Each group is identified by its **code_name**, which allows it to be identified. The **display_name** is a display name and can therefore be changed via this JSON file. You can also specify a list of users to add to the group (users_to_add) and a list of users to remove from the group (users_to_remove). If the specified users do not exist in the application, they will be ignored and the result will be logged.

The command to run for importing is as follows:

```bash
python manager.py accessgroups import_json myjson.json
```

## Manipulating groups via the Rest API

In addition to the standard routes documented in /rest available for each Pod model, the AccessGroup model has three routes to better manage them:

- /accesgroups_set_users_by_name, which takes the attributes **code_name** and **users** (same format as for JSON) in a POST request in order to add users to an access group.
- /accesgroups_remove_users_by_name, which takes the attributes **code_name** and **users** (same format as for JSON) in a POST request in order to remove users from an access group.
- /accesgroups_set_groups_by_username, which takes the attributes **username** and **groups** (same format as for JSON) in a POST request in order to be able to affiliate a user with groups
- /accesgroups_remove_groups_by_username, which takes the attributes **username** and **groups** (same format as for JSON) in a POST request in order to remove groups from a user.
