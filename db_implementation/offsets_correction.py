import re


class OffsetsCorrection:

    def replace_punc(self, clean_text, offset, start_offset_list, end_offset_list):
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

    @staticmethod
    def quote_helper(offset, start_offset_list, end_offset_list, quote_bool, index, clean_text, w_text):
        if not quote_bool:
            # when only one quote is present and it's the last one in the sentence
            if index == len(w_text) - 1:
                clean_text += w_text[index]
                start_offset_list.append(offset)
                end_offset_list.append(offset + 1)
                offset += 1
                return offset, start_offset_list, end_offset_list, quote_bool, index, clean_text, w_text
            clean_text += ' ' + w_text[index] + w_text[index + 1]
            offset += 1
            # for the quote
            start_offset_list.append(offset)
            end_offset_list.append(offset + 1)
            offset += len(w_text[index])
            # for start of the word
            start_offset_list.append(offset)

            # for the word itself
            index += 1
            offset += len(w_text[index])
            # end of the word
            end_offset_list.append(offset)
            quote_bool = True
        else:
            clean_text += w_text[index]
            start_offset_list.append(offset)
            end_offset_list.append(offset + 1)
            offset += 1
            quote_bool = False
        return offset, start_offset_list, end_offset_list, quote_bool, index, clean_text, w_text

    # returns clean text and offset_list that contains the start offset of every token in the clean text, given a list of tokens that comprise the clean text
    # w_head is needed just to check if the head is only one single quote, which sometimes occurs
    def assemble_tokens(self, w_text, w_head):
        clean_text = ''
        offset = 0
        start_offset_list = [0]
        end_offset_list = []
        index = 0
        in_double_quote = False
        in_single_quote = False
        while index < len(w_text):
            if (index == 0):
                # if first index is quote:
                if w_text[index] == '"':
                    if len(w_head) == 1 and w_head[0] == '"':
                        clean_text += w_text[index]
                        offset += len(w_text[index])
                        end_offset_list.append(offset + 1)
                        start_offset_list.append(offset)
                        return clean_text, start_offset_list, end_offset_list
                    clean_text += w_text[index] + w_text[index + 1]
                    offset += len(w_text[index])
                    start_offset_list.append(offset)
                    end_offset_list.append(offset + 1)

                    # for the word itself
                    index += 1
                    offset += len(w_text[index])
                    in_double_quote = True
                else:
                    clean_text += w_text[index]
                    offset += len(w_text[index])
                    end_offset_list.append(offset)
            elif w_text[index] == '"':
                offset, start_offset_list, end_offset_list, in_double_quote, index, clean_text, w_text = (
                    self.quote_helper(offset, start_offset_list, end_offset_list, in_double_quote, index,
                                      clean_text, w_text))
            elif w_text[index] == '\'':
                offset, start_offset_list, end_offset_list, in_single_quote, index, clean_text, w_text = (
                    self.quote_helper(offset, start_offset_list, end_offset_list, in_single_quote, index,
                                      clean_text, w_text))
            else:
                clean_text += ' '
                offset += 1
                start_offset_list.append(offset)
                clean_text += w_text[index]
                offset += len(w_text[index])
            clean_text, offset, start_offset_list, end_offset_list = self.replace_punc(clean_text, offset,
                                                                                       start_offset_list,
                                                                                       end_offset_list)
            index += 1
        return clean_text, start_offset_list, end_offset_list

    # returns clean head, full clean text of sentence, and offset list
    def return_clean_head(self, w_text, w_head, w_head_span):
        head = ''
        punc_list = ['.', ',', ';', ':', '\"', '\'', '!', '?']
        for ind in range(len(w_text)):
            if w_text[ind] == '\'s':
                w_text[ind] = "POSS"
        clean, start_offset_list, end_offset_list = self.assemble_tokens(w_text, w_head)

        w_start, w_end = w_head_span
        # if head is whole sentence
        if w_start == w_end:
            return head, clean, start_offset_list, end_offset_list
        s_head = start_offset_list[w_start]
        # if rest of sentence is part of head, prevents list index out of range error
        if w_end == len(start_offset_list):
            return clean[s_head:], clean, start_offset_list, end_offset_list
        else:
            e_head = start_offset_list[w_end]

        # deal with punctuation since they won't have spaces before them
        # (commas will be two spaces away, quotes one space away)
        if (start_offset_list[-1] == e_head or clean[start_offset_list[w_end + 1] - 2] in punc_list
                or clean[start_offset_list[w_end + 1] - 1] in punc_list):
            # if punctuation is last character in the sentence, you want to include it
            if w_head[-1] in punc_list and w_text[-1] == w_head[-1]:
                head = clean[s_head:]
            else:
                head = clean[s_head:e_head]
        else:
            head = clean[s_head:e_head - 1]
        return head, clean, start_offset_list, end_offset_list

    @staticmethod
    # NEW CODE TO RETURN FIRST AND LAST OFFSET FOR MENTIONS TABLE
    def first_last_offset(w_head_span, start_offset_list, end_offset_list, clean_text):
        w_head_start, w_head_end = w_head_span

        if w_head_start >= len(start_offset_list) or len(end_offset_list) == 0:
            return -2, -2

        first_offset = start_offset_list[w_head_start]
        if w_head_end >= len(start_offset_list):
            end_offset = start_offset_list[-1]
        else:
            end_offset = start_offset_list[w_head_end]

        if (first_offset, end_offset) == (0, 0):
            print('hmm')

        return first_offset, end_offset


        # if w_head_end >= len(end_offset_list):
        #     end_offset = end_offset_list[-1]
        # else:
        #     end_offset = end_offset_list[w_head_end]
        #
        # pred_head = clean_text[first_offset:end_offset]
        #
        # return first_offset, end_offset
