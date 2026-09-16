import logging
import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock

from portable_boot import configure
configure()
from whisper_key.state_manager import StateManager  # noqa: E402


class ModelLoadingStateTests(unittest.TestCase):
    def make_manager(self, messages, loading_after=True):
        manager = StateManager.__new__(StateManager)
        manager.logger = logging.getLogger(__name__)
        manager.set_model_loading = Mock()

        class Engine:
            def change_model(self, key, callback):
                for message in messages:
                    callback(message)

            def is_loading(self):
                return loading_after

        manager.whisper_engine = Engine()
        return manager

    def test_success_failure_cancel_timeout_and_error_leave_loading(self):
        for terminal in (
            "Model ready!",
            "Failed to load model: broken",
            "Model download cancelled",
            "Model download timed out",
            "Model load error",
        ):
            with self.subTest(terminal=terminal):
                manager = self.make_manager(("Downloading model...", terminal))
                with redirect_stdout(io.StringIO()):
                    manager._execute_model_change("small")
                self.assertEqual(manager.set_model_loading.call_args_list[-1].args, (False,))

    def test_synchronous_noop_and_exception_leave_loading(self):
        manager = self.make_manager((), loading_after=False)
        with redirect_stdout(io.StringIO()):
            manager._execute_model_change("small")
        self.assertEqual(manager.set_model_loading.call_args_list[-1].args, (False,))

        manager.whisper_engine.change_model = Mock(side_effect=RuntimeError("boom"))
        with redirect_stdout(io.StringIO()):
            manager._execute_model_change("small")
        self.assertEqual(manager.set_model_loading.call_args_list[-1].args, (False,))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
