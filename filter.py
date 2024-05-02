import corpus
import utils
import useless_words
import spam_addresses
import ham_addresses

class MyFilter:
    
    def __init__(self):
        self.emails = list() # All emails in format [name, body]
        self.gray_words = useless_words.gray_words # Words that won't help us
        self.ham_addresses = ham_addresses.ham_addresses # Ham addresses = Ok addresses
        self.spam_addresses = spam_addresses.spam_addresses 
        self.ham_words = dict() 
        self.spam_words = dict() 
        self.ham_links = list()
        self.spam_links = list()
        self.ham_words_cnt = 0
        self.spam_words_cnt = 0
        self.ham_guess = 0
        self.spam_guess = 0
        
    def train(self, train_corpus_dir):
        # Trains our spam filter
        corp = corpus.Corpus(train_corpus_dir) 
        self.emails = list(corp.emails()) 
        # correct_eval is a dictionary of correct evaluations {name : evaluation}
        correct_eval = utils.read_classification_from_file(train_corpus_dir + "/!truth.txt")
        # Work out each email, gather info about each one 
        for name, email in self.emails: 
            evaluation = correct_eval[name] # Shows evaluation of the email (OK/SPAM)
            self.analyze_the_email(email, evaluation)
        # Compute initial guess: amount of OK/SPAM messages/amount of all messages
        ham_cnt = list(correct_eval.values()).count("OK") # Amount of OK messages 
        spam_cnt = list(correct_eval.values()).count("SPAM") # Amount of SPAM messages
        self.ham_guess = ham_cnt/(ham_cnt + spam_cnt)
        self.spam_guess = spam_cnt/(ham_cnt + spam_cnt)
        self.compute_word_evaluation()
 
    def analyze_the_email(self, email, evaluation):
        # Gather info about the email: links, sender's email, dictionaries with
        # format word: amount of encounters in OK/SPAM emails
        # A word is a sequence of characters consisting of letters of the alphabet
        email = email.split("\n")
        for line in email:
            line = line.split() # Gets a list of possible words in this line
            if len(line) == 0:
                continue
            # Check if we have an email address in this line
            if line[0] == "From:":
                sender = self.find_senders_address(line)
                if sender != "":
                    if evaluation == "OK" and sender not in self.ham_addresses:
                        self.ham_addresses.append(sender)
                    elif evaluation == "SPAM" and sender not in self.spam_addresses:
                        self.spam_addresses.append(sender)
            # Work out each word in this line
            for word in line:
                # Checks if this word is a link and if so, adds it into a 
                # spam/ham links. Knowledge of the links that are used in 
                # spam/ok messages will help us to divide them 
                if word.startswith("http://") or word.startswith("https://"):
                    if word[-1] in ['.', ']', ',', '/', ')', '}']:
                        word = word[:-1]
                    if evaluation == 'OK' and word not in self.ham_links:
                        word = word.lower()
                        self.ham_links.append(word)
                    elif evaluation == 'SPAM' and word not in self.ham_links and word not in self.spam_links:
                        word = word.lower()
                        self.spam_links.append(word)
                else:
                    # Checks if it is a normal word and then changes ham_words
                    # and spam_words depending on evaluation of email
                    word = self.clean_a_word(word)
                    if word != "":
                        if word in self.gray_words:
                            continue
                        # if the word is already in our dictionaries
                        if evaluation == "OK" and (word in self.ham_words):
                            self.ham_words_cnt += 1
                            self.ham_words[word] += 1
                        elif evaluation == "SPAM" and (word in self.spam_words):
                            self.spam_words[word] += 1
                            self.spam_words_cnt += 1
                        # If the word is new
                        elif evaluation == "OK" and (word not in self.ham_words):
                            self.ham_words[word] = 1
                            self.ham_words_cnt += 1
                            if word not in self.spam_words:
                                self.spam_words[word] = 0
                        elif evaluation == "SPAM" and (word not in self.spam_words):
                            self.spam_words[word] = 1
                            self.spam_words_cnt += 1
                            if word not in self.ham_words:
                                self.ham_words[word] = 0
 
    def find_senders_address(self, line):
        # Finds sender's email address in this line
        for word in line:
            if "@" in word: 
                if word[0].isalpha() == False:
                    word = word[1:]
                if word[-1].isalpha() == False:
                    word = word[:-1]
                word = word.lower()
                return word
        return ""
             
    def clean_a_word(self, word):
        # Translates all letters in the word to lowercase, removes punctuation 
        # marks from the beginning and the end of the word
        # Ignores words that can possible be empty after clearing first and last 
        # characters and ignores non-words
        if len(word) <= 2: 
            return ""
        word = word.lower()
        if word[0].isalpha() == False:
            word = word[1:]
        if word[-1].isalpha() == False:
            word = word[:-1]
        # Ignores small and empty words
        if len(word) <= 2: 
            return ""
        # Ignores words that have more than just letters
        for letter in word:
            if letter < 'a' or letter > 'z':
                word = ""
                break
        return word
 
    def compute_word_evaluation(self):
        # For each word from white words and black words computes the probability 
        # of encountering this word in SPAM or OK email
        # At the beginning in dictionaries ham_words and spam_words we stored 
        # data in format {word: number of encountering it in spam/ham emails}
        # We will change the format to {word: probability of encountering it in spam/ham email}
        # Number of encountering can be 0 so we add 1 to avoid probability = 0
        for word in self.ham_words:
            self.ham_words[word] = (self.ham_words[word] + 1)/(self.ham_words_cnt + len(self.ham_words))
            self.spam_words[word] = (self.spam_words[word] + 1)/(self.spam_words_cnt + len(self.spam_words))
 
    def test(self, test_corpus_dir):
        # Creates file !prediction.txt
        corp = corpus.Corpus(test_corpus_dir)
        self.emails = list(corp.emails())
        evaluation = dict()
        # Work out each email, gather info about each one 
        for name, email in self.emails: 
            evaluation[name] = self.evaluate(email)
        utils.write_classification_to_file(test_corpus_dir, evaluation)
 
    def evaluate(self, email):
        ham_score = self.ham_guess
        spam_score = self.spam_guess
        email = email.split("\n")
        met_words = list() # We will work out first 1000 unique words
        for line in email:
            line = line.split() # Gets a list of possible words in this line
            if len(line) == 0:
                continue
            # Checks sender's email 
            is_new_sender = self.check_bad_senders(line)
            if is_new_sender != "NEW":
                return is_new_sender
            for word in line:
                # Checks if it is a normal word and then computes ham score and
                # spam score
                word = self.clean_a_word(word)
                if word != "":
                    # Ignores new words and gray words
                    if word in self.gray_words or word not in self.ham_words:
                        continue
                    if word not in met_words:
                        met_words.append(word) 
                    if ham_score * self.ham_words[word] == 0 or \
                                        spam_score * self.spam_words[word] == 0:
                        break
                    ham_score *= self.ham_words[word] 
                    spam_score *= self.spam_words[word] 
            if len(met_words) >= 1000:
                break
        if ham_score >= spam_score:
            return "OK"
        else:
            return "SPAM"
        
    def check_bad_links(self, email):
        # If there is a spam link in the email, then this email is spam
        result = "OK"
        for link in self.spam_links:
            if link in email:
                result = "SPAM"
        for link in self.ham_links:
            if link in email:
                result = "OK"
        return result
 
    def check_bad_senders(self, line):
        # Checks, if there is an email in this line and if so, checks if 
        # this email is already in a list of spam or ham addresses. 
        if line[0] == "From:":
            sender = self.find_senders_address(line)
            if sender != "":
                if sender in self.spam_addresses:
                    return "SPAM"
                elif sender in self.ham_addresses:
                    return "OK"
        return "NEW"