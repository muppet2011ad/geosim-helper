class Comment(object):
    def __init__(self, body):
        self.body = body

    def reply(self, text):
        print(text)