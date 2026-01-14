import RoDevEngine

import RoDevEngine.core.logger as logger
import RoDevEngine.core.settings

settings = RoDevEngine.core.settings.Settings()
win_width = int(settings.get_setting("window_width", 800))
win_height = int(settings.get_setting("window_height", 600))

RoDevEngine.set_logging_level(RoDevEngine.LoggingLevels.DEBUG)
window = RoDevEngine.init(window_width=win_width, window_height=win_height)

while not window.should_close():
    window.update()

window.terminate()

settings.save_config()