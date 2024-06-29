import ast

from app.visualize.analysis.element_manager import CodeElementManager
from app.visualize.analysis.stmt.stmt_traveler import StmtTraveler
from app.visualize.generator.converter_traveler import ConverterTraveler
from app.visualize.generator.visualization_manager import VisualizationManager


# TODO 이름 수정
class CodeVisualizer:

    def __init__(self, source_code):
        self._parsed_node = ast.parse(source_code)
        self._elem_manager = CodeElementManager()

        self._vizualization_manager = VisualizationManager()

    def visualize_code(self):
        analyzed_stmt_list = self._analysis_parsed_node()
        # TODO: 시각화 노드 리스트 생성
        return ConverterTraveler.travel(analyzed_stmt_list)

    def _analysis_parsed_node(self):
        self._elem_manager.increase_depth()
        steps = []

        for node in self._parsed_node.body:
            if isinstance(node, ast.Assign):
                assign_obj = StmtTraveler.assign_travel(node, self._elem_manager)
                # TODO:Assing_obj를 리스트가 아닌객체로 변경하고, extend -> append로 변경
                steps.append(assign_obj)

            elif isinstance(node, ast.For):
                for_vizs = StmtTraveler.for_travel(node, self._elem_manager)
                steps.append(for_vizs)

            elif isinstance(node, ast.Expr):
                expr_obj = StmtTraveler.expr_travel(node, self._elem_manager)
                steps.append(expr_obj)

            else:
                raise TypeError(f"지원하지 않는 노드 타입입니다.: {type(node)}")

        self._elem_manager.decrease_depth()

        return steps
