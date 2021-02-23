import pickle
import numpy as np

# prepare
def create_synonym(vocab_list,vocab_embeddings,k=1):

    norm_vocab_embeddings = np.linalg.norm(vocab_embeddings, axis=1)

    synonyms = {}
    for i in range(len(vocab_list)):
        v = vocab_embeddings[i]
        similarity = np.dot(v,vocab_embeddings.T) / (np.linalg.norm(v) * norm_vocab_embeddings)
        top_k_idx = similarity.argsort()[-(k+1):][::-1][1:]
        temp_synonym = []
        for idx in top_k_idx:
            if similarity[idx] >= 0.96:
                temp_synonym.append(vocab_list[idx])
        synonyms[vocab_list[i]] = ', '.join(temp_synonym)

    return synonyms


with open('vocab.txt', encoding='utf-8') as f:
    vocab_list = [vocab.strip() for vocab in f.readlines()]

with open('vocab_embeddings.pickle', 'rb') as f:
    vocab_embeddings = pickle.load(f)

synonyms = create_synonym(vocab_list,vocab_embeddings,1)
with open('synonyms.pickle','wb') as f:
    pickle.dump(synonyms, f)

# with open('synonyms.pickle','rb') as f:
#     synonyms = pickle.load(f)

synonyms_list = []
for key,value in synonyms.items():
    if value != '' and ',' not in key and ',' not in value:
        synonyms_list.append(key+','+value+'\n')

with open('synonyms.txt','w') as f:
    f.writelines(synonyms_list)

print('done!')
