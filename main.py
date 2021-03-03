from functools import reduce
import sys
from typing import List

from pptree import *
import itertools
import operator
from graphviz import Digraph

sys.setrecursionlimit(10 ** 6)

end_node = Node("T")
FIRST_ELEMENT_INDEX = 0
LAST_ELEMENT_INDEX = -1
EPSILON = ""
EQUATION_SIGN = "="
CONSTANTS = ["A", "B", "C"]
VARS = ["x", "y", "z"]


##################### Базовые класс уравнения ###########################
class Equation(object):
    def __init__(self, left: str, right: str):
        self.left_part = left
        self.right_part = right

    def __str__(self):
        return self.left_part + EQUATION_SIGN + self.right_part

    def is_empty(self):
        return len(self.right_part) == 0 and len(self.left_part) == 0

    def right_part_is_empty(self):
        return len(self.right_part) == 0

    def left_part_is_empty(self):
        return len(self.left_part) == 0

    def textual_presentation(self):
        return self.left_part + EQUATION_SIGN + self.right_part

    def is_textual_equal_with_constants(self, constants=CONSTANTS):
        is_equal = True
        if len(self.right_part) == len(self.left_part):
            for i in range(len(self.left_part)):
                if self.right_part[i] in constants and self.left_part[i] in constants:
                    if self.right_part[i] != self.left_part[i]:
                        is_equal = False
                else:
                    is_equal = False
        else:
            return False
        return is_equal

    def replace(self, a, b):
        self.left_part.replace(a, b)
        self.right_part.replace(a, b)


############## Вспомогательные методы #################
def is_solved(equation: Equation, constants=CONSTANTS):
    return equation.is_textual_equal_with_constants(constants)


def equations_to_string(equations: list[Equation]):
    equation_string = "{"
    for equation in equations:
        equation_string += str(equation) + ";"
    return equation_string + "}"


def kill_char(string, n):
    begin = string[:n]
    end = string[n + 1:]
    return begin + end


def replace_var_for_epsilon(equations: list[Equation], var):
    empty_equation = []
    for equation in equations:
        replaced_equation = Equation(equation.left_part.replace(var, EPSILON),
                                     equation.right_part.replace(var, EPSILON))
        empty_equation.append(replaced_equation)
    return empty_equation


def replace_var_for_equation(equations: list[Equation], var, constant):
    empty_equation = []
    for equation in equations.copy():
        replaced_equation = Equation(equation.left_part.replace(var, constant + var),
                                     equation.right_part.replace(var, constant + var))
        empty_equation.append(replaced_equation)
    return empty_equation


# поиск цикла
def is_textual_equivalent(node: Node, name):
    cycle_node = node
    i = 0
    possible_cycle: list[Node] = [cycle_node]
    while cycle_node.parent is not None:
        if i < 1:
            i += 1
        else:
            if cycle_node.name == name:
                for cycle in possible_cycle:
                    cycle.is_cycled = True
                return cycle_node
        cycle_node = cycle_node.parent
        possible_cycle.append(cycle_node)
    return None


# Проверяет, что две строчки являются регулярно-упорядоченными
# Выходом функции является булевое значение
def is_reg_ordered(first, second, constants=CONSTANTS, vars=VARS):
    for constant in constants:
        first = first.replace(constant, EPSILON)
        second = second.replace(constant, EPSILON)
    if first == second:
        return True
    return False


# Проверяет, что две строчки являются равносоставленными
# Выходом функции является булевое значение
def is_simplify(left, right, constants=CONSTANTS, vars=VARS):
    simplify_dictionary_first = {}
    constants_counter_first = 0

    simplify_dictionary_second = {}
    constants_counter_second = 0

    min_len = len(right) if len(left) > len(right) else len(left)
    for i in range(min_len):
        left_elem = left[i]
        right_elem = right[i]
        if left_elem in constants:
            constants_counter_first += 1
        else:
            if left_elem in simplify_dictionary_first:
                simplify_dictionary_first[left[i]] += 1
            else:
                simplify_dictionary_first[left[i]] = 1
        if right_elem in constants:
            constants_counter_second += 1
        else:
            if right_elem in simplify_dictionary_second:
                simplify_dictionary_second[right[i]] += 1
            else:
                simplify_dictionary_second[right[i]] = 1
    # Проверка, что мультимножество переменных и количество элементов из констант равны.
    if simplify_dictionary_first and simplify_dictionary_second and simplify_dictionary_first == simplify_dictionary_second and constants_counter_first == constants_counter_second:
        return True
    return False


# Функция, возвращающая равносоставленные уравнения
def simplify_equation(equation: Equation, constants=CONSTANTS, vars=VARS):
    left = equation.left_part
    right = equation.right_part
    min_len = len(right) if len(left) > len(right) else len(left)
    for i in range(1, min_len):
        if is_simplify(left[: i], right[: i], constants, vars):
            equal_equation = Equation(left[:i], right[:i])
            residual_equation = Equation(left[i:], right[i:])
            return [equal_equation, residual_equation]
    return [equation]


def clear_tree(node: Node):
    node.is_visited = False
    for child in node.children:
        if child.is_visited:
            clear_tree(child)


def draw_dot_vision(node: Node, path="test-output/round-table.gv"):
    draw_dot = Digraph()
    draw_dot.node(str(node.__hash__()), node.name)
    _draw_dot_vision(draw_dot, node)
    draw_dot.render(path, view=True)
    clear_tree(node)


def _draw_dot_vision(draw_dot: Digraph, node: Node):
    if node is not None and not node.is_visited:
        node.is_visited = True
        for child in node.children:
            draw_dot.node(str(child.__hash__()), child.name)
            draw_dot.edge(str(node.__hash__()), str(child.__hash__()), child.delta)
            _draw_dot_vision(draw_dot, child)


#######################################################


def reg_ordered_solution(equation: Equation, constants=CONSTANTS, vars=VARS):
    stack = set()
    root_node = Node("ROOT")
    _reg_ordered_solution([equation], root_node, constants, vars, stack.copy())
    draw_dot_vision(root_node)
    draw_dot_vision(root_node, 'test-output/test_tree_clean.gv')
    return root_node


def _reg_ordered_solution(equations: list[Equation], node: Node(list[Equation]), constants=CONSTANTS, vars=VARS,
                          vars_stack=set()):
    # Предусловие выхода - все уравнения решены
    solved = True
    for equation in equations:
        if not is_solved(equation, constants):
            solved = False
    if solved:
        t_node = Node("T", node)
        return
    # step 1
    for equation in equations:
        len_left = len(equation.left_part)
        len_right = len(equation.right_part)
        # step 1
        if len_left > 0 and len_right > 0:
            while len(equation.left_part) > 0 and len(equation.right_part) > 0 and equation.left_part[0] == \
                    equation.right_part[0]:
                equation.left_part = kill_char(equation.left_part, FIRST_ELEMENT_INDEX)
                equation.right_part = kill_char(equation.right_part, FIRST_ELEMENT_INDEX)
            while len(equation.left_part) > 0 and len(equation.right_part) > 0 and equation.left_part[-1] == \
                    equation.right_part[-1]:
                equation.left_part = kill_char(equation.left_part, LAST_ELEMENT_INDEX)
                equation.right_part = kill_char(equation.right_part, LAST_ELEMENT_INDEX)
    # step 2
    len_left = len(equation.left_part)
    len_right = len(equation.right_part)
    if len_left > 0 and len_right > 0 and equation.left_part[0] in constants and equation.right_part[0] in constants:
        if not equation.left_part[0] == equation.right_part[0]:
            node = Node("NO_SOLUTION", node)
            return
    # step 3
    empty_equation = []
    for equation in equations:
        if not equation.is_empty():
            empty_equation.append(equation)
    equations = empty_equation
    for equation in equations:
        # Ветвь решения тупиковая
        if (equation.left_part_is_empty() and not equation.right_part_is_empty()) or (
                not equation.left_part_is_empty() and equation.right_part_is_empty()):
            return
    # step 4
    cycle_node = is_textual_equivalent(node, equations_to_string(equations))
    if cycle_node is not None:
        # this is cycled
        node.children.append(cycle_node)
        return
    # step 5
    new_built_equations = []
    for equation in equations.copy():
        new_built_equations.append(simplify_equation(equation))
    new_built_equations = reduce(operator.concat, new_built_equations)
    new_node = Node(equations_to_string(new_built_equations), node)

    # step 6
    print([str(x) for x in equations])
    # if equations[0].is_empty():
    #     return
    left_first_symbol = equations[0].left_part[0]
    right_first_symbol = equations[0].right_part[0]
    if left_first_symbol in constants and right_first_symbol in vars:
        replaced_epsilon_equations = replace_var_for_epsilon(new_built_equations.copy(), right_first_symbol)
        replaced_equations = replace_var_for_equation(new_built_equations.copy(), right_first_symbol, left_first_symbol)
        #
        epsilon_node = Node(equations_to_string(replaced_epsilon_equations), new_node,
                            delta=right_first_symbol + "-> eps")
        equation_node = Node(equations_to_string(replaced_equations), new_node,
                             delta=right_first_symbol + "->" + left_first_symbol + right_first_symbol)
        #
        vars_stack.add(right_first_symbol)
        #
        _reg_ordered_solution(replaced_epsilon_equations, epsilon_node, constants, vars, vars_stack.copy())
        _reg_ordered_solution(replaced_equations, equation_node, constants, vars, vars_stack.copy())
    else:
        _reg_ordered_solution(new_built_equations, new_node, constants, vars, vars_stack.copy())


def find_all_t(node: Node):
    node_list = []
    _find_all_t(node, node_list)
    clear_tree(node)
    return node_list


def _find_all_t(node: Node, node_list: list[Node(Equation)]):
    if not node.is_visited:
        node.is_visited = True
        for child in node.children:
            if child.name == "T":
                node_list.append(child)
            else:
                _find_all_t(child, node_list)


def graph_builder_with_t_swaps(node: Node, var):
    subtrees = find_biggest_subtree(node, var)
    characteristic_list = [set[Equation]]
    for subtree_root_node in subtrees:
        characteristic_list.append(set(find_characteristic_equation(subtree_root_node, var)))
    # есть однозначное отображение characteristic_list[i] к subtree[i]
    change_subtree_list = [[Node]]  # Список нод, которые будут заменены в графе
    for i in range(len(subtrees)):
        # всегда данное уравнение заменяет свой граф на Т-лист
        change_subtree_list[i] = [subtrees[i]]
        for j in range(i, len(subtrees)):
            # Есть одинаковые решения уравнений
            if len(characteristic_list[i].intersection(characteristic_list[j])) > 0:
                # Добавляем еще одну ноду, если у них есть пересечения в решении
                change_subtree_list[i].append(subtrees[j])
    # change_subtree_list - содержит списки, по которым нужно построить новые графы, с заменой на Т-листы
    for nodes in change_subtree_list:
        # находим в дереве конкретную ноду из списка - заменяем её на T-лист
        # далее полученный граф переделываем по такому же принципу для второй ноды, если она есть итд.
        # на выходе получим граф вида G(find_characteristic_equation(subtree_root_node, var))
        pass



# поиск максимальных поддеревьев по одной переменной
# тут делается упущение, что всё, что ниже однозначно однопеременно
# TODO MAYBE_NEED_FIX
def find_biggest_subtree(node: Node, var):
    t_node_list: list[Node] = find_all_t(node)
    unique_var = False
    subtrees = []
    for t_node in t_node_list:
        while t_node.parent is not None:
            print("DELTA:", t_node.delta)
            if t_node.delta == "":
                t_node = t_node.parent
            else:
                if var in t_node.delta:
                    unique_var = True
                    t_node = t_node.parent
                else:
                    break
        if unique_var:
            subtrees.append(t_node)
            draw_dot_vision(t_node, path="test-output/test_cycle" + str(t_node.__hash__()) + ".gv")
    return subtrees


# def find_all_t(node: Node):
#     node_list = []
#     _find_all_t(node, node_list)
#     clear_tree(node)
#     return node_list
#
#
# def _find_all_t(node: Node, node_list: list[Node(Equation)]):
#     if not node.is_visited:
#         node.is_visited = True
#         for child in node.children:
#             if child.name == "T":
#                 node_list.append(child)
#             else:
#                 _find_all_t(child, node_list)
def build_characteristic_equation(ak_list, an_list, var):
    left_part = ""
    right_part = var
    for i in ak_list:
        left_part += i
    for i in an_list:
        left_part += i
        right_part += i
    left_part += var
    for i in ak_list:
        right_part += i
    return Equation(left_part, right_part)


# Поиск характеристического уравнения поддерева
def find_characteristic_equation(node: Node, var):
    while node.children is not None and node.delta != "":
        node = node.children[0]
    if node.is_cycled:
        # type A
        ak_list = []
        an_list = []
        _find_characteristic_equation(node, var, ak_list, an_list)
        clear_tree(node)
        # Уравнение построено
        return build_characteristic_equation(ak_list, an_list, var)
    else:
        # type B or no cycle
        pass
    pass


def _find_characteristic_equation(node: Node, var, ak_list: list[str], an_list: list[str], was_eps=False):
    if not node.is_visited:
        node.is_visited = True
        for child in node.children:
            if node.delta != "":
                if node.delta == var + "-> eps":
                    was_eps = True
                if node.delta != var + "-> eps":
                    # получаю ai
                    if not was_eps:
                        ak_list.append(node.delta.replace("->", "").replace(var, ""))
                    else:
                        an_list.append(node.delta.replace("->", "").replace(var, ""))
            _find_characteristic_equation(child, var, ak_list, an_list, was_eps)


#################### TESTS ##########################
print(is_reg_ordered("xAB", "BAx", CONSTANTS, VARS))
print(is_reg_ordered("xyxAB", "AxyABx", CONSTANTS, VARS))
print(is_reg_ordered("x", "A", CONSTANTS, VARS))
print(is_reg_ordered("xy", "yx", CONSTANTS, VARS))
print(is_reg_ordered("xz", "Axy", CONSTANTS, VARS))

test_equation1 = Equation("xAyBzC", "AxyBCz")
simple = simplify_equation(test_equation1)
print([str(x) for x in simple])

##################### MORE COMPLEX TEST #########################
test_equation2 = Equation("Axyx", "xyxA")
root_node = reg_ordered_solution(test_equation2)
find_biggest_subtree(root_node, "y")
# test_equation2 = Equation("ABAx", "xBAA")
# reg_ordered_solution(test_equation2)
