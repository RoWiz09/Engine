import RoDevEngine

import RoDevEngine.core.logger
import RoDevEngine.core.settings

settings = RoDevEngine.core.settings.Settings()
win_width = int(settings.get_setting("window_width", 800))
win_height = int(settings.get_setting("window_height", 600))

window = RoDevEngine.init(window_width=win_width, window_height=win_height)
RoDevEngine.core.logger.configure_loggers(log_level = RoDevEngine.core.logger.logging_levels.DEBUG)

while not window.should_close():
    window.update()

settings.save_config()

RoDevEngine.get_logger("My-Logger").log_info("Window closed.")