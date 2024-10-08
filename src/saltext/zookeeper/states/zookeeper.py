"""
Manage Zookeeper znodes and ACLs statefully.

.. important::
    This module requires the general :ref:`Zookeeper setup <zookeeper-setup>`.

ACLs
----

For more information about ACLs, please checkout the kazoo documentation.

https://kazoo.readthedocs.io/en/latest/api/security.html#kazoo.security.make_digest_acl

.. _acl-dicts:

ACL dictionaries
~~~~~~~~~~~~~~~~
The following options can be included in the acl dictionary:

username
    Username to use for the ACL.

password
    A plain-text password to hash.

write [bool]
    Write permission.

create [bool]
    Create permission.

delete [bool]
    Delete permission.

admin [bool]
    Admin permission.

all [bool]
    All permissions.
"""

__virtualname__ = "zookeeper"


def __virtual__():
    if "zookeeper.create" in __salt__:
        return __virtualname__
    return (False, "zookeeper module could not be loaded")


def _check_acls(left, right):
    first = not bool(set(left) - set(right))
    second = not bool(set(right) - set(left))
    return first and second


def present(
    name,
    value,
    acls=None,
    ephemeral=False,
    sequence=False,
    makepath=False,
    version=-1,
    profile=None,
    hosts=None,
    scheme=None,
    username=None,
    password=None,
    default_acl=None,
):
    """
    Make sure znode is present in the correct state with the correct acls

    name
        path to znode

    value
        value znode should be set to

    acls
        list of acl dictionaries to set on znode (make sure the ones salt is connected with are included)
        Default: None

    ephemeral
        Boolean to indicate if ephemeral znode should be created
        Default: False

    sequence
        Boolean to indicate if znode path is suffixed with a unique index
        Default: False

    makepath
        Boolean to indicate if the parent paths should be created
        Default: False

    version
        For updating, specify the version which should be updated
        Default: -1 (always match)

    profile
        Configured Zookeeper profile to authenticate with (Default: None)

    hosts
        Lists of Zookeeper Hosts (Default: '127.0.0.1:2181)

    scheme
        Scheme to authenticate with (Default: 'digest')

    username
        Username to authenticate (Default: None)

    password
        Password to authenticate (Default: None)

    default_acl
        Default acls to assign if a node is created in this connection (Default: None)

    .. code-block:: yaml

        add znode:
          zookeeper.present:
            - name: /test/name
            - value: gtmanfred
            - makepath: True

        update znode:
          zookeeper.present:
            - name: /test/name
            - value: daniel
            - acls:
              - username: daniel
                password: test
                read: true
              - username: gtmanfred
                password: test
                read: true
                write: true
                create: true
                delete: true
                admin: true
            - makepath: True
    """

    ret = {
        "name": name,
        "result": False,
        "comment": f"Failed to setup znode {name}",
        "changes": {},
    }
    connkwargs = {
        "profile": profile,
        "hosts": hosts,
        "scheme": scheme,
        "username": username,
        "password": password,
        "default_acl": default_acl,
    }
    if acls is None:
        chk_acls = []
    else:
        chk_acls = [__salt__["zookeeper.make_digest_acl"](**acl) for acl in acls]
    if __salt__["zookeeper.exists"](name, **connkwargs):
        cur_value = __salt__["zookeeper.get"](name, **connkwargs)
        cur_acls = __salt__["zookeeper.get_acls"](name, **connkwargs)
        if cur_value == value and _check_acls(cur_acls, chk_acls):
            ret["result"] = True
            ret["comment"] = (
                f"Znode {name} is already set to the correct value with the correct acls"
            )
            return ret
        elif __opts__["test"] is True:
            ret["result"] = None
            ret["comment"] = f"Znode {name} is will be updated"
            ret["changes"]["old"] = {}
            ret["changes"]["new"] = {}
            if value != cur_value:
                ret["changes"]["old"]["value"] = cur_value
                ret["changes"]["new"]["value"] = value
            if not _check_acls(chk_acls, cur_acls):
                ret["changes"]["old"]["acls"] = cur_acls
                ret["changes"]["new"]["acls"] = chk_acls
            return ret
        else:
            value_result, acl_result = True, True
            changes = {}
            if value != cur_value:
                __salt__["zookeeper.set"](name, value, version, **connkwargs)
                new_value = __salt__["zookeeper.get"](name, **connkwargs)
                value_result = new_value == value
                changes.setdefault("new", {}).setdefault("value", new_value)
                changes.setdefault("old", {}).setdefault("value", cur_value)
            if chk_acls and not _check_acls(chk_acls, cur_acls):
                __salt__["zookeeper.set_acls"](name, acls, version, **connkwargs)
                new_acls = __salt__["zookeeper.get_acls"](name, **connkwargs)
                acl_result = _check_acls(new_acls, chk_acls)
                changes.setdefault("new", {}).setdefault("acls", new_acls)
                changes.setdefault("old", {}).setdefault("value", cur_acls)
            ret["changes"] = changes
            if value_result and acl_result:
                ret["result"] = True
                ret["comment"] = f"Znode {name} successfully updated"
            return ret

    if __opts__["test"] is True:
        ret["result"] = None
        ret["comment"] = f"{name} is will be created"
        ret["changes"]["old"] = {}
        ret["changes"]["new"] = {}
        ret["changes"]["new"]["acls"] = chk_acls
        ret["changes"]["new"]["value"] = value
        return ret

    __salt__["zookeeper.create"](name, value, acls, ephemeral, sequence, makepath, **connkwargs)

    value_result, acl_result = True, True
    changes = {"old": {}}

    new_value = __salt__["zookeeper.get"](name, **connkwargs)
    value_result = new_value == value
    changes.setdefault("new", {}).setdefault("value", new_value)

    new_acls = __salt__["zookeeper.get_acls"](name, **connkwargs)
    acl_result = acls is None or _check_acls(new_acls, chk_acls)
    changes.setdefault("new", {}).setdefault("acls", new_acls)

    ret["changes"] = changes
    if value_result and acl_result:
        ret["result"] = True
        ret["comment"] = f"Znode {name} successfully created"

    return ret


def absent(
    name,
    version=-1,
    recursive=False,
    profile=None,
    hosts=None,
    scheme=None,
    username=None,
    password=None,
    default_acl=None,
):
    """
    Make sure znode is absent

    name
        path to znode

    version
        Specify the version which should be deleted
        Default: -1 (always match)

    recursive
        Boolean to indicate if children should be recursively deleted
        Default: False

    profile
        Configured Zookeeper profile to authenticate with (Default: None)

    hosts
        Lists of Zookeeper Hosts (Default: '127.0.0.1:2181)

    scheme
        Scheme to authenticate with (Default: 'digest')

    username
        Username to authenticate (Default: None)

    password
        Password to authenticate (Default: None)

    default_acl
        Default acls to assign if a node is created in this connection (Default: None)

    .. code-block:: yaml

        delete znode:
          zookeeper.absent:
            - name: /test
            - recursive: True
    """
    ret = {
        "name": name,
        "result": False,
        "comment": f"Failed to delete znode {name}",
        "changes": {},
    }
    connkwargs = {
        "profile": profile,
        "hosts": hosts,
        "scheme": scheme,
        "username": username,
        "password": password,
        "default_acl": default_acl,
    }

    if __salt__["zookeeper.exists"](name, **connkwargs) is False:
        ret["result"] = True
        ret["comment"] = f"Znode {name} does not exist"
        return ret

    changes = {}
    changes["value"] = __salt__["zookeeper.get"](name, **connkwargs)
    changes["acls"] = __salt__["zookeeper.get_acls"](name, **connkwargs)
    if recursive is True:
        changes["children"] = __salt__["zookeeper.get_children"](name, **connkwargs)

    if __opts__["test"] is True:
        ret["result"] = None
        ret["comment"] = f"Znode {name} will be removed"
        ret["changes"]["old"] = changes
        return ret

    __salt__["zookeeper.delete"](name, version, recursive, **connkwargs)

    if __salt__["zookeeper.exists"](name, **connkwargs) is False:
        ret["result"] = True
        ret["comment"] = f"Znode {name} has been removed"
        ret["changes"]["old"] = changes

    return ret


def acls(
    name,
    acls,
    version=-1,
    profile=None,
    hosts=None,
    scheme=None,
    username=None,
    password=None,
    default_acl=None,
):
    """
    Update acls on a znode

    name
        path to znode

    acls
        list of acl dictionaries to set on znode

    version
        Specify the version which should be deleted
        Default: -1 (always match)

    profile
        Configured Zookeeper profile to authenticate with (Default: None)

    hosts
        Lists of Zookeeper Hosts (Default: '127.0.0.1:2181)

    scheme
        Scheme to authenticate with (Default: 'digest')

    username
        Username to authenticate (Default: None)

    password
        Password to authenticate (Default: None)

    default_acl
        Default acls to assign if a node is created in this connection (Default: None)

    .. code-block:: yaml

        update acls:
          zookeeper.acls:
            - name: /test/name
            - acls:
              - username: daniel
                password: test
                all: True
              - username: gtmanfred
                password: test
                all: True
    """
    ret = {
        "name": name,
        "result": False,
        "comment": f"Failed to set acls on znode {name}",
        "changes": {},
    }
    connkwargs = {
        "profile": profile,
        "hosts": hosts,
        "scheme": scheme,
        "username": username,
        "password": password,
        "default_acl": default_acl,
    }
    if isinstance(acls, dict):
        acls = [acls]
    chk_acls = [__salt__["zookeeper.make_digest_acl"](**acl) for acl in acls]

    if not __salt__["zookeeper.exists"](name, **connkwargs):
        ret["comment"] += ": Znode does not exist"
        return ret

    cur_acls = __salt__["zookeeper.get_acls"](name, **connkwargs)
    if _check_acls(cur_acls, chk_acls):
        ret["result"] = True
        ret["comment"] = f"Znode {name} acls already set"
        return ret

    if __opts__["test"] is True:
        ret["result"] = None
        ret["comment"] = f"Znode {name} acls will be updated"
        ret["changes"]["old"] = cur_acls
        ret["changes"]["new"] = chk_acls
        return ret

    __salt__["zookeeper.set_acls"](name, acls, version, **connkwargs)

    new_acls = __salt__["zookeeper.get_acls"](name, **connkwargs)
    ret["changes"] = {"old": cur_acls, "new": new_acls}
    if _check_acls(new_acls, chk_acls):
        ret["result"] = True
        ret["comment"] = f"Znode {name} acls updated"
        return ret
    ret["comment"] = f"Znode {name} acls failed to update"
    return ret
