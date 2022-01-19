import numpy as np
from fuzzywuzzy import fuzz
from data_types import Stack


def SplitByCharacters(text, characters):
    split = []
    prev_index = 0
    for i in range(len(text)):
        char = text[i]
        if char in characters:
            split.append(text[prev_index:i])
            prev_index = i + 1
    split.append(text[prev_index:len(text)])
    return split


def EvaluateCalcWeight(a, b):
    return float(b) if a else 0


def EvaluateAddWeight(a, b):
    return a + b


def EvaluateNot(a):
    return not a


def EvaluateXOR(a, b):
    return a != b  # if booleans, != is xor


def EvaluateAND(a, b):
    return a and b


def EvaluateOR(a, b):
    return a or b


class Operators:
    operators = {}
    operators["AND"] = ["AND", "and", "&", "&&"]
    operators["NOT"] = ["NOT", "not", "-", "!"]
    operators["OR"] = ["OR", "or", "~", "||"]
    operators["XOR"] = ["XOR", "xor", "^"]
    pre_operators = ['+', '-', '!']
    all_operators = ['(', ')', 'CALCWEIGHT', 'ADDWEIGHT']
    for key in operators.keys():
        all_operators += operators[key]
    precedence = {
        "CALCWEIGHT": 1,
        "ADDWEIGHT": 2,
        "NOT": 3,
        "XOR": 4,
        "AND": 5,
        "OR": 6,
        "(": 7
    }
    arity = {
        "CALCWEIGHT": 2,
        "ADDWEIGHT": 2,
        "NOT": 1,
        "XOR": 2,
        "AND": 2,
        "OR": 2
    }
    evaluation_funcs = {
        "CALCWEIGHT": EvaluateCalcWeight,
        "ADDWEIGHT": EvaluateAddWeight,
        "NOT": EvaluateNot,
        "XOR": EvaluateXOR,
        "AND": EvaluateAND,
        "OR": EvaluateOR
    }


def IsOperator(text):
    return text in Operators.all_operators


def GetOperatorType(text):
    for key in Operators.operators.keys():
        if text in Operators.operators[key]:
            return key
    return None


def EvaluateOperator(operator, operands):
    return Operators.evaluation_funcs[operator](*operands)


def ReducePreOperators(word):
    # returns formatted expression, actual word
    char_1 = word[0]
    if char_1 in Operators.pre_operators:
        word = word[1:]
        if char_1 == '+':  # (+ means inclusive)
            formatted = word
        else:
            formatted = GetOperatorType(char_1) + ' ' + word
    else:
        formatted = word
    return formatted, word


def ConvertSearchText(text):
    # returns formatted search text, list of required tags
    tag_names = []
    split_text = text.split(" ")
    output = ""
    last_index = len(split_text) - 1
    for i, word in enumerate(split_text):
        start_brackets = 0
        end_brackets = 0
        for char in word:
            if char == '(':
                start_brackets += 1
            else:
                break
        for char in word[::-1]:
            if char == ')':
                end_brackets += 1
            else:
                break
        checked_word = word.replace('(', '')
        checked_word = checked_word.replace(')', '')
        if IsOperator(checked_word):
            output += start_brackets * '(' + GetOperatorType(
                checked_word) + end_brackets * ')' + ' '
        elif i < last_index:
            next_word = split_text[i + 1]
            if IsOperator(next_word):
                new_text, word = ReducePreOperators(
                    word.lower()[start_brackets:len(word) - end_brackets])
                output += start_brackets * '(' + new_text + end_brackets * ')' + ' '
                if word not in tag_names:
                    tag_names.append(word)
            else:
                new_text, word = ReducePreOperators(
                    word.lower()[start_brackets:len(word) - end_brackets])
                output += start_brackets * '(' + new_text + end_brackets * ')' + ' AND '
                if word not in tag_names:
                    tag_names.append(word)
        else:
            new_text, word = ReducePreOperators(
                word.lower()[start_brackets:len(word) - end_brackets])
            output += start_brackets * '(' + new_text + end_brackets * ')'
            if word not in tag_names:
                tag_names.append(word)
    return SplitText(output), tag_names


def SplitText(text):
    output = []
    word = ''
    max_index = len(text) - 1
    for i in range(len(text) + 1):
        if i > max_index:  # we let it iterate 1 more time to finish off
            if len(word) == 0:
                continue
        else:
            char = text[i]
            if char != ' ':
                word += char
                if char not in ['(', ')'] and (i >= max_index or text[i + 1]
                                               not in ['(', ')']):
                    continue
            elif len(word) == 0:
                continue
        output.append(word)
        word = ''
    return output


def InfixToPostfix(text):
    stack = Stack()
    output = []
    for word in text:
        if not IsOperator(word):
            output.append(word)
        elif word == '(':
            stack.push(word)
        elif word == ')':
            while (not stack.is_empty) and (stack.peek() != '('):
                output.append(stack.pop())
            if (not stack.is_empty) and (stack.peek() != '('):
                return False
            else:
                stack.pop()  # removes open bracket
        else:
            while (not stack.is_empty) and (Operators.precedence[stack.peek()]
                                            <= Operators.precedence[word]):
                output.append(stack.pop())
            stack.push(word)
    while not stack.is_empty:
        output.append(stack.pop())
    return output


def InsertValuesIntoQuery(query, values):
    new_query = []
    for word in query:
        if word in values.keys():
            new_query.append(values[word])
        else:
            new_query.append(word)
    return new_query


def EvaluatePostfix(postfix):
    if not isinstance(postfix, list):
        postfix = postfix.split(" ")
    stack = Stack()
    for word in postfix:
        if not IsOperator(word):
            stack.push(word)
        else:
            arity = Operators.arity[word]
            if len(stack) < arity:
                raise Exception("Invalid postfix expression input.")
            operands = []
            for i in range(arity):
                operands.append(stack.pop())
            # start from the right-most operand because of the stack structure (LIFO)
            operands = operands[::-1]
            new_expression = EvaluateOperator(word, operands)
            stack.push(new_expression)
    return stack.pop()


def ExtremeSearch(search_text):
    from SQL import GetTagIDsFromNames, GetAllItemTags
    search_text, inp_tags = ConvertSearchText(search_text)
    query = InfixToPostfix(search_text)
    tag_ids = GetTagIDsFromNames(inp_tags)
    for tag in inp_tags:
        if tag not in tag_ids.keys():
            return ("INVALID", "TAGS")
    matches = []
    data = GetAllItemTags()
    for item in data:
        values = {}
        for tag in tag_ids:
            if isinstance(tag_ids[tag], int):
                if tag_ids[tag] in item[1]:  # assuming form [itemID, tagIDs]
                    values[tag] = True
                else:
                    values[tag] = False
            else:
                values[tag] = False
                for match in tag_ids[tag]:
                    if match in item[1]:
                        values[tag] = True
                        break
        item_query = InsertValuesIntoQuery(query, values)
        if EvaluatePostfix(item_query):
            matches.append(item[0])  # assuming form [itemID, tagIDs]
    return matches


def CheckValidity(text):
    bracket_depth = 0
    for word in text:
        if IsOperator(word):
            if bracket_depth != 1 and word in (Operators.operators["OR"] +
                                               Operators.operators["XOR"]):
                return False  # ORs and XORs must be in brackets
        if word == "(":
            bracket_depth += 1
            if bracket_depth == 2:
                return False  # Max bracket depth = 1
        elif word == ")":
            bracket_depth -= 1
    if bracket_depth != 0:
        return False
    current_bracket = []
    for word in text:
        if word == "(":
            current_bracket = []
        elif word == ")":
            current_split = []
            max_len = len(current_bracket)
            for i in range(max_len + 1):
                if i != max_len:
                    inner_word = current_bracket[i]
                if i == max_len or (IsOperator(inner_word) and inner_word
                                    in (Operators.operators["OR"] +
                                        Operators.operators["XOR"])):
                    not_count = 0
                    tag_count = 0
                    for split_word in current_split:
                        if not IsOperator(split_word):
                            tag_count += 1
                        elif split_word in Operators.operators["NOT"]:
                            not_count += 1
                    if not_count >= tag_count:
                        return False  # must be at least 1 inclusive term in OR/XOR
                    current_split = []
                else:
                    current_split.append(inner_word)
            current_bracket = []
        else:
            current_bracket.append(word)
    return True


def CheckStrictValidity(text):
    if not CheckValidity(text):
        return False
    bracket_depth = 0
    tag_count = 0
    not_count = 0
    max_index = len(text) - 1
    for i, word in enumerate(text):
        if '(' in word:
            bracket_depth += 1
        elif ')' in word:
            bracket_depth -= 1
        elif bracket_depth == 0:
            if not IsOperator(word):
                tag_count += 1
            elif word in Operators.operators["NOT"]:
                if i != max_index and text[i + 1][0] == '(':
                    continue
                not_count += 1
    if not_count > tag_count:
        return False  # must be at least 1 inclusive term in the expression
    return True


def GetTopLevelInformation(text):
    bracket_depth = 0
    required = []
    remove = []
    requires_evaluation = False
    max_index = len(text) - 1
    for i, word in enumerate(text):
        if word == "(":
            bracket_depth += 1
        elif word == ")":
            bracket_depth -= 1
        elif bracket_depth == 0 and not IsOperator(word):
            if i == 0:
                required.append(word)
                continue
            if text[i - 1] in Operators.operators["NOT"]:
                remove.append(word)
            else:
                required.append(word)
        elif bracket_depth == 0 and word in Operators.operators["NOT"]:
            if i != max_index and text[i + 1][0] == '(':
                requires_evaluation = True
        elif word in (Operators.operators["OR"] + Operators.operators["XOR"]):
            requires_evaluation = True
    return required, remove, requires_evaluation


def StrictSearch(search_text):
    from SQL import GetAllItemTags, GetTagIDsFromNames
    search_text, inp_tags = ConvertSearchText(search_text)
    if not CheckStrictValidity(search_text):
        return ("INVALID", "VALIDITY")
    temp_required, temp_remove, requires_evaluation = GetTopLevelInformation(
        search_text)
    query = InfixToPostfix(search_text)
    tag_ids = GetTagIDsFromNames(inp_tags)
    for tag in inp_tags:
        if tag not in tag_ids.keys():
            return ("INVALID", "TAGS")
    required = []
    for i in temp_required:
        i = tag_ids[i]
        if isinstance(i, int):
            required.append(i)
    remove = []
    for i in temp_remove:
        i = tag_ids[i]
        if isinstance(i, int):
            remove.append(i)
    matches = []
    data = GetAllItemTags()
    for item in data:
        values = {}
        for tag in tag_ids:
            if isinstance(tag_ids[tag], int):
                if tag_ids[tag] in item[1]:  # assuming form [itemID, tagIDs]
                    values[tag] = True
                else:
                    values[tag] = False
            else:
                values[tag] = False
                for match in tag_ids[tag]:
                    if match in item[1]:
                        values[tag] = True
                        break
        do_continue = False
        for tag in required:
            if tag not in item[1]:
                do_continue = True
                break
        if do_continue:
            continue
        for tag in remove:
            if tag in item[1]:
                do_continue = True
                break
        if do_continue:
            continue
        if requires_evaluation:
            item_query = InsertValuesIntoQuery(query, values)
            if not EvaluatePostfix(item_query):
                continue
        matches.append(item[0])  # assuming form [itemID, tagIDs]
    return matches


def FormatTag(word):
    # returns formatted expression, actual word, value to shift final weight by
    char_1 = word[0]
    shift_value = 0
    if char_1 in Operators.pre_operators:
        word = word[1:]
        if char_1 == '+':  # (+ means inclusive)
            formatted = word
        elif char_1 == "-":
            split = SplitByCharacters(word, ['[', ']'])
            word = split[0]
            value = float(split[1])
            formatted = word + '[' + str(-value) + ']'
            shift_value = value
        else:
            formatted = GetOperatorType(char_1) + ' ' + word
    else:
        formatted = word
    return formatted, word, shift_value


def ConvertWeightedSearchText(text):
    split_text = SplitText(text)
    tag_names = []
    output = ""
    last_index = len(split_text) - 1
    bracket_depth = 0
    total_shift = 0
    inverse_bracket_end_weight = False
    for i, word in enumerate(split_text):
        if i != 0:
            split = output.split("[")
            if len(split) > 1:
                output = split[0] + ' CALCWEIGHT ' + split[1][:-2] + ' '
        if word == '(':
            bracket_depth += 1
        elif word == ')':
            bracket_depth -= 1
        if bracket_depth == 0 and (not IsOperator(word)
                                   or word == ')') and ('[' not in word
                                                        or ']' not in word):
            if word == ')' and i < last_index:
                if split_text[i + 1][0] != '[':
                    if inverse_bracket_end_weight:
                        word += '[-1] '
                        total_shift += 1
                        inverse_bracket_end_weight = False
                    else:
                        word += '[1] '
                elif inverse_bracket_end_weight:
                    value = float(split_text[i + 1][1:-1])
                    split_text[i + 1] = '[' + str(-value) + ']'
                    total_shift += value
                    inverse_bracket_end_weight = False
            elif inverse_bracket_end_weight:
                word += '[-1] '
                total_shift += 1
                inverse_bracket_end_weight = False
            else:
                word += '[1]'
        if word[0] == '(':
            output += word
            continue
        elif ')' in word:
            split = word.split('[')
            if len(split) > 1:
                word = split[0] + ' CALCWEIGHT ' + split[1][:-2] + ' '
                if i < last_index and (not IsOperator(split_text[i + 1])
                                       or split_text[i + 1][0] == '('):
                    word += 'ADDWEIGHT '
                elif i < (last_index - 1) and (
                        split_text[i + 1] in Operators.operators["NOT"]
                        and split_text[i + 2][0] == '('):
                    word += 'ADDWEIGHT '
            output += word
            continue
        if IsOperator(word):
            if word in Operators.operators["NOT"]:
                next_word = split_text[i + 1]
                if next_word == '(':
                    inverse_bracket_end_weight = True
            elif bracket_depth == 0 and word in Operators.operators['AND']:
                output += 'ADDWEIGHT '
            else:
                output += GetOperatorType(word) + ' '
        elif i < last_index:
            next_word = split_text[i + 1]
            if IsOperator(next_word) and next_word != '(':
                if bracket_depth == 0:
                    new_text, word, shift_value = FormatTag(word.lower())
                    total_shift += shift_value
                else:
                    new_text, word = ReducePreOperators(word.lower())
                if i < (last_index) - 1 and next_word in Operators.operators[
                        "NOT"] and split_text[i + 2][0] == '(':
                    # if the next operator is a NOT inverting a bracketed section, must add 'ADDWEIGHT '
                    split = new_text.split('[')
                    new_text = split[0] + ' CALCWEIGHT ' + split[
                        1][:-1] + ' ADDWEIGHT'
                output += new_text + ' '
                if word not in tag_names:
                    word = SplitByCharacters(word, ['['])[0]
                    if len(word) > 1:
                        tag_names.append(word)
            else:
                if bracket_depth == 0:
                    new_text, word, shift_value = FormatTag(word.lower())
                    total_shift += shift_value
                    split = new_text.split('[')
                    if len(split) > 1:
                        new_text = split[0] + ' CALCWEIGHT ' + split[
                            1][:-1] + ' '
                    output += new_text + 'ADDWEIGHT '
                else:
                    new_text, word = ReducePreOperators(word.lower())
                    output += new_text + ' AND '
                if word not in tag_names:
                    word = SplitByCharacters(word, ['['])[0]
                    if len(word) > 0:
                        tag_names.append(word)
        else:
            if bracket_depth == 0:
                new_text, word, shift_value = FormatTag(word.lower())
                total_shift += shift_value
            else:
                new_text, word = ReducePreOperators(word.lower())
            output += new_text
            if word not in tag_names:
                word = SplitByCharacters(word, ['['])[0]
                if len(word) > 0:
                    tag_names.append(word)
    split = output.split("[")
    if len(split) > 1:
        output = split[0] + ' CALCWEIGHT ' + split[1][:-1] + ' '
    return SplitText(output), tag_names, total_shift


def CheckWeightValidity(text):
    if not CheckValidity(text):
        return False
    bracket_depth = 0
    for word in text:
        if '(' in word:
            bracket_depth += 1
        elif ')' in word:
            bracket_depth -= 1
        elif bracket_depth > 0:
            if word == 'CALCWEIGHT':
                return False
    return True


def WeightedSearch(search_text, minimum_score=None):
    from SQL import GetTagIDsFromNames, GetAllItemTags
    search_text, inp_tags, total_shift = ConvertWeightedSearchText(search_text)
    if not CheckWeightValidity(search_text):
        return ("INVALID", "VALIDITY")
    query = InfixToPostfix(search_text)
    tag_ids = GetTagIDsFromNames(inp_tags)
    for tag in inp_tags:
        if tag not in tag_ids.keys():
            return ("INVALID", "TAGS")
    matches = {}
    data = GetAllItemTags()
    for item in data:
        values = {}
        for tag in tag_ids.keys():
            if isinstance(tag_ids[tag], int):
                if tag_ids[tag] in item[1]:  # assuming form [itemID, tagIDs]
                    values[tag] = True
                else:
                    values[tag] = False
            else:
                values[tag] = False
                for match in tag_ids[tag]:
                    if match in item[1]:
                        values[tag] = True
                        break
        item_query = InsertValuesIntoQuery(query, values)
        matches[item[0]] = EvaluatePostfix(
            item_query) + total_shift  # assuming form [itemID, tagIDs]
    if minimum_score == None:
        return matches
    to_return = {}
    for item in matches.keys():
        if matches[item] >= minimum_score:
            to_return[item] = matches[item]
    return to_return


def FormatResultsToHTML(items):
    item_content = ""
    dot_content = ""
    num_of_items = len(items)
    for i, item in enumerate(items):
        item_content += f"""
<div class="mySlides fade">
  <div class="numbertext">{i+1} / {num_of_items}</div>
"""
        try:
            if item.endswith(".jpg") or item.endswith(
                    ".jpeg") or item.endswith(".png") or item.endswith(".gif"):
                item_content += f"""  <img class="center" src="{item}" style="height:880px;">"""
            elif item.endswith(".mp4") or item.endswith(
                    ".ogg") or item.endswith(".webm"):
                format_type = item.split(".")[-1]
                item_content += f"""  <video autoplay class="center" src="{item}" type="video/{format_type}" style="height:880px" controls>"""
            elif "viewkey=" in item:
                url_content = item.split("viewkey=")[1]
                viewkey = url_content.split("&")[0]
                url = "/".join(item.split("/")[:3])
                url += "/embed/" + viewkey
                item_content += f"""  <iframe class="center" src="{url}" frameborder="0" scrolling="no" style="width:90%;height:880px" allowfullscreen></iframe>"""
            else:
                item_content += f"""  <div class="center" style="width:100%;height:880px;background:black"><div style="color:white;padding-top:25%;text-align:center">Could not display content. Click the link to see it.</div></div>"""
        except:
            item_content += f"""  <div class="center" style="width:100%;height:880px;background:black"><div style="color:white;padding-top:25%;text-align:center">Could not display content. Click the link to see it.</div></div>"""
        item_content += f"""
  <div class="caption_wrap center"><a class="text center" href="{item}">Link</a></div>
</div>

"""
        dot_content += f"""<span class="dot" onclick="currentSlide({i+1})"></span>\n"""
    with open("resources\\base_script.html", "r") as f:
        contents = f.read()
        f.close()
    contents = contents.replace("[CONTENT 1]", item_content)
    contents = contents.replace("[CONTENT 2]", dot_content)
    return contents


def FormatImportTags(text):
    text = text.strip().lower()
    lines = text.split("\n")
    lines = [i.strip('\r') for i in lines]
    if (lines[0] == 'tag' or lines[0] == 'metadata') and lines[1][0] == '?':
        to_remove = []
        for line in lines:
            if not line.startswith('?'):
                to_remove.append(line)
        for line in to_remove:
            lines.remove(line)
        for i, line in enumerate(lines):
            lines[i] = "_".join(line[2:].split(" ")[:-1])
    elif lines[0].startswith("categories:  "):
        lines = lines[0][13:]
        lines = ["_".join(i.strip().split(" ")) for i in lines.split(",")]
    elif lines[0].startswith("tags: "):
        lines = lines[0][6:]
        lines = SplitByCharacters(
            lines, ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "K"])
        while '' in lines:
            lines.remove('')
        for i, line in enumerate(lines):
            lines[i] = "_".join(line.split(" "))
    elif lines[0] == 'tags' and lines[1] == '' and lines[2].startswith(
            '    ? '):
        lines = ["_".join(i.split(" ")[5:-1]) for i in lines[2:]]
        while '' in lines:
            lines.remove('')
    else:
        return None
    return lines


def GetLevenshteinDist(a, b):
    rows = len(a) + 1
    columns = len(b) + 1
    distance = np.zeros((rows, columns),
                        dtype=int)  # initialize a matrix of zeroes
    for i in range(1, rows):
        for j in range(1, columns):
            # populate matrix with indexes of strings.
            distance[i][0] = i
            distance[0][j] = j
    for column in range(1, columns):
        for row in range(1, rows):
            if a[row - 1] == b[column - 1]:
                cost = 0  # if characters are identical in the same position, cost is 0
            else:
                cost = 1
            distance[row][column] = min(
                distance[row - 1][column] + 1,  # cost of deletions
                distance[row][column - 1] + 1,  # cost of insertions
                distance[row - 1][column - 1] + cost)  # cost of substitutions
    return distance[row][column]


def GetTagSimilarity(a, b):
    ratio = fuzz.ratio(a, b)
    if len(b) >= len(a):
        partial_ratio = fuzz.partial_ratio(a, b)
        token_set_ratio = fuzz.token_set_ratio(a, b)
    else:
        partial_ratio = 0
        token_set_ratio = 0
    token_sort_ratio = fuzz.token_sort_ratio(a, b)
    return max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)


def GetTagMostSimilar(a, options):
    matches = {}
    for option in options:
        matches[option] = GetTagSimilarity(a, option)
    return matches