import ast

from unittest.mock import MagicMock, patch

import pytest

from app.visualize.analysis.stmt.models.assign_stmt_obj import AssignStmtObj
from app.visualize.analysis.stmt.models.expr_stmt_obj import ExprStmtObj
from app.visualize.analysis.stmt.models.flowcontrolobj.break_stmt_obj import BreakStmtObj
from app.visualize.analysis.stmt.models.for_stmt_obj import BodyObj
from app.visualize.analysis.stmt.models.if_stmt_obj import (
    IfStmtObj,
    ElifConditionObj,
    ElseConditionObj,
    IfConditionObj,
    ConditionObj,
)
from app.visualize.analysis.stmt.parser.flowcontrol.break_stmt import BreakStmt
from app.visualize.analysis.stmt.parser.if_stmt import IfStmt
from app.visualize.analysis.stmt.stmt_traveler import StmtTraveler


@pytest.mark.parametrize(
    "code, called_func",
    [
        pytest.param("a=b", "_assign_travel", id="assign"),
        pytest.param("print('hello')", "_expr_travel", id="expr"),
        pytest.param("pass", "_flow_control_travel", id="pass"),
        pytest.param("break", "_flow_control_travel", id="break"),
    ],
)
def test_travel(mocker, code: str, called_func: str, create_ast, elem_container):
    stmt_node = create_ast(code)
    mock_travel = mocker.patch.object(StmtTraveler, called_func)

    StmtTraveler.travel(stmt_node, elem_container)

    mock_travel.assert_called_once()


@pytest.mark.parametrize(
    "code, mock_result",
    [
        pytest.param(
            """a = 10 \nprint('hello') \n""",
            [
                AssignStmtObj(
                    targets=("a",),
                    expr_stmt_obj=ExprStmtObj(id=1, value=10, expressions=("10",), expr_type="constant", type="expr"),
                    type="assign",
                ),
                ExprStmtObj(id=2, value="'hello'\n", expressions=("'hello'",), expr_type="print", type="expr"),
            ],
        ),
        pytest.param(
            """left = 0 \nright = 10 \nif (left+right)/2 == 5: \n   print("check")""",
            [
                AssignStmtObj(
                    targets=("left",),
                    expr_stmt_obj=ExprStmtObj(id=2, value=0, expressions=("0",), expr_type="constant", type="expr"),
                    type="assign",
                ),
                AssignStmtObj(
                    targets=("right",),
                    expr_stmt_obj=ExprStmtObj(id=3, value=10, expressions=("10",), expr_type="constant", type="expr"),
                    type="assign",
                ),
                IfStmtObj(
                    conditions=(
                        IfConditionObj(
                            id=4,
                            expressions=("left + right / 2 == 5", "0 + 10 / 2 == 5", "10 / 2 == 5", "5.0 == 5"),
                            result=True,
                        ),
                    ),
                    body_steps=[
                        ExprStmtObj(id=5, value="'check'\n", expressions=("'check'",), expr_type="print", type="expr")
                    ],
                    type="if",
                ),
            ],
        ),
    ],
)
def test__parse_for_body_success(mocker, elem_container, code: str, mock_result):
    """리스트 형태와 body의 개수 만큼 obj를 생성하여 반환하는지 검증"""
    mocker.patch.object(StmtTraveler, "travel", side_effect=mock_result)

    actual = StmtTraveler._parse_for_body(ast.parse(code).body, elem_container)

    assert isinstance(actual, list)
    assert len(actual) == len(mock_result)


@pytest.mark.parametrize(
    "code, expect",
    [
        pytest.param(
            """
if a > 10:
    print("a > 10")
elif a < 10:
    print("a < 10")
else:
    print("a > 10")
            """,
            IfStmtObj(
                conditions=(
                    IfConditionObj(id=1, expressions=("a>10",), result=False),
                    ElifConditionObj(id=2, expressions=("a<10",), result=False),
                    ElseConditionObj(id=3, expressions=None, result=True),
                ),
                body_steps=[[]],
            ),
            id="complex if-elif-else",
        ),
    ],
)
def test_if_travel(mocker, code: str, expect, elem_container):
    ast_if = ast.parse(code).body[0]
    mocker.patch.object(
        IfStmt, "parse_if_condition", return_value=IfConditionObj(id=1, expressions=("a>10",), result=False)
    )
    mocker.patch.object(
        IfStmt, "parse_elif_condition", return_value=ElifConditionObj(id=2, expressions=("a<10",), result=False)
    )
    mocker.patch.object(
        IfStmt, "parse_else_condition", return_value=ElseConditionObj(id=3, expressions=None, result=True)
    )
    mocker.patch.object(StmtTraveler, "travel", return_value=[])

    actual = StmtTraveler._if_travel(ast_if, [], [], elem_container)

    assert actual == expect


@pytest.mark.parametrize(
    "conditions, node, called_func",
    [
        pytest.param(
            [],
            ast.If(test=ast.parse("a>10").body[0].value),
            "parse_if_condition",
            id="conditions is empty",
        ),
        pytest.param(
            [IfConditionObj(id=1, expressions=("a>10",), result=False)],
            ast.If(test=ast.parse("True").body[0].value),
            "parse_elif_condition",
            id="conditions is not empty",
        ),
    ],
)
def test_append_condition_obj(mocker, conditions, node: ast.If, called_func, elem_container, create_ast):
    mock_func = mocker.patch.object(IfStmt, called_func)

    StmtTraveler._append_condition_obj(conditions, elem_container, node)

    mock_func.assert_called_once_with(node.test, elem_container)


@pytest.mark.parametrize(
    "conditions, node, result",
    [
        pytest.param(
            [],
            ast.parse("print('hello')").body[0],
            True,
            id="else condition when result True",
        ),
        pytest.param(
            [],
            ast.parse("print('hello')").body[0],
            False,
            id="else condition when result False",
        ),
    ],
)
def test_append_else_condition_obj(mocker, conditions, node: ast.stmt, result: bool):
    mock_if_stmt = mocker.patch.object(IfStmt, "parse_else_condition")

    StmtTraveler._append_else_condition_obj(conditions, node, result)

    mock_if_stmt.assert_called_once_with(node, result)


@pytest.mark.parametrize(
    "node, conditions, body_objs",
    [
        pytest.param(
            ast.parse("if a > 10: \n    print('hello')").body[0],
            [IfConditionObj(id=1, expressions=("a>10",), result=True)],
            [],
            id="if condition is True - 바디 추가 함",
        ),
    ],
)
def test_parse_if_body_추가(mocker, node: ast.If, conditions: list[ConditionObj], body_objs: list[BodyObj]):
    mocker.patch.object(
        StmtTraveler,
        "travel",
        return_value=ExprStmtObj(id=0, value="hello", expressions=("hello",), expr_type="print"),
    )
    StmtTraveler._parse_if_body(node, conditions, body_objs, MagicMock())

    assert body_objs[-1] == ExprStmtObj(id=0, value="hello", expressions=("hello",), expr_type="print")


@pytest.mark.parametrize(
    "node, conditions, body_objs",
    [
        pytest.param(
            ast.parse("if a < 10: \n    print('hello')").body[0],
            [IfConditionObj(id=1, expressions=("a<10",), result=False)],
            [ExprStmtObj(id=0, value="hello", expressions=("hello",), expr_type="print")],
            id="if condition is False - 바디 추가 안함",
        )
    ],
)
def test_parse_if_body_추가_안함(
    mocker, node: ast.If, conditions: list[ConditionObj], body_objs: list[BodyObj], elem_container
):
    mocker.patch.object(
        StmtTraveler,
        "travel",
        return_value=ExprStmtObj(id=0, value="hello", expressions=("hello",), expr_type="print"),
    )
    temp_body_objs = list(body_objs)
    StmtTraveler._parse_if_body(node, conditions, body_objs, MagicMock())

    assert temp_body_objs == body_objs


@pytest.mark.parametrize(
    "node, conditions",
    [
        pytest.param(
            ast.parse("if a < 10: \n    print('hello')\nelif a>10: \n   print('world')").body[0],
            [IfConditionObj(id=1, expressions=("a>10",), result=False)],
            id="orelse - elif",
        )
    ],
)
def test_parse_if_orelse_elif문_분기_실행(mocker, node: ast.If, conditions, elem_container):
    body_objs = []
    mock_if_travel = mocker.patch.object(StmtTraveler, "_if_travel", return_value=None)
    StmtTraveler._parse_if_branches(body_objs, conditions, elem_container, node.orelse)

    mock_if_travel.assert_called_once_with(node.orelse[0], conditions, body_objs, elem_container)


@pytest.mark.parametrize(
    "node",
    [
        pytest.param(
            ast.parse("if a < 10: \n   print('world') \nelse: \n   print('world')").body[0],
            id="orelse - else",
        )
    ],
)
def test_parse_if_orelse_else문_분기_실행(mocker, node: ast.If, elem_container):
    mock_if_travel = mocker.patch.object(StmtTraveler, "_parse_else", return_value=None)
    StmtTraveler._parse_if_branches([], [], elem_container, node.orelse)

    mock_if_travel.assert_called_with(
        node.orelse,
        [],
        [],
        elem_container,
    )


@pytest.mark.parametrize(
    "target",
    [
        pytest.param(ast.Constant(value=10), id="10"),
        pytest.param(ast.Assign(targets=[ast.Name(id="a")], value=ast.Constant(value=10)), id="assign"),
    ],
)
def test_parse_if_orelse_예외발생(target, elem_container):
    # 예외가 터지면 통과, 안터지면 실패
    with pytest.raises(TypeError):
        StmtTraveler._parse_if_branches([], [], elem_container, target)

        assert False


@pytest.mark.parametrize(
    "node, called_func",
    [
        pytest.param(ast.Pass(), "_pass_travel", id="_pass_travel 호출 success"),
        pytest.param(ast.Break(), "_break_travel", id="_break_travel 호출 success"),
    ],
)
def test__flow_control_travel(mocker, node: ast.Pass | ast.Break | ast.Continue, called_func):
    mock_func = mocker.patch.object(StmtTraveler, called_func)

    StmtTraveler._flow_control_travel(node)

    mock_func.assert_called_once_with(node)


@pytest.mark.parametrize(
    "node",
    [
        pytest.param(ast.If(), id="_flow_control_travel 호출 fail"),
        pytest.param(ast.Assign(), id="_flow_control_travel 호출 fail"),
    ],
)
def test__flow_control_travel(mocker, node: ast):
    with pytest.raises(TypeError):
        StmtTraveler._flow_control_travel(node)


def test__break_travel(mocker):
    node = ast.Break(lineno=1)
    mock_break_stmt = mocker.patch.object(BreakStmt, "parse", return_value=BreakStmtObj(id=1, expr="break"))

    StmtTraveler._break_travel(node)

    mock_break_stmt.assert_called_once_with(node)
