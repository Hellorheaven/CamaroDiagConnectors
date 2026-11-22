"""Durable host-side programming journal model. No physical driver.

A durable intent is recorded before each potential destructive phase. Reopening
an in-flight transaction marks recovery required; it cannot authorize retries.
Use a private local directory, not network/removable storage. This software
model does not prove durability of the eventual embedded journal.
"""
import os
import re
import sqlite3
from pathlib import Path

_NEXT = {"prepared":"erase_intent", "erase_intent":"program_intent",
         "program_intent":"verify_intent", "verify_intent":"verified",
         "verified":"restart_intent", "restart_intent":"postcheck",
         "postcheck":"completed"}
_CRITICAL = {"erase_intent","program_intent","verify_intent","verified",
             "restart_intent","postcheck"}
_DIGEST = re.compile(r"[0-9a-f]{64}")

class ProgrammingJournal:
    def __init__(self, db):
        self.db=db
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA journal_mode=DELETE")

    @classmethod
    def create(cls, path, *, target, profile, original_sha256, desired_sha256):
        if not isinstance(target,str) or not target.strip() or not isinstance(profile,str) or not profile.strip():
            raise ValueError("Exact target and profile are required")
        if any(not isinstance(x,str) or not _DIGEST.fullmatch(x) for x in (original_sha256,desired_sha256)):
            raise ValueError("Invalid SHA-256")
        file=Path(path)
        fd=os.open(file,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.close(fd)
        journal=cls(sqlite3.connect(file, isolation_level=None))
        try:
            with journal._transaction():
                journal.db.execute("CREATE TABLE metadata (target TEXT NOT NULL, profile TEXT NOT NULL, original_sha256 TEXT NOT NULL, desired_sha256 TEXT NOT NULL)")
                journal.db.execute("INSERT INTO metadata VALUES (?,?,?,?)",(target,profile,original_sha256,desired_sha256))
                journal.db.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, state TEXT NOT NULL, stamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
                journal.db.execute("INSERT INTO events(state) VALUES ('prepared')")
            return journal
        except BaseException:
            journal.close()
            # Preserve failed file for inspection; never overwrite automatically.
            raise

    @classmethod
    def reopen(cls,path):
        uri=Path(path).resolve().as_uri()+"?mode=rw"
        journal=cls(sqlite3.connect(uri,uri=True,isolation_level=None))
        try:
            with journal._transaction():
                if journal.state in _CRITICAL:
                    journal._append("recovery_required")
            return journal
        except BaseException:
            journal.close()
            raise

    from contextlib import contextmanager
    @contextmanager
    def _transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    @property
    def state(self):
        row=self.db.execute("SELECT state FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        if not row or row[0] not in set(_NEXT)|{"completed","aborted","recovery_required"}:
            raise ValueError("Invalid journal state")
        return row[0]

    def _append(self,state):
        self.db.execute("INSERT INTO events(state) VALUES (?)",(state,))

    def advance(self,expected,following):
        """Compare-and-transition under a durable transaction (model only)."""
        with self._transaction():
            if self.state != expected or _NEXT.get(expected)!=following:
                raise ValueError("Stale or forbidden programming transition")
            self._append(following)

    def fault(self):
        with self._transaction():
            current=self.state
            if current=="prepared":
                self._append("aborted")
            elif current in _CRITICAL:
                self._append("recovery_required")
            # Terminal states cannot be cleared by an error or reconnect.

    def history(self):
        return tuple(row[0] for row in self.db.execute("SELECT state FROM events ORDER BY seq"))

    def close(self):
        self.db.close()
