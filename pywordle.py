# -*- coding: utf-8 -*-
"""
Created on Mon Jan 10 18:01:49 2022

@author: Connor
"""

import numpy as np
from collections import defaultdict

#%% Prune files and add to main database

# with open("wordle_data.txt", "r") as fh:
#     lines = fh.readlines()

# with open("wordle_data2.txt", "r") as fh:
#     lines2 = fh.readlines()

# for ii, line in enumerate(lines):
#     lines[ii] = line.rstrip()

# for ii, line in enumerate(lines2):
#     lines2[ii] = line.rstrip()

# lines2 = sorted(lines2)

# for item in lines2:
#     if item not in lines:
#         lines.append(item)

# lines = sorted(lines)
# with open("wordle_data_total.txt", "w") as fh:
#     print(*lines, sep="\n", file=fh)

#%% Load Data
with open("wordle_data_total.txt", "r") as fh:
    lines = fh.readlines()

for ii, line in enumerate(lines):
    lines[ii] = line.rstrip()

#%% Determine Best Guesses

vowels = "aeiouy"
decent_words = []

for ii, word in enumerate(lines):
    stop_flag = False
    cc = 0
    # Assert no duplicate letters
    for ll in word:
        if word.count(ll) > 1:
            stop_flag = True

    # Assert all "decent" words have 3 vowels
    if not stop_flag:
        for vv in vowels:
            cc += word.count(vv)
            
        if cc < 3:
            stop_flag = True
    
    # If the word is valid, add it and keep going
    if not stop_flag:
        decent_words.append(word)

# Best guesses seemingly are:
# "ABUSE" & "IRONY" as a pair to cover 10 letters, 6 vowels

#%% Get most common letter in each slot
def get_decent_words(words_list):
    def r0():
        return 0
    
    d0 = defaultdict(r0)
    d1 = defaultdict(r0)
    d2 = defaultdict(r0)
    d3 = defaultdict(r0)
    d4 = defaultdict(r0)
    dd = [d0, d1, d2, d3, d4]
    l_list = [list() for i in range(5)]
    
    for word in words_list:
        for ii in range(0,5):
            if ii == 0:
                d0[word[ii]] += 1
            elif ii == 1:
                d1[word[ii]] += 1
            elif ii == 2:
                d2[word[ii]] += 1
            elif ii == 3:
                d3[word[ii]] += 1
            elif ii == 4:
                d4[word[ii]] += 1
    
    for ii, d in enumerate(dd):
        l_list[ii] = sorted(d.items(),key=lambda x: x[1], reverse=True)
    
    #% Score the Words
    dd_talley = defaultdict(r0)
    for jj, word in enumerate(words_list):
        dd_talley[word] = 0
        for ii in range(0,5):
            if ii == 0:
                dd_talley[word] += d0[word[ii]]
            elif ii == 1:
                dd_talley[word] += d1[word[ii]]
            elif ii == 2:
                dd_talley[word] += d2[word[ii]]
            elif ii == 3:
                dd_talley[word] += d3[word[ii]]
            elif ii == 4:
                dd_talley[word] += d4[word[ii]]
    
    vals = sorted(dd_talley.items(),key=lambda x: x[1], reverse=True)
    return vals


#%% Find best match

def find_best_match(qword):
    """
    Find best match will look in the overall list of words in the database and 
    determine the best matching word. Returns None if there isn't a match.
    
    Use "*" as the wildcard character.
    """
    if len(qword) != 5 and ";" not in qword and "-" not in qword:
        raise ValueError(f"Word {qword} is not 5 characters long.")
    elif ";" in qword or "-" in qword:
        if ";" in qword and "-" in qword:
            if qword.index(";") > qword.index("-"):
                raise ValueError(f"Word {qword} must have ';' before '-'.")
            else:
                qword, knowns = qword.split(";")
                knowns, rms = knowns.split("-")

        elif ";" in qword and "-" not in qword:
            if len(qword.split(";")[0]) != 5:
                raise ValueError(f"Word {qword.split(';')[0]} is not 5 characters long.")
            else:
                qword, knowns = qword.split(";")
                rms = ""
        else:
            # "-" in qword and ";" not in qword
            if len(qword.split("-")[0]) != 5:
                raise ValueError(f"Word {qword.split('-')[0]} is not 5 characters long.")
            else:
                qword, rms = qword.split("-")
                knowns = ""
    else:
        knowns = ""
        rms = ""
    
    qword = qword.lower()
    knowns = knowns.lower()
    rms = rms.lower()    
    
    wildcards = [cc == "*" for cc in qword]
    remaining_words = []
    
    for ii, word in enumerate(lines):
        stop_flag = False
        for jj, cc in enumerate(qword):
            if not wildcards[jj]:
                stop_flag |= word[jj].lower() != qword[jj].lower()
        
        if not stop_flag:
            for jj, cc in enumerate(knowns):
                stop_flag |= cc not in word
        
        for jj, rr in enumerate(rms):
            stop_flag |= rr in word
        # If the word is valid, add it and keep going
        if not stop_flag:
            remaining_words.append(word)
    
    return remaining_words

def mark_correct(word, inword, guess):
    def r0():
        return 0
    dd = defaultdict(r0)
    for cc in word:
        dd[cc] += 1
    for ii, cc in enumerate(inword):
            if word[ii] == cc:
                guess[ii] = 1
                dd[cc] -= 1
        
    return guess, dd

def mark_within(word, inword, guess, dd):   
    for ii, cc in enumerate(inword):
        if word.count(cc) ==  inword.count(cc): # and word.count(cc) > 0
            # mark all
            if word[ii] != cc: # and inword[ii] == cc
                guess[ii] = 2
                dd[cc] -= 1
        elif word.count(cc) < inword.count(cc):
            if word[ii] != cc and dd[cc]: # and inword[ii] == cc
                guess[ii] = 2
                dd[cc] -= 1
        else:
            if word[ii] != cc: # and inword[ii] == cc
                guess[ii] = 2
                dd[cc] -= 1
    return guess
                
def run_game():
    word = lines[np.random.randint(0, len(lines))]
    
    num_guesses = 0
    
    win_flag = False
    while num_guesses < 6 and not win_flag:
        inword = input(f"What is your guess? {6-num_guesses} guesses left!\n")
        if len(inword) != 5:
            print("Incorrect length, try again.")
            continue
        if inword not in lines:
            print("Invalid word, try again.")
            continue

        guess = np.zeros((5,))
        guess, dd = mark_correct(word, inword, guess)
        guess = mark_within(word, inword, guess, dd)
        
        print(guess)
        num_guesses+=1
        win_flag = inword == word
    if win_flag:
        print(f"You got it in {num_guesses} tries! The word was:", word)
    else:
        print("Nice try, the word was: ", word)

def main():
    # return find_best_match("*R*N*;I")
    guess = np.zeros((5,))
    word = "abbey"
    inword = "aargh"
    guess, dd = mark_correct(word, inword, guess)
    print(guess)
    guess = mark_within(word, inword, guess, dd)
    print(guess)
    
    get_decent_words(decent_words)
    
if __name__ == "__main__":
    a = main()