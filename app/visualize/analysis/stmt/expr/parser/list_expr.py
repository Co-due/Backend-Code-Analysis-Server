from typing import List

from app.visualize.analysis.stmt.expr.expr_util import util
from app.visualize.analysis.stmt.expr.model.expr_obj import ListObj, ExprObj


class ListExpr:

    @staticmethod
    def parse(elts: list[ExprObj]):
        value = ListExpr._get_value(elts)
        expressions = ListExpr._concat_expression(elts)

        return ListObj(value=value, expressions=expressions)

    @staticmethod
    def _get_value(elts: list[ExprObj]):
        return [elt.value for elt in elts]

    @staticmethod
    def _concat_expression(elts: list[ExprObj]):
        elts_expression_lists = [elt.expressions for elt in elts]
        transposed_expression_lists = util.transpose_with_last_fill(elts_expression_lists)

        # [[1, 2, 3], [4, 5, 6]] -> ("[1, 4]", "[2, 5]", "[3, 6]")
        return tuple(f"[{','.join(map(str, t))}]" for t in transposed_expression_lists)
