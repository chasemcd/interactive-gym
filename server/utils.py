"""
This is all stolen from: https://github.com/HumanCompatibleAI/overcooked-demo/blob/master/server/utils.py
"""

from threading import Lock


class ThreadSafeSet(set):
    def __init__(self, *args, **kwargs):
        super(ThreadSafeSet, self).__init__(*args, **kwargs)
        self.lock = Lock()

    def add(self, *args):
        with self.lock:
            retval = super(ThreadSafeSet, self).add(*args)
        return retval

    def clear(self, *args):
        with self.lock:
            retval = super(ThreadSafeSet, self).clear(*args)
        return retval

    def pop(self, *args):
        with self.lock:
            if len(self):
                retval = super(ThreadSafeSet, self).pop(*args)
            else:
                retval = None
        return retval

    def remove(self, item):
        with self.lock:
            if item in self:
                retval = super(ThreadSafeSet, self).remove(item)
            else:
                retval = None
        return retval


class ThreadSafeDict(dict):
    def __init__(self, *args, **kwargs):
        super(ThreadSafeDict, self).__init__(*args, **kwargs)
        self.lock = Lock()

    def clear(self, *args, **kwargs):
        with self.lock:
            retval = super(ThreadSafeDict, self).clear(*args, **kwargs)
        return retval

    def pop(self, *args, **kwargs):
        with self.lock:
            retval = super(ThreadSafeDict, self).pop(*args, **kwargs)
        return retval

    def __setitem__(self, *args, **kwargs):
        with self.lock:
            retval = super(ThreadSafeDict, self).__setitem__(*args, **kwargs)
        return retval

    def __delitem__(self, item):
        with self.lock:
            if item in self:
                retval = super(ThreadSafeDict, self).__delitem__(item)
            else:
                retval = None
        return retval


class GameExitStatus:
    ActiveWithOtherPlayers = "active_with_other_players"
    ActiveNoPlayers = "active_no_players"
    InactiveNoPlayers = "inactive_no_players"
    InactiveWithOtherPlayers = "inactive_with_other_players"


class _Available:
    """
    Adapted from RLLib's _NotProvided
    https://github.com/ray-project/ray/rllib/utils/from_config.py#L261
    """

    class __Available:
        pass

    instance = None

    def __init__(self):
        if _Available.instance is None:
            _Available.instance = _Available.__Available()


Available = _Available
