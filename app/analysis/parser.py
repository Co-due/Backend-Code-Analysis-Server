import ast
import re

from app.analysis.element_manager import CodeElementManager
from app.analysis.models import *

g_elem_manager = CodeElementManager()
print("CodeElementManager 생성")


def assign_parse(node):
    for target in node.targets:
        depth = g_elem_manager.depth
        if isinstance(node.value, ast.BinOp):
            parsed_expressions = binOp_parse(node.value)
            for parsed_expression in parsed_expressions:
                g_elem_manager.addStep(
                    Variable(depth=depth, name=target.id, expr=parsed_expression)
                )
            g_elem_manager.add_variable_value(name=target.id, value=parsed_expressions[-1])
        elif isinstance(node.value, ast.Constant):
            value = constant_parse(node.value)
            g_elem_manager.add_variable_value(name=target.id, value=value)
            g_elem_manager.addStep(
                Variable(depth=depth, name=target.id, expr=g_elem_manager.get_variable_value(name=target.id))
            )
        elif isinstance(node.value, ast.Name):
            g_elem_manager.addStep(
                Variable(depth=depth, name=target.id, expr=node.id)
            )
            value = name_parse(node.value)
            g_elem_manager.add_variable_value(name=target.id, value=value)
            g_elem_manager.addStep(
                Variable(depth=depth, name=target.id, expr=value)
            )


def replace_variable(expression, variable, key):
    pattern = rf'\b{variable}\b'
    replaced_expression = re.sub(pattern, str(key), expression)
    return replaced_expression


def binOp_calculate_binOp(node, expr):
    if isinstance(node, ast.BinOp):
        left = binOp_calculate_binOp(node.left, expr)
        right = binOp_calculate_binOp(node.right, expr)
        if isinstance(node.op, ast.Add):
            value = left + right
        elif isinstance(node.op, ast.Sub):
            value = left - right
        elif isinstance(node.op, ast.Mult):
            value = left * right
        elif isinstance(node.op, ast.Div):
            value = left / right
        else:
            raise NotImplementedError(f"Unsupported operator: {type(node.op)}")
        return value
    elif isinstance(node, ast.Name):
        return name_parse(node)
    elif isinstance(node, ast.Constant):
        return constant_parse(node)
    else:
        raise NotImplementedError(f"Unsupported node type: {type(node)}")


def binOp_calculate_expressions(expr, result):
    ret = [expr]
    pattern = r'\b[a-zA-Z]{1,2}\b'
    variables = re.findall(pattern, expr)
    for var in variables:
        value = g_elem_manager.get_variable_value(var)
        expr = replace_variable(expression=expr, variable=var, key=value)
    if len(variables) != 0:
        ret.append(expr)
    ret.append(result)
    return ret


def binOp_parse(node):
    value = binOp_calculate_binOp(node, ast.unparse(node))
    return binOp_calculate_expressions(ast.unparse(node), value)


def name_parse(node):
    try:
        return g_elem_manager.get_variable_value(name=node.id)
    except NameError as e:
        print("#error:", e)


def constant_parse(node):
    return node.value


def for_parse(node):
    # 타겟 처리
    target_name = node.target.id
    for_id = g_elem_manager.get_id(node)

    # Condition 객체 생성
    if isinstance(node.iter, ast.Call):
        condition = create_condition(target_name, node.iter)

    # For 객체 생성
    g_elem_manager.addStep(
        For(id=for_id, depth=g_elem_manager.depth, condition=condition)
    )

    # Body 처리
    g_elem_manager.increase_depth()
    for i in range(condition.start, condition.end, condition.step):
        # target 업데이트
        g_elem_manager.add_variable_value(name=target_name, value=i)
        for child_node in node.body:
            if isinstance(child_node, ast.Expr):
                parsed_objs = expr_parse(child_node)
                if parsed_objs is None:
                    continue

                for parsed_obj in parsed_objs:
                    g_elem_manager.addStep(parsed_obj)

        # condition 객체에서 cur 값만 변경한 새로운 condition 생성
        new_condition = condition.copy_with_new_cur(i)
        g_elem_manager.addStep(
            For(id=for_id, depth=g_elem_manager.get_depth() - 1, condition=new_condition)
        )




def expr_parse(node: ast.Expr):
    if isinstance(node.value, ast.Call):
        return call_parse(node.value)


def call_parse(node: ast.Call):
    func_name = node.func.id

    if func_name == 'print':
        return print_parse(node)


def print_parse(node: ast.Call):
    print_objects = []

    for cur_node in node.args:
        if isinstance(cur_node, ast.BinOp):
            # 연산 과정 리스트 생성
            parsed_expressions = binOp_parse(cur_node)
            # 중간 연산 과정이 포함된 노드 생성
            for parsed_expression in parsed_expressions:
                print_obj = Print(id=g_elem_manager.get_id(node), depth=g_elem_manager.get_depth(), name='print', expr=parsed_expression)
                print_objects.append(print_obj)  # 리스트에 추가

    return print_objects


def create_condition(target_name, node: ast.Call):
    # Condition - start, end, step
    start = 0
    end = None
    step = 1

    # args의 개수에 따라 start, end, step에 값을 할당
    identifier_list = [identifier_parse(arg) for arg in node.args]

    if len(identifier_list) == 1:
        end = identifier_list[0]
    elif len(identifier_list) == 2:
        start, end = identifier_list
    elif len(identifier_list) == 3:
        start, end, step = identifier_list

    return Condition(name=target_name, start=start, end=end, step=step, cur=start)


def identifier_parse(arg):
    if isinstance(arg, ast.Name):  # 변수 이름인 경우
        return name_parse(arg)
    elif isinstance(arg, ast.Constant):  # 상수인 경우
        return constant_parse(arg)
    else:
        raise TypeError(f"Unsupported node type: {type(arg)}")