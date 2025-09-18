"""
检查报告模块：根据病例结构化数据生成检查报告
"""

class ExamReportGenerator:
    @staticmethod
    def get_report(sp_data):
        """
        根据病例数据返回辅助检查报告
        :param sp_data: Sp_data实例
        :return: dict，包含所有辅助检查内容
        """
        data = sp_data.data if hasattr(sp_data, 'data') else sp_data
        report = {}
        # 体格检查
        if "physical_exam" in data:
            report["physical_exam"] = data["physical_exam"]
        # 辅助检查
        if "auxiliary_exam" in data:
            report["auxiliary_exam"] = data["auxiliary_exam"]
        return report
