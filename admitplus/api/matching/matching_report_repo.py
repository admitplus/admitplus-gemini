import logging
from bson import ObjectId


class MatchingReportRepo:
    def __init__(self):
        # 你的初始化代码
        pass

    def insert_matching_report(self, student_id, matching_report):
        """
        插入匹配报告到数据库

        Args:
            student_id: 学生ID
            matching_report: 匹配报告数据（应该是字典或列表，不是字符串）
        """
        try:
            logging.info(
                f"[Matching Report Repo] [Insert Matching Report] Inserting matching report for student_id: {student_id}"
            )

            # 确保 matching_report 是字典或列表，不是字符串
            if isinstance(matching_report, str):
                logging.warning(
                    f"[Matching Report Repo] [Insert Matching Report] matching_report is string, attempting to parse as JSON"
                )
                import json

                matching_report = json.loads(matching_report)

            # 构建要插入的文档
            report_document = {
                "student_id": student_id,
                "matching_report": matching_report,
                # 添加其他必要字段...
            }

            # 这里应该是你的数据库插入逻辑
            # result = self.collection.insert_one(report_document)
            # return str(result.inserted_id)

            # 临时返回一个模拟的 ID
            logging.info(
                f"[Matching Report Repo] [Insert Matching Report] Successfully inserted matching report for student_id: {student_id}"
            )
            return "mock_insert_id"

        except Exception as e:
            logging.error(
                f"[Matching Report Repo] [Insert Matching Report] Error inserting matching report for student_id {student_id}: {str(e)}"
            )
            return None
