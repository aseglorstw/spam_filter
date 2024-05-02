import os

class Corpus:
    def __init__(self, adress):
        self.adress = adress

    def emails(self):
        emails = os.listdir(self.adress)
        for email in emails:
            if email[0] != "!":
                file_name = self.adress + "/" + email
                with open(file_name, 'rt', encoding='utf-8') as file:
                    body = ""
                    for line in file:
                        body += line
                    yield [email, body]




