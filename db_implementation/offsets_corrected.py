import re
import json

def replace_punc(clean_text, offset, start_offset_list, end_offset_list):
    poss_diff = 0
    dash_diff = 0
    s = clean_text
    s, off1 = re.subn(' \\.', '.', s)
    s, off2 = re.subn(' ,', ',', s)
    s, off3 = re.subn(' ;', ';', s)
    s, off4 = re.subn(' :', ':', s)
    s, off5 = re.subn(' POSS', '\'s', s)
    s, off6 = re.subn(' n\'t', 'n\'t', s)
    s, off7 = re.subn(' %', '%', s)
    s, off8 = re.subn('\\$ ', '$', s)
    s, off8 = re.subn('  --  ', ' -- ', s)
    s, off9 = re.subn('\\( ', '(', s)
    s, off10 = re.subn(' \\)', ')', s)
    s, off11 = re.subn(' !', '!', s)
    s, off12 = re.subn(' \\?', '?', s)
    if off8 == 1:
        dash_diff = 2
    if off5 == 1:
        poss_diff = 3
    adjust_val = off1 + off2 + off3 + off4 + poss_diff + off6 + off7 + dash_diff + off9 + off10 + off11 + off12
    offset -= adjust_val
    if off1 + off2 + off3 + off4 + poss_diff + off6 + off7 + dash_diff + off9 + off10 + off11 + off12 > 0:
        start_offset_list[-1] -= adjust_val
        end_offset_list[-1] -= adjust_val
    return s, offset, start_offset_list, end_offset_list

def quote_helper(offset, start_offset_list, end_offset_list, quote_bool, index, clean_text, w_text):
    if not quote_bool:
        #if first quote
        #when only one quote is present and it's the last one in the sentence
        if index == len(w_text)-1:
            clean_text += w_text[index]
            start_offset_list.append(offset)
            end_offset_list.append(offset)
            offset += 1
            return offset, start_offset_list, end_offset_list, quote_bool, index, clean_text, w_text
        clean_text += ' ' + w_text[index] + w_text[index+1]
        offset += 1
        #for the quote
        start_offset_list.append(offset)
        end_offset_list.append(offset)
        offset += len(w_text[index])
        #for start of the word
        start_offset_list.append(offset)

        #for the word itself
        index+=1
        offset += len(w_text[index])
        #end of the word
        end_offset_list.append(offset-1)
        quote_bool = True
    else:
        #if second quote
        clean_text += w_text[index]
        start_offset_list.append(offset)
        end_offset_list.append(offset)
        offset += 1
        quote_bool = False
    return offset, start_offset_list, end_offset_list, quote_bool, index, clean_text, w_text

#returns clean text and offset_list that contains the start offset of every token in the clean text, given a list of tokens that comprise the clean text
# w_head is needed just to check if the head is only one single quote, which sometimes occurs
def assemble_tokens(w_text, w_head):
    clean_text = ''
    offset = 0
    start_offset_list = [0]
    end_offset_list = []
    index = 0
    in_double_quote = False
    in_single_quote = False
    while index < len(w_text):
        if (index == 0):
            #if first index is quote:
            if w_text[index] == '"':
                if len(w_head) == 1 and w_head[0] == '"':
                    clean_text += w_text[index]
                    offset += len(w_text[index])
                    end_offset_list.append(offset)
                    start_offset_list.append(offset)
                    return clean_text, start_offset_list, end_offset_list
                clean_text += w_text[index] + w_text[index+1]
                offset += len(w_text[index])
                start_offset_list.append(offset)
                end_offset_list.append(offset)

                #for the word itself
                index+=1
                offset += len(w_text[index])
                in_double_quote = True
            else:
                clean_text += w_text[index]
                offset += len(w_text[index])
                end_offset_list.append(offset-1)
        elif w_text[index] == '"':
            offset, start_offset_list, end_offset_list, in_double_quote, index, clean_text, w_text = quote_helper(offset, start_offset_list, end_offset_list, in_double_quote, index, clean_text, w_text)
        elif w_text[index] == '\'':
            offset, start_offset_list, end_offset_list, in_single_quote, index, clean_text, w_text = quote_helper(offset, start_offset_list, end_offset_list, in_single_quote, index, clean_text, w_text)
        else:
            clean_text += ' '
            offset += 1
            start_offset_list.append(offset)
            clean_text += w_text[index]
            offset += len(w_text[index])
            end_offset_list.append(offset-1)
        clean_text, offset, start_offset_list, end_offset_list = replace_punc(clean_text, offset, start_offset_list, end_offset_list)
        index += 1
    return clean_text, start_offset_list, end_offset_list

#returns clean head, full clean text of sentence, and offset list
def return_clean_head(w_text, w_head, w_head_span):
    head = ''
    punc_list = ['.', ',', ';', ':', '\"', '\'', '!', '?']
    for ind in range(len(w_text)):
        if w_text[ind] == '\'s':
            w_text[ind] = "POSS"
    clean, start_offset_list, end_offset_list = assemble_tokens(w_text, w_head)
    w_start, w_end = w_head_span
    #if head is whole sentence
    if w_start == w_end:
        return head, clean, start_offset_list, end_offset_list
    s_head = start_offset_list[w_start]
    #if rest of sentence is part of head, prevents list index out of range error
    if w_end == len(start_offset_list):
        return clean[s_head:], clean, start_offset_list, end_offset_list
    else:
        e_head = start_offset_list[w_end]

    #deal with punctuation since they won't have spaces before them (commas will be two spaces away, quotes one space away)
    if start_offset_list[-1] == e_head or clean[start_offset_list[w_end+1]-2] in punc_list or clean[start_offset_list[w_end+1]-1] in punc_list:
        #if punctuation is last character in the sentence, you want to include it
        if w_head[-1] in punc_list and w_text[-1] == w_head[-1]:
            head = clean[s_head:]
        else:
            head = clean[s_head:e_head]
    else:
        head = clean[s_head:e_head-1]
    return head, clean, start_offset_list, end_offset_list

#NEW CODE TO RETURN FIRST AND LAST OFFSET FOR MENTIONS TABLE
def first_last_offset(w_head_span, start_offset_list, end_offset_list):
    w_head_start, w_head_end = w_head_span
    first_offset = start_offset_list[w_head_start]
    if w_head_end >= len(start_offset_list):
        end_offset = end_offset_list[-1]
    else:
        end_offset = end_offset_list[w_head_end]
    return first_offset, end_offset

def testing(l_bound, limit, data):
    count = 0
    for obj in data:
        w_text = obj['w_text']
        w_head = obj['w_head']
        w_head_span = obj['w_head_span']
        if count > limit:
            break
        if count < l_bound:
            count += 1
            continue
        head, clean, offset_list = return_clean_head(w_text, w_head, w_head_span)
        print('-------------------------------------------------------')
        print(clean)
        print('ORIGINAL:', obj['clean_head'])
        print('     NEW:', head)
        count += 1

if __name__ == '__main__':
    #f = open('/Users/justinchen/Desktop/GitHub/unified-mpqa/db_implementation/mpqa_csds.json', 'r', encoding='utf-8')
    #data = json.load(f)
    w_text = [
                "But",
                "the",
                "political",
                "classes",
                "in",
                "the",
                "United",
                "States",
                ",",
                "and",
                "not",
                "only",
                "they",
                ",",
                "consider",
                "America",
                "as",
                "something",
                "special",
                ",",
                "as",
                "\"",
                "God",
                "'s",
                "own",
                "country",
                ".",
                "\""
            ]
    w_head = [
                "something",
                "special",
                ",",
                "as",
                "\"",
                "God",
                "'s",
                "own",
                "country",
                ".",
                "\""
            ]
    w_head_span = [17, 28]
    head, clean, start_offset_list, end_offset_list = return_clean_head(w_text, w_head, w_head_span)
    print(head, clean)
    print(first_last_offset(w_head_span, start_offset_list, end_offset_list))



    #testing(0,100, data)