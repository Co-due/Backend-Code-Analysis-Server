import ast
from unittest.mock import patch
import pytest

from app.visualize.analysis.stmt.expr.model.expr_obj import ExprObj
from app.visualize.analysis.stmt.parser.for_stmt import ForStmt
from app.visualize.analysis.stmt.parser.expr_stmt import ExprTraveler


@pytest.mark.parametrize(
    "target, expect",
    [
        (
                ast.Name(id="i", ctx=ast.Store()),
                "i"
        ),
        (
                ast.Name(id="a", ctx=ast.Store()),
                "a"
        ),
    ],
)
def test__get_target_name(elem_manager, target, expect):
    # target 노드를 받아서 변수 이름을 반환하는지 테스트
    result = ForStmt._get_target_name(target, elem_manager)

    assert result == expect


@pytest.mark.parametrize(
    "target",
    [
        (
                ast.Constant(value=1)
        ),
    ],
)
def test__get_target_name_fail(elem_manager, target):
    # target 노드를 받아서 변수 이름을 반환하는지 테스트
    # 예외가 터지면 통과, 안터지면 실패
    with pytest.raises(TypeError, match=r"\[ForParser\]:  .*는 잘못된 타입입니다."):
        ForStmt._get_target_name(target, elem_manager)


# TODO 함수마다 parser를 추가하는 방향 고민
@pytest.mark.parametrize(
    "code, expect",
    [
        (
                """for i in range(3): \n    pass""",
                ExprObj(
                    type="range",
                    value={"end": "3", "start": "0", "step": "1"},
                    expressions=[{"end": "3", "start": "0", "step": "1"}],
                ),
        )
    ],
)
def test_get_condition_obj(create_ast, elem_manager, code, expect):
    # iter 노드를 받아서 range 함수의 파라미터를 반환하는지 테스트
    iter_node = create_ast(code).iter

    with patch.object(
            ExprTraveler,
            "call_travel",
            return_value=ExprObj(
                type="range",
                value={"end": "3", "start": "0", "step": "1"},
                expressions=[{"end": "3", "start": "0", "step": "1"}],
            ),
    ):
        actual = ForStmt._get_condition_obj(iter_node, elem_manager)
        assert actual == expect
