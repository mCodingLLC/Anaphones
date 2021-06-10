import json
import sys
from collections import defaultdict, UserDict
from typing import Dict, List, Iterator, Iterable, Union, TypeVar, Optional, Callable

import attr

if sys.version_info < (3, 9):
    raise RuntimeError("This module requires Python 3.9 or higher")


def clean_str_to_alphanum(word: str) -> str:
    return "".join(c for c in word if c.isalpha() and c not in 'ˈˌ.-"\'')


def normalize_pronunciation(pronunciation: str) -> str:
    return clean_str_to_alphanum(pronunciation.strip('/'))


@attr.s(frozen=True, slots=True)
class Spelling:
    s: str = attr.ib(converter=clean_str_to_alphanum)

    def __str__(self) -> str:
        return self.s

    def sorted(self) -> 'Spelling':
        return Spelling(sorted_str(self.s))

    def is_anagram_of(self, other: 'Spelling') -> bool:
        return self.sorted() == other.sorted()


@attr.s(frozen=True, slots=True)
class Pronunciation:
    s: str = attr.ib(converter=normalize_pronunciation)

    def __str__(self) -> str:
        return self.s

    def sorted(self) -> 'Pronunciation':
        return Pronunciation(sorted_str(self.s))

    def is_anagram_of(self, other: 'Pronunciation') -> bool:
        return self.sorted() == other.sorted()


@attr.s(frozen=True, slots=True)
class PronouncedWord:
    spelling: Spelling = attr.ib()
    pronunciation: Pronunciation = attr.ib()

    def __str__(self) -> str:
        return f'({str(self.spelling)}, {str(self.pronunciation)})'

    def is_anagram_of(self, other: 'PronouncedWord') -> bool:
        return self.spelling.is_anagram_of(other.spelling)

    def is_phonetic_anagram_of(self, other: 'PronouncedWord') -> bool:
        return self.pronunciation.is_anagram_of(other.pronunciation)

    def json_safe_str(self) -> str:
        return f'{self.spelling}:{self.pronunciation}'


def deduplicate_pronunciations(words: Iterable[PronouncedWord]) -> List[PronouncedWord]:
    seen_pronunciations = set()
    unique = []
    for word in words:
        if word.pronunciation not in seen_pronunciations:
            unique.append(word)
            seen_pronunciations.add(word.pronunciation)
    return unique


class IPADict(UserDict[Spelling, List[Pronunciation]]):

    @staticmethod
    def from_file(filename: str, language: str) -> 'IPADict':
        with open(filename, encoding='utf-8') as fp:
            (d,) = json.load(fp)[language]
        return IPADict({
            Spelling(k): list(set(Pronunciation(x) for x in v.split(', ')))
            for k, v in d.items()
        })

    def flatten_to_pronounced_words(self) -> Iterator[PronouncedWord]:
        for spelling, pronunciations in self.data.items():
            for pronunciation in pronunciations:
                yield PronouncedWord(spelling, pronunciation)


def sorted_str(word: str) -> str:
    return "".join(sorted(word))


T = TypeVar('T')


def find_anagrams(spellings: Iterable[T], key: Optional[Callable[[T], str]] = None) -> Dict[Pronunciation, List[T]]:
    d: Dict[str, List[T]] = defaultdict(list)
    for w in spellings:
        s: str
        if key is not None:
            s = key(w)
        elif not isinstance(w, str):
            raise TypeError
        else:
            s = w
        d[sorted_str(s)].append(w)
    return {Pronunciation(letters): word_list for letters, word_list in d.items()}


class PhoneticAnagramDict(UserDict[Pronunciation, List[PronouncedWord]]):

    @staticmethod
    def from_IPADict(ipa_dict: IPADict) -> 'PhoneticAnagramDict':
        def get_pronunciation_str(x: PronouncedWord) -> str:
            return x.pronunciation.s

        phonetic_anagrams = find_anagrams(ipa_dict.flatten_to_pronounced_words(),
                                          key=get_pronunciation_str)
        return PhoneticAnagramDict(phonetic_anagrams)

    def __getitem__(self, pronunciation: Union[str, Pronunciation]) -> List[PronouncedWord]:
        if isinstance(pronunciation, Pronunciation):
            return self.data[pronunciation.sorted()]
        else:
            return self.data[Pronunciation(pronunciation).sorted()]

    def __str__(self) -> str:
        return str(self.data)


def main():
    lang = 'en_US'  # feel free to download other languages or dictionaries
    dict_filename = f"ipa-dict-{lang}.json"
    spelling_to_pronunciations = IPADict.from_file(dict_filename, lang)

    phonetic_anagrams_dict = PhoneticAnagramDict.from_IPADict(spelling_to_pronunciations)

    anaphones = {}
    anaphones_unique_pronunciation = {}
    anaphones_nontrivial_unique_pronunciation = {}

    for pronounced_word in spelling_to_pronunciations.flatten_to_pronounced_words():
        anas = phonetic_anagrams_dict[pronounced_word.pronunciation]
        key_str = pronounced_word.json_safe_str()
        anaphones[key_str] = ', '.join([x.json_safe_str() for x in anas])

        anas = deduplicate_pronunciations(anas)
        joined_anas = ', '.join([x.json_safe_str() for x in anas])
        anaphones_unique_pronunciation[key_str] = joined_anas

        if len(anas) > 1:
            anaphones_nontrivial_unique_pronunciation[key_str] = joined_anas

    dicts_files = [(anaphones, "anaphones.json"),
                   (anaphones_unique_pronunciation, "anaphones_unique_pronunciation.json"),
                   (anaphones_nontrivial_unique_pronunciation, "anaphones_nontrivial_unique_pronunciation.json")]

    for d, filename in dicts_files:
        with open(filename, "w", encoding='utf-8') as f:
            print(f"writing file {filename}")
            json.dump(d, f, indent="\t", sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    import time
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    elapsed = end - start
    print(f'finished in {elapsed:.02f}s')
