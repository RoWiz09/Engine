import ghost_engine.core.logger as logger
import ghost_engine.core.settings as settings
import ghost_engine

settings_ = settings.Settings()
win_width = int(settings_.get_setting("window_width", 800))
win_height = int(settings_.get_setting("window_height", 600))

logger.setup()
ghost_engine.configure_loggers(log_level = ghost_engine.LoggingLevels.DEBUG)
window = ghost_engine.init_window(window_width=win_width, window_height=win_height)

while not window.should_close():
    window.update()

window.terminate()

settings_.save_config()