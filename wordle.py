# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 12:17:21 2022

@author: Connor
"""

import re
import numpy as np
import h5py

from collections import defaultdict
from copy import deepcopy
#%% Load Data
with open("wordles.txt", "r") as fh:
    wordles = fh.readlines()

for ii, line in enumerate(wordles):
    wordles[ii] = line.rstrip()
    
with open("valid_words.txt", "r") as fh:
    valid_words = fh.readlines()

for ii, vword in enumerate(valid_words):
    valid_words[ii] = vword.rstrip()    

valid_words.extend(wordles)

valid_words_str = "\n".join(valid_words) + "\n"
wordles_str = "\n".join(wordles) + "\n"

wordle_map = {}
with h5py.File("wordle_map.h5", "r") as fh:
    for key, value in fh.items():
        wordle_map[key] = value[()]

def parse_knowns(knowns: str):
    rEL = lambda : list()

    kd = defaultdict(rEL)
    for ii, cc in enumerate(knowns):
        if cc.isalpha():
            jj = ii+1
            cont_flag = jj < len(knowns)
            while jj < len(knowns) and cont_flag:
                if knowns[jj].isnumeric():
                    kd[cc].append(int(knowns[jj]))
                else:
                    cont_flag = False
                jj += 1
    return kd

def parse_info_string(qword):
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
    knowns = parse_knowns(knowns.lower())
    rms = rms.lower()    
    
    return qword, knowns, rms

def make_info_string(qword, knowns, rms):
    k_str = ""
    for key, value in sorted(knowns.items()):
        k_str += f"{key}" + "".join(str(v) for v in sorted(value))
    
    if k_str and rms:
        return qword + ";" + k_str + "-" + "".join(str(r) for r in sorted(rms))
    elif k_str and not rms:
        return qword + ";" + k_str
    elif rms and not k_str:
        return qword + "-" + "".join(str(r) for r in sorted(rms))
    else:
        return qword
        

def find_remaining_words(guess_flag, *args):
    if len(args) == 1:
        qword, knowns, rms = parse_info_string(args[0])
    elif len(args) == 3:
        qword, knowns, rms = args
    else:
        raise ValueError(f"Improper length for {args}: {len(args)}")
    
    if rms or knowns:
        ll = list(("", "", "", "", ""))
    else:
        ll = list((".", ".", ".", ".", "."))
    
    if rms and knowns:
        # rms
        for ii, item in enumerate(ll):
            ll[ii] = f"[^{rms}]"
        
        # knowns
        for key, value in knowns.items():
            for jj in value:
                ll[jj] = ll[jj][0:-1] + key + ll[jj][-1]
    elif rms and not knowns:
        # rms
        for ii, item in enumerate(ll):
            ll[ii] = f"[^{rms}]"
    elif knowns and not rms:
        # knowns
        for key, value in knowns.items():
            for jj in value:
                if not ll[jj]:
                    ll[jj] = "[^]"
                ll[jj] = ll[jj][0:-1] + key + ll[jj][-1]
    else:
        pass
    for ii, item in enumerate(ll):
        if not item:
            ll[ii] = "."
    
    for kk, cc in enumerate(qword):
        if cc.isalpha():
            ll[kk] = cc
    
    pttrn = "".join(ll) + r"\s"
    pattern = re.compile(pttrn)
    if guess_flag:
        new_valid_words = pattern.findall(valid_words_str)
    else:
        new_valid_words = pattern.findall(wordles_str)
    
    badword_list = list()
    for key, value in knowns.items():
        for vword in new_valid_words:
            if key not in vword and vword not in badword_list:
                badword_list.append(vword)
    
    for bword in badword_list:
        new_valid_words.remove(bword)
                
    return new_valid_words

def mark_correct(word, inword, guess):
    r0 = lambda : 0
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

def mark_guesses(word, inword):
    guess = np.zeros((5,))
    guess, dd = mark_correct(word, inword, guess)
    return mark_within(word, inword, guess, dd)

def process_move(wordle, guess, word_str, knowns, rms):
    """
    Takes in the word and guess, and returns the new 
    qword, knowns, and rms
    """
    guesses = mark_guesses(wordle, guess)
    for ii, val in enumerate(guesses):
        cc = guess[ii]
        if val == 0:
            if cc not in knowns and cc not in rms:
                # If it isn't in knowns or rms already
                # Add "0"s to rms
                rms += cc
            else:
                # if it is in knowns, not in rms
                if cc in knowns:
                    # Add the potential knew index to the knowns dict
                    if ii not in knowns[cc]:
                        knowns[cc].append(ii)
        if val == 1:
            if word_str[ii] == "*" or word_str[ii] == ".":
                word_str = word_str[0:ii] + cc + word_str[ii+1:]
            else:
                assert word_str[ii] == cc
        
        if val == 2:
            # Add the potential knew index to the knowns dict
            if ii not in knowns[cc]:
                knowns[cc].append(ii)
    return word_str, knowns, rms
    

def find_best_guess(*args):
    if len(args) == 1:
        qword, knowns, rms = parse_info_string(args[0])
    elif len(args) == 3:
        qword, knowns, rms = args
    else:
        raise ValueError(f"Improper length for {args}: {len(args)}")
    rem_words = find_remaining_words(False, qword, knowns, rms)
    rem_guesses = find_remaining_words(True, ".....")
    
    guesses = defaultdict(lambda : list())
    for jj, guess in enumerate(rem_guesses):
        for wordle in rem_words:
            new_qword, new_knowns, new_rms = process_move(wordle.strip(), guess.strip(), deepcopy(qword), deepcopy(knowns), deepcopy(rms))
            new_words = find_remaining_words(False, new_qword, new_knowns, new_rms)
            if new_words:
                guesses[guess].append(len(new_words))
        progress = jj*100 / len(rem_guesses)
        print(f"{progress}%")
    
    for guess, value in guesses.items():
        guesses[guess] = sum(value) / len(value)
    
    # sort the items into key, value tuples, sorted by value
    vals = sorted(guesses.items(),key=lambda x: x[1])
    
    # Filter for only valid wordles
    ff = filter(lambda x: x[0].strip() in wordles, vals)
    items = [item for item in ff]
    # If there isn't a valid wordle somehow, just return vals
    if items:
        # otherwise return the valid items
        return items
    else:
        return vals

def run_game():
    word = wordles[np.random.randint(0, len(wordles))]
    num_guesses = 0
    win_flag = False
    while num_guesses < 6 and not win_flag:
        inword = input(f"What is your guess? {6-num_guesses} guesses left!\n")
        if len(inword) != 5:
            print("Incorrect length, try again.")
            continue
        if inword not in valid_words:
            print("Invalid word, try again.")
            continue

        guess = mark_guesses(word, inword)
        
        print(guess)
        num_guesses+=1
        win_flag = inword == word
    if win_flag:
        print(f"You got it in {num_guesses} tries! The word was:", word)
    else:
        print("Nice try, the word was: ", word)

def solve_all():
    output_dict = {}
    for wordle in wordles:
        num_guesses = solve(wordle)
        output_dict[wordle] = num_guesses
        
    return output_dict

def solve(wordle):
    qword = "....."
    knowns = defaultdict(lambda : list())
    rms = ""
    num_guesses = 0
    done_flag = False
    while num_guesses < 8 and not done_flag:
        i_str = make_info_string(deepcopy(qword), deepcopy(knowns), deepcopy(rms))
        
        if i_str not in wordle_map:
            # Next, use that info to get the next best guess
            out = find_remaining_words(True, deepcopy(qword), deepcopy(knowns), deepcopy(rms))
            out2 = find_best_guess(deepcopy(qword), deepcopy(knowns), deepcopy(rms))
            out3 = [item for item in out2 if item[0] in out]
            
            if out3[0][1] == 1.0:
                this_guess = out3[0][0].strip()
            else:
                this_guess = out2[0][0].strip()
            
            wordle_map[i_str] = this_guess
        else:
            this_guess = wordle_map[i_str]
        
        qword, knowns, rms = process_move(wordle.strip(), this_guess, deepcopy(qword), deepcopy(knowns), deepcopy(rms))
        num_guesses += 1
        if "." not in qword:
            done_flag = True
    
    return num_guesses

def write_solve_data(data, filename = "NumGuessesPerSolve.txt"):
    with open(filename, "w") as tf:
        for key, value in data.items():
            print(key, value, file=tf)

def write_map():
    with h5py.File('wordle_map.h5', "w") as fh:
        for key, value in wordle_map.items():
            fh[key] = value

if __name__ == "__main__":
    # Put your guess in wordle (I usually start with SOARE)
    # If nothing, next best word is child
    # info string syntax is:
    # 5 characters that are either letters or "." for unknowns
    # if any yellow letters, add a ";" to the info string 
    # all knowns as are parsed as:
    # character NotCorrectIndexes
    # Any letters not in the word at all are added to the end of the string 
    # after a "-" charater.
    # Example: 
    # "s....;o1r24e3-flick"
    # says the first letter is for sure an S
    # there is an o, r, and e in the word 
    # (but not at indexes 1, 2 or 4, and 3 respectively)
    # and there are no "f", "l", "i", "c", or "k"s in the final word.
    info_str = "shar.-oetick"
    qword, knowns, rms = parse_info_string(info_str)
    i_str = make_info_string(deepcopy(qword), deepcopy(knowns), deepcopy(rms))
    if i_str not in wordle_map:
        out = find_remaining_words(False, qword)
        out2 = find_best_guess(qword)
        out3 = [item for item in out2 if item[0] in out]
        
        if out3[0][1] == 1.0:
            best_guess = out3[0][0].strip()
        else:
            best_guess = out2[0][0].strip()
    else:
        best_guess = wordle_map[i_str]
        
    print(best_guess)
        
    # a,b,c = process_move("humph", "aahed", ".....", defaultdict(lambda : list(), {"r": [3], "u": 0, "n": 1}), "soaeity")
    
    # This will go through the overall wordle map (and populate any not seen 
    # info_string states) to find a solution track.
    # exp_value = solve_all()
    # solve("waver")

    
