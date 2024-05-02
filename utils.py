def read_classification_from_file(file_name):
    with open(file_name, 'rt', encoding='utf-8') as file:
        evaluation = dict()
        for line in file:
            line = line.split()
            evaluation[line[0]] = line[1] # email_name = classification
        return evaluation

def write_classification_to_file(test_corpus_dir, evaluation):
    with open(test_corpus_dir + "/!prediction.txt", 'w+', encoding='utf-8') as file:
        for email_name in evaluation.keys():
            file.write(email_name + " " + evaluation[email_name] + "\n")
