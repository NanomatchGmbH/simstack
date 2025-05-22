from unittest.mock import MagicMock, patch

from PySide6.QtCore import QMutex

from simstack.view.ViewTimer import ViewTimer


@patch("simstack.view.ViewTimer.QTimer")
def test_view_timer_init(mock_qtimer, qtbot):
    """Test initialization of ViewTimer"""
    callback = MagicMock()
    mock_timer_instance = MagicMock()
    mock_qtimer.return_value = mock_timer_instance

    timer = ViewTimer(callback)

    # Check that QTimer was created
    mock_qtimer.assert_called_once()

    assert timer._timer == mock_timer_instance
    assert timer._callback == callback
    assert timer._remaining_due_times == []
    assert timer._due_time == -1
    assert timer._last_timeout == -1
    assert isinstance(timer._lock, QMutex)

    # Check connection
    mock_timer_instance.timeout.connect.assert_called_once()


def test_view_timer_stop(qtbot):
    """Test stop method of ViewTimer"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Mock timer.stop
    timer._timer.stop = MagicMock()

    # Call stop method
    timer.stop()

    # Check if timer.stop was called
    timer._timer.stop.assert_called_once()

    # Check if last_timeout was reset
    assert timer._last_timeout == -1


@patch("time.time", return_value=100)
def test_view_timer_update_interval_inactive_timer(mock_time, qtbot):
    """Test update_interval with inactive timer"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Mock timer methods
    timer._timer.isActive = MagicMock(return_value=False)
    timer._timer.start = MagicMock()

    # Mock lock methods
    timer._lock_list = MagicMock()
    timer._unlock_list = MagicMock()

    # Call update_interval
    interval = 5
    timer.update_interval(interval)

    # Check if lock methods were called
    timer._lock_list.assert_called_once()
    timer._unlock_list.assert_called_once()

    # Check if timer was started with correct interval
    timer._timer.start.assert_called_once_with(interval * 1000)

    # Check if due_time was set correctly
    assert timer._due_time == mock_time.return_value + interval

    # Check if last_timeout was set
    assert timer._last_timeout == mock_time.return_value


@patch("time.time", return_value=100)
def test_view_timer_update_interval_active_timer_positive_remainder(mock_time, qtbot):
    """Test update_interval with active timer and positive remainder"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Setup initial state
    timer._due_time = 110  # 10 seconds from now

    # Mock timer methods
    timer._timer.isActive = MagicMock(return_value=True)
    timer._timer.setInterval = MagicMock()

    # Mock lock methods
    timer._lock_list = MagicMock()
    timer._unlock_list = MagicMock()

    # Call update_interval with 5 seconds
    interval = 5
    timer.update_interval(interval)

    # Check if lock methods were called
    timer._lock_list.assert_called_once()
    timer._unlock_list.assert_called_once()

    # The remainder should be 110 - 100 - 5 = 5 seconds
    assert timer._remaining_due_times == [5]

    # Check if due_time was updated
    assert timer._due_time == mock_time.return_value + interval

    # Check if timer interval was updated
    timer._timer.setInterval.assert_called_once_with(interval * 1000)


@patch("time.time", return_value=100)
def test_view_timer_update_interval_active_timer_negative_remainder(mock_time, qtbot):
    """Test update_interval with active timer and negative remainder"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Setup initial state
    timer._due_time = 110  # 10 seconds from now

    # Mock timer methods
    timer._timer.isActive = MagicMock(return_value=True)
    timer._timer.setInterval = MagicMock()

    # Mock lock methods
    timer._lock_list = MagicMock()
    timer._unlock_list = MagicMock()

    # Call update_interval with 15 seconds (more than the remaining time)
    interval = 15
    timer.update_interval(interval)

    # Check if lock methods were called
    timer._lock_list.assert_called_once()
    timer._unlock_list.assert_called_once()

    # The remainder should be negative: 110 - 100 - 15 = -5 seconds
    # So we add abs(-5) = 5 to the beginning of the remaining_due_times
    assert timer._remaining_due_times == [5]


@patch("time.time", return_value=100)
def test_view_timer_timeout_without_remaining_times(mock_time, qtbot):
    """Test __timeout method with no remaining times"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Setup state
    timer._last_timeout = 95  # 5 seconds ago
    timer._due_time = 100  # Due now
    timer._remaining_due_times = []

    # Mock methods
    timer._lock_list = MagicMock()
    timer._unlock_list = MagicMock()
    timer.stop = MagicMock()

    # Call __timeout method
    timer._ViewTimer__timeout()

    # Check if lock methods were called
    timer._lock_list.assert_called_once()
    timer._unlock_list.assert_called_once()

    # Check if stop was called
    timer.stop.assert_called_once()

    # Check if callback was called with correct elapsed time
    callback.assert_called_once_with(5)  # 100 - 95 = 5 seconds

    # Check if last_timeout was updated
    assert timer._last_timeout == mock_time.return_value


@patch("time.time", return_value=100)
def test_view_timer_timeout_with_remaining_times(mock_time, qtbot):
    """Test __timeout method with remaining times"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Setup state
    timer._last_timeout = 95  # 5 seconds ago
    timer._due_time = 100  # Due now
    timer._remaining_due_times = [7, 3]  # Two more timeouts

    # Mock methods
    timer._lock_list = MagicMock()
    timer._unlock_list = MagicMock()
    timer._timer.setInterval = MagicMock()
    timer.stop = MagicMock()

    # Call __timeout method
    timer._ViewTimer__timeout()

    # Check if lock methods were called
    timer._lock_list.assert_called_once()
    timer._unlock_list.assert_called_once()

    # Check if stop was NOT called
    timer.stop.assert_not_called()

    # Check if next timeout was set
    timer._timer.setInterval.assert_called_once_with(
        3 * 1000
    )  # Last item popped from the list

    # Check if callback was called with correct elapsed time
    callback.assert_called_once_with(5)  # 100 - 95 = 5 seconds

    # Check if last_timeout was updated
    assert timer._last_timeout == mock_time.return_value

    # Check if remaining_due_times was updated
    assert timer._remaining_due_times == [7]


@patch("time.time", return_value=100)
def test_view_timer_timeout_not_due_yet(mock_time, qtbot):
    """Test __timeout method when not due yet"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Setup state
    timer._last_timeout = 95  # 5 seconds ago
    timer._due_time = 110  # Due in 10 seconds
    timer._remaining_due_times = [7, 3]  # Not used in this test

    # Mock methods
    timer._lock_list = MagicMock()
    timer._unlock_list = MagicMock()
    timer._timer.setInterval = MagicMock()
    timer.stop = MagicMock()

    # Call __timeout method
    timer._ViewTimer__timeout()

    # Check if lock methods were called
    timer._lock_list.assert_called_once()
    timer._unlock_list.assert_called_once()

    # Check if neither stop nor setInterval were called
    timer.stop.assert_not_called()
    timer._timer.setInterval.assert_not_called()

    # Check if callback was called with correct elapsed time
    callback.assert_called_once_with(5)  # 100 - 95 = 5 seconds

    # Check if last_timeout was updated
    assert timer._last_timeout == mock_time.return_value

    # Check if remaining_due_times was not changed
    assert timer._remaining_due_times == [7, 3]


def test_view_timer_set_or_start_active_timer(qtbot):
    """Test __set_or_start method with active timer"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Mock timer methods
    timer._timer.isActive = MagicMock(return_value=True)
    timer._timer.setInterval = MagicMock()
    timer._timer.start = MagicMock()

    # Call __set_or_start
    interval = 5
    timer._ViewTimer__set_or_start(interval)

    # Check if setInterval was called
    timer._timer.setInterval.assert_called_once_with(interval * 1000)

    # Check if start was NOT called
    timer._timer.start.assert_not_called()


def test_view_timer_set_or_start_inactive_timer(qtbot):
    """Test __set_or_start method with inactive timer"""
    callback = MagicMock()
    timer = ViewTimer(callback)

    # Mock timer methods
    timer._timer.isActive = MagicMock(return_value=False)
    timer._timer.setInterval = MagicMock()
    timer._timer.start = MagicMock()

    # Call __set_or_start
    interval = 5
    timer._ViewTimer__set_or_start(interval)

    # Check if start was called
    timer._timer.start.assert_called_once_with(interval * 1000)

    # Check if setInterval was NOT called
    timer._timer.setInterval.assert_not_called()
