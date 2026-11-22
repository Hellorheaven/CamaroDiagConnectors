import tempfile
import unittest
from pathlib import Path
from camarodiagconnectors.programming_journal import ProgrammingJournal

class JournalTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"transaction.sqlite"
    def create(self):
        return ProgrammingJournal.create(self.path,target="synthetic ECU",
            profile="synthetic HW revision 1",original_sha256="a"*64,desired_sha256="b"*64)
    def test_complete_transaction(self):
        events=("prepared","erase_intent","program_intent","verify_intent","verified",
                "restart_intent","postcheck","completed")
        journal=self.create()
        try:
            for a,b in zip(events,events[1:]): journal.advance(a,b)
            self.assertEqual(journal.history(),events)
        finally: journal.close()
        reopened=ProgrammingJournal.reopen(self.path)
        try:
            self.assertEqual(reopened.state,"completed")
            reopened.fault()
            self.assertEqual(reopened.history(),events)
        finally: reopened.close()
    def test_reopen_each_critical_phase(self):
        events=("prepared","erase_intent","program_intent","verify_intent","verified","restart_intent","postcheck")
        for i in range(1,len(events)):
            with self.subTest(phase=events[i]):
                self.path=self.path.with_name(f"{i}.sqlite")
                journal=self.create()
                try:
                    for k in range(i): journal.advance(events[k],events[k+1])
                finally: journal.close()
                restarted=ProgrammingJournal.reopen(self.path)
                try:
                    self.assertEqual(restarted.state,"recovery_required")
                    with self.assertRaises(ValueError): restarted.advance(events[i],"completed")
                finally: restarted.close()
    def test_refuse_skip_and_overwrite(self):
        journal=self.create()
        try:
            with self.assertRaises(ValueError): journal.advance("prepared","completed")
            with self.assertRaises(FileExistsError): self.create()
            self.assertEqual(journal.history(),("prepared",))
            journal.fault()
            self.assertEqual(journal.state,"aborted")
        finally: journal.close()
    def test_fault_after_erase_intent(self):
        journal=self.create()
        try:
            journal.advance("prepared","erase_intent")
            journal.fault()
            journal.fault()
            self.assertEqual(journal.history(),("prepared","erase_intent","recovery_required"))
        finally: journal.close()
    def test_missing_file_is_not_created(self):
        import sqlite3
        with self.assertRaises(sqlite3.OperationalError): ProgrammingJournal.reopen(self.path)
        self.assertFalse(self.path.exists())
