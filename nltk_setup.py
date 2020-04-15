from __future__ import absolute_import



import nltk



NLTK_RESOURCES = ['punkt', 'wordnet', 'maxent_treebank_pos_tagger', 'averaged_perceptron_tagger']


def download_nltk_resources():
    for resource in NLTK_RESOURCES:
        if not nltk.download(resource):
            raise RuntimeError('Failed to download NLTK resource {}'.format(resource))


if __name__ == '__main__':
    download_nltk_resources()
