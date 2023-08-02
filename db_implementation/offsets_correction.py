import re


class OffsetsCorrection:
    @staticmethod
    def replace_punc(clean_text, offset, offset_list):
        poss_diff = 0
        s = clean_text
        s, off1 = re.subn(' \.', '.', s)
        s, off2 = re.subn(' ,', ',', s)
        s, off3 = re.subn(' ;', ';', s)
        s, off4 = re.subn(' :', ':', s)
        s, off5 = re.subn(' POSS', '\'s', s)
        if off5 == 1:
            poss_diff = 3
        adjust_val = off1 + off2 + off3 + off4 + poss_diff
        offset -= adjust_val
        if off1 + off2 + off3 + off4 + poss_diff > 0:
            offset_list[-1] -= adjust_val
        return s, offset, offset_list

    @staticmethod
    def quote_helper(offset, offset_list, quote_bool, index, clean_text, w_text):
        if not quote_bool:
            clean_text += ' ' + w_text[index] + w_text[index + 1]
            offset += 1
            offset_list.append(offset)
            offset += len(w_text[index])
            offset_list.append(offset)

            # for the word itself
            index += 1
            offset += len(w_text[index])
            quote_bool = True
        else:
            clean_text += w_text[index]
            offset_list.append(offset)
            offset += 1
            quote_bool = False
        return offset, offset_list, quote_bool, index, clean_text, w_text

    def assemble_tokens(self, w_text):
        clean_text = ''
        offset = 0
        offset_list = [0]
        index = 0
        in_double_quote = False
        in_single_quote = False
        while index < len(w_text):
            if index == 0:
                # if first index is quote:
                if w_text[index] == '"':
                    clean_text += w_text[index] + w_text[index + 1]
                    offset_list.append(offset)
                    offset += len(w_text[index])
                    offset_list.append(offset)

                    # for the word itself
                    index += 1
                    offset += len(w_text[index])
                    in_double_quote = True
                else:
                    clean_text += w_text[index]
                    offset += len(w_text[index])
            elif w_text[index] == '"':
                offset, offset_list, in_double_quote, index, clean_text, w_text = self.quote_helper(offset, offset_list,
                                                                                                    in_double_quote,
                                                                                                    index,
                                                                                                    clean_text, w_text)
            elif w_text[index] == '\'':
                offset, offset_list, in_single_quote, index, clean_text, w_text = self.quote_helper(offset, offset_list,
                                                                                                    in_single_quote,
                                                                                                    index,
                                                                                                    clean_text, w_text)
            else:
                clean_text += ' '
                offset += 1
                offset_list.append(offset)
                clean_text += w_text[index]
                offset += len(w_text[index])
            clean_text, offset, offset_list = self.replace_punc(clean_text, offset, offset_list)
            index += 1
        return clean_text, offset_list
