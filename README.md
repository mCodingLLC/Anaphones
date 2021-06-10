# Anaphones

Anaphones are like anagrams but for sounds (phonemes).
Examples include: salami-awesomely, atari-tiara, and beefy-phoebe.
Anaphones can be anagrams, like atari-tiara, but they don't have to be, and most anagrams are not anaphones.
Anaphones also include homophones, like their-there-they're,
but the interesting anaphones are ones that have distinct pronunciations.

I've compiled a dictionary of them because why not?
The relevant files are:

- ipa-dict-en_US.json: the phonetic dictionary used to find the anaphones.
- anaphones.json: the complete dictionary of all anaphones I found.
- anaphones_unique_pronunciation.json: 
  same as anaphones.json but deduplicates pronunciations, so homophones like "there, their, they're" will only have one representative.
    
- anaphones_nontrivial_unique_pronunciation.json: additionally filters out words that do not have any anaphones that are not homophones. 
- anaphones.py: the Python code used to generate the dictionaries.