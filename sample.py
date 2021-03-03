from functools import reduce
import sys
from pptree import *
import itertools
import operator
from graphviz import Digraph

sys.setrecursionlimit(10**6)

dot = Digraph(comment='The Round Table')
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
        replaced_equation = Equation(equation.left_part.replace(var, EPSILON), equation.right_part.replace(var, EPSILON))
        empty_equation.append(replaced_equation)
    return empty_equation


def replace_var_for_equation(equations: list[Equation], var, constant):
    empty_equation = []
    for equation in equations.copy():
        replaced_equation = Equation(equation.left_part.replace(var, constant+var),
                                     equation.right_part.replace(var, constant+var))
        empty_equation.append(replaced_equation)
    return empty_equation


def is_textual_equivalent(node: Node, name):
    cycle_node = node
    i = 0
    while cycle_node.parent is not None:
        if i < 2:
            i += 1
        else:
            for child in cycle_node.children:
                if child.name == name:
                    #dot.edge(child.name, name, label="PARENT_CYCLED")
                    print("NAME:", name, "PARENT_NAME:", child.name)
                    return True
        cycle_node = cycle_node.parent
    return False


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


def append_dot_node(node):
    dot.node(node.name, node.name)


def append_dot_node_with_edge(node1, node2, edge_name=""):
    append_dot_node(node2)
    dot.edge(node1.name, node2.name, label=edge_name)
#######################################################


def reg_ordered_solution(equation: Equation, constants=CONSTANTS, vars=VARS):
    # root_node = Node(equations_to_string([equation]))
    root_node = Node("ROOT")
    append_dot_node(root_node)
    _reg_ordered_solution([equation], root_node, constants, vars)
    print_tree(root_node)


def _reg_ordered_solution(equations: list[Equation], node: Node(list[Equation]), constants=CONSTANTS, vars=VARS):
    print([str(x) for x in equations])
    for equation in equations:
        len_left = len(equation.left_part)
        len_right = len(equation.right_part)
        # step 1
        if len_left > 0 and len_right > 0:
            if equation.left_part[0] == equation.right_part[0]:
                equation.left_part = kill_char(equation.left_part, FIRST_ELEMENT_INDEX)
                equation.right_part = kill_char(equation.right_part, FIRST_ELEMENT_INDEX)
                if equation.is_empty():
                    end_node = Node("END_NODE")
                    append_dot_node_with_edge(node, end_node, "T")
                    node = Node("SOLVED", node)
                    return
            # возможна ошибка, если всего был один элемент
            if len(equation.left_part) > 0 and len(equation.right_part) > 0 and equation.left_part[-1] == equation.right_part[-1]:
                equation.left_part = kill_char(equation.left_part, LAST_ELEMENT_INDEX)
                equation.right_part = kill_char(equation.right_part, LAST_ELEMENT_INDEX)
                if equation.is_empty():
                    end_node = Node("END_NODE")
                    append_dot_node_with_edge(node, end_node, "T")
                    node = Node("SOLVED", node)
                    return
    # step 2 (???)
    len_left = len(equation.left_part)
    len_right = len(equation.right_part)
    if len_left > 0 and len_right > 0 and equation.left_part[0] in constants and equation.right_part[0] in constants:
        if not equation.left_part[0] == equation.right_part[0]:
            node = Node("NO_SOLUTION", node)
            return
        else:
            if len_left == 1 and len_right == 1:
                end_node = Node("T")
                append_dot_node_with_edge(node, end_node)
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
    if len(equations) == 0:
        t_node = Node("T")
        append_dot_node_with_edge(node, t_node, "T")
        return
    # step 4
    if is_textual_equivalent(node, equations_to_string(equations)):
        # this is cycled
        dot.edge(node.name, equations_to_string(equations), label="PARENT_CYCLED")
        node = Node("cycle", node)
        return
    # step 5
    new_built_equations = []
    for equation in equations.copy():
        new_built_equations.append(simplify_equation(equation))
    new_built_equations = reduce(operator.concat, new_built_equations)
    new_node = Node(equations_to_string(new_built_equations), node)
    append_dot_node_with_edge(node, new_node, "simplify")

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
        epsilon_node = Node(equations_to_string(replaced_epsilon_equations), new_node)
        equation_node = Node(equations_to_string(replaced_equations), new_node)
        #
        append_dot_node_with_edge(new_node, epsilon_node, right_first_symbol + "-> eps")
        append_dot_node_with_edge(new_node, equation_node, right_first_symbol + "->" + left_first_symbol + right_first_symbol)
        #
        _reg_ordered_solution(replaced_epsilon_equations, epsilon_node, constants, vars)
        _reg_ordered_solution(replaced_equations, equation_node, constants, vars)
    else:
        _reg_ordered_solution(new_built_equations, new_node, constants, vars)

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
reg_ordered_solution(test_equation2)
# test_equation2 = Equation("ABAx", "xBAA")
# reg_ordered_solution(test_equation2)
dot.render('test-output/round-table.gv', view=True)
