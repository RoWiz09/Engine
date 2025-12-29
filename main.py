import RoDevEngine

import RoDevEngine.core.logger as logger
import RoDevEngine.core.settings

settings = RoDevEngine.core.settings.Settings()
win_width = int(settings.get_setting("window_width", 800))
win_height = int(settings.get_setting("window_height", 600))

logger.configure_loggers(log_level = logger.LoggingLevels.FATAL, log_to_console = True)
window = RoDevEngine.init(window_width=win_width, window_height=win_height)

while not window.should_close():
    window.update()

window.terminate()

settings.save_config()