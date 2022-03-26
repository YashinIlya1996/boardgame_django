from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bg_project.apps.users'

    def ready(self):
        """ Метод вызывается единоразово при инициализации приложения
            В данном случае используется, чтобы зарегистрировать сигналы. """
        import bg_project.apps.users.signals

