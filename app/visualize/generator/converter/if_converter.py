from app.visualize.analysis.stmt.model.if_stmt_obj import (
    ConditionObj,
    IfConditionObj,
    ElifConditionObj,
    ElseConditionObj,
)
from app.visualize.generator.model.if_viz import ConditionViz, IfElseDefineViz, IfElseChangeViz
from app.visualize.generator.visualization_manager import VisualizationManager


class IfConverter:

    @staticmethod
    def get_header_define_viz(conditions: tuple[ConditionObj, ...], viz_manager: VisualizationManager):
        if_header_conditions = []

        for condition in conditions:
            if isinstance(condition, IfConditionObj):
                if_header_conditions.append(IfConverter._create_condition_viz(condition, "if"))

            elif isinstance(condition, ElifConditionObj):
                if_header_conditions.append(IfConverter._create_condition_viz(condition, "elif"))

            elif isinstance(condition, ElseConditionObj):
                if_header_conditions.append(IfConverter._create_condition_viz(condition, "else"))

            else:
                raise TypeError(f"[IfConverter]: 지원하지 않는 조건문 타입입니다.: {type(condition)}")

        return IfElseDefineViz(depth=viz_manager.get_depth(), conditions=if_header_conditions)

    @staticmethod
    def get_header_change_steps(conditions: tuple[ConditionObj, ...], viz_manager: VisualizationManager):
        steps = []

        for condition in conditions:
            if isinstance(condition, ElseConditionObj):
                steps.append(
                    IfElseChangeViz(id=condition.id, depth=viz_manager.get_depth(), expr=str(condition.result))
                )

            elif isinstance(condition, IfConditionObj) or isinstance(condition, ElifConditionObj):
                for expression in condition.expr_obj.expressions:
                    steps.append(IfElseChangeViz(id=condition.id, depth=viz_manager.get_depth(), expr=expression))
                steps.append(
                    IfElseChangeViz(id=condition.id, depth=viz_manager.get_depth(), expr=str(condition.result))
                )
            else:
                raise TypeError(f"[IfConverter]: 지원하지 않는 조건문 타입입니다.: {type(condition)}")

            if steps[-1].expr == "True":
                return steps

        return steps

    @staticmethod
    def insert_body_steps_after_true_expression(header_change_step_list, body_steps_viz):
        for index, step in enumerate(header_change_step_list):
            # step.expr이 "True"인 경우
            if step.expr == "True":
                # 현재 스텝의 다음 위치에 body_steps_viz 삽입
                header_change_step_list[index + 1 : index + 1] = body_steps_viz
                return header_change_step_list  # 합쳐진 리스트 반환

        return header_change_step_list

    @staticmethod
    def _create_condition_viz(condition, condition_type):
        expr = condition.expr_obj.expressions[0] if condition_type != "else" else ""
        return ConditionViz(id=condition.id, expr=expr, type=condition_type)
