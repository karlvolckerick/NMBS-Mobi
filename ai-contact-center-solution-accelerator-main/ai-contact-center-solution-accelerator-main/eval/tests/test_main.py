from pathlib import Path
from unittest.mock import MagicMock, patch

from eval.__main__ import main


class TestMain:
    @patch("eval.__main__.run")
    @patch("eval.__main__.load_eval_config")
    def test_main_with_defaults(self, mock_load_config, mock_run):
        mock_config = MagicMock()
        mock_config.execution.concurrency = 1
        mock_load_config.return_value = mock_config

        with patch("sys.argv", ["eval"]):
            main()

        mock_load_config.assert_called_once_with(Path("config.yaml"))
        mock_run.assert_called_once_with(mock_config)

    @patch("eval.__main__.run")
    @patch("eval.__main__.load_eval_config")
    def test_main_with_custom_config(self, mock_load_config, mock_run):
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        with patch("sys.argv", ["eval", "--config", "custom.yaml"]):
            main()

        mock_load_config.assert_called_once_with(Path("custom.yaml"))
        mock_run.assert_called_once_with(mock_config)

    @patch("eval.__main__.run")
    @patch("eval.__main__.load_eval_config")
    def test_main_with_concurrency_override(self, mock_load_config, mock_run):
        mock_config = MagicMock()
        mock_config.execution.concurrency = 1
        mock_load_config.return_value = mock_config

        with patch("sys.argv", ["eval", "--concurrency", "4"]):
            main()

        assert mock_config.execution.concurrency == 4
        mock_run.assert_called_once_with(mock_config)

    @patch("eval.__main__.run")
    @patch("eval.__main__.load_eval_config")
    def test_main_with_short_flags(self, mock_load_config, mock_run):
        mock_config = MagicMock()
        mock_config.execution.concurrency = 1
        mock_load_config.return_value = mock_config

        with patch("sys.argv", ["eval", "-c", "test.yaml", "-n", "8"]):
            main()

        mock_load_config.assert_called_once_with(Path("test.yaml"))
        assert mock_config.execution.concurrency == 8
        mock_run.assert_called_once_with(mock_config)
