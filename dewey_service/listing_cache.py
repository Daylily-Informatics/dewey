"""Bounded raw S3 listing cache. Authorization never lives in this cache."""
from collections import OrderedDict
from concurrent.futures import Future
from copy import deepcopy
from threading import RLock
from time import monotonic
from sys import getsizeof

from dewey_service.performance import measure, metric


def _size(value):
    seen = set()
    def visit(item):
        if id(item) in seen:
            return 0
        seen.add(id(item))
        result = getsizeof(item)
        if isinstance(item, dict):
            result += sum(visit(k) + visit(v) for k, v in item.items())
        elif isinstance(item, (list, tuple)):
            result += sum(visit(v) for v in item)
        return result
    return visit(value)


class ListingCache:
    def __init__(self):
        self._lock = RLock()
        self._entries = OrderedDict()
        self._flights = {}
        self._generation = 0
        self._bytes = 0
        self._ttl = None

    def invalidate(self):
        # A generation also fences every fetch that started before invalidation.
        with self._lock:
            self._generation += 1
            self._entries.clear()
            self._bytes = 0

    def get(self, key, *, ttl, refresh, fetch):
        if type(ttl) is not int or not 0 <= ttl <= 300:
            raise ValueError("Listing cache TTL must be an integer from 0 through 300")
        with self._lock:
            if ttl != self._ttl or refresh:
                self.invalidate()
                self._ttl = ttl
            if ttl == 0:
                flight = None
            else:
                entry = self._entries.get(key)
                if entry is not None:
                    created, size, result = entry
                    if monotonic() - created < ttl:
                        self._entries.move_to_end(key)
                        metric("cache_hits", 1)
                        return deepcopy(result)
                    self._entries.pop(key)
                    self._bytes -= size
                flight_key = (self._generation, key)
                flight = self._flights.get(flight_key)
                owner = flight is None
                if owner:
                    flight = Future()
                    self._flights[flight_key] = flight
        if ttl and not owner:
            metric("cache_coalesced", 1)
            from dewey_service.performance import remaining_seconds
            return deepcopy(flight.result(timeout=remaining_seconds()))
        metric("cache_misses", 1)
        try:
            with measure("s3_ms"):
                result = fetch()
            if ttl:
                size = _size((key, result)) + 256
                with self._lock:
                    if flight_key[0] == self._generation and size <= 64 * 1024 * 1024:
                        while self._entries and (len(self._entries) >= 256 or self._bytes + size > 64 * 1024 * 1024):
                            _, (_, removed_size, _) = self._entries.popitem(last=False)
                            self._bytes -= removed_size
                        self._entries[key] = (monotonic(), size, deepcopy(result))
                        self._bytes += size
                    flight.set_result(result)
            return deepcopy(result)
        except BaseException as exc:
            if ttl:
                flight.set_exception(exc)
            raise
        finally:
            if ttl:
                with self._lock:
                    self._flights.pop(flight_key, None)
