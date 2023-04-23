#!/bin/python3
import re
import typing

def main() -> None:
    try:
        while True:
            sentence = input('Sentence: ')
            output: list[typing.Tuple[str, list[str]]] = []
            with open('amepd', 'rt', encoding='utf-8') as f:
                # Find each word in the sentence in the phenome dictionary
                for idx, word in enumerate(sentence.split(' ')):
                    word = word.lower()
                    output.append((word, []))

                    # Remove chars such as '!', '?', '.' and ',' from the end of the word.
                    specialChars, word = removeSpecialChars(word)
                    # handle special pronunciations first
                    output[idx] = (word, handleSpecialCases(word))

                    if len (output[idx][1]) == 0:
                        f.seek(0x00) # Start of file
                        while origLine := f.readline():
                            line = origLine.strip()
                            if line.startswith(';;;'):
                                continue
                            line = line.lower()
                            line = re.sub(r'\(.+\)', '', line)  # multiple pronounciations are marked word(1) ... word(2)
                            line = re.sub('#.*$', '', line)     # comments are marked with WORD  XX XX XX #@@ { usecase: ...}
                            line = line.strip()
                            if line.split(' ')[0] == word:
                                phenomes = ' '.join(line.split(' ')[2:])
                                # print(f'Found: {word}: {phenomes}')
                                # words are separated from phenomes by a double space.
                                parsedPhenomes = parsePhenomeLine(phenomes)
                                if parsedPhenomes not in output[idx][1]:
                                    output[idx][1].append(parsedPhenomes)
                        if len(output[idx][1]) == 0:
                            print(f'Error: Could not find word "{word}" in dictionary.')
                            output[idx][1].append(word)
                        elif len(output[idx][1]) > 1:
                            print(f'Warning: Found multiple matches for {word}:\n{output[idx]}')

                    # re-append special characters.
                    for x in range(0, len(output[idx][1])):
                        output[idx][1][x] += specialChars[::-1]
            # print(f'{output=}')
            for x in output:
                # x is (word, [['ph1', 'ph2'], ['altph1', 'altph2']])
                for y in x[1][0]:
                    print(f'{"".join(y)}', end='')
                print(' ', end='')
            print()
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    return

def removeSpecialChars(word: str) -> (str, str):
    specialChars = ''
    # Run through the word backwards so that only special chars at the very end are considered
    # So that words such as "w,.or!d" don't end up as "word,.!",
    # but still allow for multiple chars like that.
    for c in word[::-1]:
        if c == '?':
            specialChars += '?'
        elif c == '.':
            specialChars += '.'
        elif c == '!':
            specialChars += '!'
        elif c == ',':
            specialChars += ','
        else:
            break

    # Need special case because word[:0] is empty.
    return specialChars, (word[:-1*len(specialChars)] if len(specialChars) > 0 else word)

def handleSpecialCases(word: str) -> list[list[str]]:
    # special cases to match game
    if word == 'a':
        return [['-', 'u']]
    if word == 'the':
        return [['dh', 'u']]

    # multiple matches
    if word == 'to':
        return [['t', 'oo']]
    if word == 'get':
        return [['g', 'e', 't']]
    if word == 'of':
        return [['v', 'u', '_']]
    if word == 'use':
        return [['y', 'oo', 's']]
    if word == 'uses':
        return [['y', 'oo', 's', 'i', 'z']]
    return []

def parsePhenomeLine(line: str) -> str:
    line = line.upper()
    line = concatPhenomes(line)
    prevWasConsonant = False        # Was the previous phenome a consonant?
    prevWasVowel = False            # Was the previous phenome a vowel?
    isNewCompound = True            # Must I create a new compound (true) or can I make a compound (false) with what's there?
    output = []
    # Consonant vowel -> Normal
    # Vowel consonant -> Inverted + _
    # Vowel, no consonant (Vowel or End) -> -V1, new sylable
    phenomeList = line.split(' ')
    phenomeAmount = len(phenomeList)
    specialInsertCount = 0
    for idx, phenome in enumerate(phenomeList):
        # print(f'{phenome=}, {output=}, {prevWasVowel=}, {prevWasConsonant=}, {isNewCompound=}')
        if phenome in phenomeDictConsonants:
            tunicPhenome = phenomeDictConsonants[phenome]

            if prevWasConsonant:
                # Can't compound with another consonant.
                isNewCompound = True

            if isNewCompound:
                output.append(tunicPhenome)
                isNewCompound = False
            elif prevWasVowel:
                # compounding with previous vowel requires inversion
                output.insert(idx+specialInsertCount-1, tunicPhenome)
                output.append('_')
                specialInsertCount += 1
                isNewCompound = True
            else:
                # Start of word
                output.append(tunicPhenome)
                isNewCompound = False
            prevWasConsonant = True
            prevWasVowel = False
        elif phenome in phenomeDictVowels:
            tunicPhenome = phenomeDictVowels[phenome]

            if prevWasVowel:
                # Can't compound with another vowel
                isNewCompound = True

            if isNewCompound:
                if idx+1 == phenomeAmount or phenomeList[idx+1] in phenomeDictVowels:
                    # Can't compound it with the next phenome (is another vowel or end of word)
                    # so it needs a vowel carrier
                    output.append('-')
                    specialInsertCount += 1
                    isNewCompound = True
                else:
                    # Can compound with the next phenome
                    isNewCompound = False
                output.append(tunicPhenome)
            else:
                # Start of word or compounding with previous consonant
                output.append(tunicPhenome)
                isNewCompound = True
            prevWasConsonant = False
            prevWasVowel = True
        else:
            print(f'Error: No such phenome defined {phenome}.')
        idx += 1
    return output

def concatPhenomes(line: str) -> str:
    line = re.sub('AE0 R', 'AE0R', line)
    line = re.sub('AE1 R', 'AE1R', line)
    line = re.sub('AE2 R', 'AE2R', line)
    line = re.sub('IH0 R', 'IH0R', line)
    line = re.sub('IH1 R', 'IH1R', line)
    line = re.sub('IH2 R', 'IH2R', line)
    line = re.sub('EH0 R', 'EH0R', line)
    line = re.sub('EH1 R', 'EH1R', line)
    line = re.sub('EH2 R', 'EH2R', line)
    line = re.sub('AO0 R', 'AO0R', line)
    line = re.sub('AO1 R', 'AO1R', line)
    line = re.sub('AO2 R', 'AO2R', line)
    return line

phenomeDictVowels = {
    'AX': 'a',      # About
    'AE0':'a',      # Abdomen
    'AE1': 'a',     # hAt
    'AE2': 'a',     # Aberration
    'AE0R': "ar",   # N/A
    'AE1R': "ar",   # fAR
    'AE2R': "ar",   # ARamaic
    'AA0': 'ah',    # pythOn
    'AA1': 'ah',    # abbOt
    'AA2': 'ah',    # abOmination
    'AO0': 'ah',    # acOrn
    'AO1': 'ah',    # lAW
    'AO2': 'ah',    # airlOck
    'AO0R': 'or',   # achORd
    'AO1R': 'or',   # mORE
    'AO2R': 'or',   # airbORne
    'EY0': 'ey',    # ajAY
    'EY1': 'ey',    # hEY
    'EY2': 'ey',    # airplAne
    'EH0': 'e',     # aesthetic
    'EH1': 'e',     # pet
    'EH2': 'e',     # access
    'EH0R': 'er',   # aerobic
    'EH1R': 'er',   # air
    'EH2R': 'er',   # adversary
    'IY0': 'ee',    # any
    'IY1': 'ee',    # meet
    'IY2': 'ee',    # appleseed
    'AH0': 'u',     # product
    'AH1': 'u',     # sunny
    'AH2': 'u',     # backup
    'IH0': 'i',     # abolish
    'IH1': 'i',     # hit
    'IH2': 'i',     # thing
    'IH0R': 'eer',  # berate
    'IH1R': 'eer',  # beer
    'IH2R': 'eer',  # atmosphere
    'AY0': 'ie',    # ailene (name)
    'AY1': 'ie',    # pie
    'AY2': 'ie',    # acolyte
    'AXR': 'ir',    # backwards
    'ER0': 'ir',    # twitter
    'ER1': 'ir',    # bird
    'ER2': 'ir',    # artwork
    'OW0': 'o',     # aero
    'OW1': 'o',     # toe
    'OW2': 'o',     # alcove
    'OY0': 'oy',    # conroy
    'OY1': 'oy',    # toy
    'OY2': 'oy',    # airfoil
    'UW0': 'oo',    # accusation
    'UW1': 'oo',    # toon
    'UW2': 'oo',    # absolute
    'UH0': 'ou',    # arthur (name)
    'UH1': 'ou',    # book
    'UH2': 'ou',    # adulthood
    'AW0': 'ow',    # birdhouse
    'AW1': 'ow',    # how
    'AW2': 'ow',    # airpower
}

phenomeDictConsonants = {
    'B': 'b',       # bat
    'CH': 'ch',     # chat
    'D': 'd',       # debt
    'F': 'f',       # fret
    'G': 'g',       # get
    'HH': 'h',      # hat
    'JH': 'j',      # jet
    'K': 'k',       # kid
    'L': 'l',       # let
    'M': 'm',       # met
    'N': 'n',       # net
    'NG': 'ng',     # king
    'P': 'p',       # pet
    'R': 'r',       # rat
    'S': 's',       # sat
    'SH': 'sh',     # ship
    'T': 't',       # tent
    'TH': 'th',     # thin
    'DH': 'dh',     # this
    'V': 'v',       # vet
    'W': 'w',       # wet
    'Y': 'y',       # yet
    'Z': 'z',       # zit
    'ZH': 'zh',     # casual
}


if __name__ == '__main__':
    main()
