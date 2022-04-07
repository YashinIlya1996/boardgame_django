class MeetCategory:
    regex = "future|im-creator|with-my-participation|past"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)